<?php
header('Content-Type: application/json');
require 'db_connect.php';

if (!isset($_FILES['file']) || !isset($_POST['type'])) {
    echo json_encode(['status' => 'error', 'message' => 'Missing file or type']);
    exit();
}

$file  = $_FILES['file'];
$type  = $_POST['type'];
$ext   = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));

if (!in_array($ext, ['jpg','jpeg','png','pdf'])) {
    echo json_encode(['status' => 'error', 'message' => 'Invalid file type. Use JPG, PNG or PDF.']);
    exit();
}

// ── Forward to Flask ──────────────────────────────────────────
$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL            => 'http://127.0.0.1:5000/process',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => [
        'file' => new CURLFile($file['tmp_name'], $file['type'], $file['name']),
        'type' => $type,
    ],
    CURLOPT_TIMEOUT => 120,
]);
$response   = curl_exec($ch);
$httpStatus = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError  = curl_error($ch);
curl_close($ch);

if ($curlError || $httpStatus !== 200) {
    echo json_encode(['status' => 'error', 'message' => 'Flask unreachable — is python app.py running? (' . ($curlError ?: "HTTP $httpStatus") . ')']);
    exit();
}

$result = json_decode($response, true);
if (!$result || $result['status'] !== 'success') {
    echo json_encode(['status' => 'error', 'message' => $result['message'] ?? 'Pipeline failed']);
    exit();
}

// ── Map form_class → type_id ──────────────────────────────────
$typeMap = ['1A' => 1, '2A' => 2, '3A' => 3, '90' => 4];
$typeId  = $typeMap[$result['form_class']] ?? 1;
$userId  = 1;  // TODO: $_SESSION['user_id']

// ── Insert document ───────────────────────────────────────────
$stmt = $conn->prepare("INSERT INTO documents (type_id, user_id, status, upload_date) VALUES (:type_id, :user_id, 'Pending', NOW())");
$stmt->execute([':type_id' => $typeId, ':user_id' => $userId]);
$docId = $conn->lastInsertId();

// ── Write to ocr_logs ─────────────────────────────────────────
try {
    $conn->prepare("INSERT INTO ocr_logs (doc_id, raw_text, clean_text, created_at) VALUES (:doc_id, :raw, :clean, NOW())")
         ->execute([':doc_id' => $docId, ':raw' => $result['raw_text'] ?? '', ':clean' => $result['raw_text'] ?? '']);
} catch (PDOException $e) { error_log('ocr_logs: ' . $e->getMessage()); }

// ── Save extracted fields ─────────────────────────────────────
foreach ($result['fields'] as $fieldName => $fieldValue) {
    if (trim((string)$fieldValue) === '') continue;

    $fStmt = $conn->prepare("SELECT field_id FROM data_fields WHERE field_name = :fn");
    $fStmt->execute([':fn' => $fieldName]);
    $field = $fStmt->fetch(PDO::FETCH_ASSOC);

    if ($field) {
        $fieldId = $field['field_id'];
    } else {
        $ins = $conn->prepare("INSERT INTO data_fields (field_name, data_type) VALUES (:fn, 'text')");
        $ins->execute([':fn' => $fieldName]);
        $fieldId = $conn->lastInsertId();
    }

    $conn->prepare("INSERT INTO document_data (doc_id, field_id, extracted_value, ner_confidence_score, is_corrected) VALUES (:doc_id, :field_id, :val, :conf, 0)")
         ->execute([':doc_id' => $docId, ':field_id' => $fieldId, ':val' => $fieldValue, ':conf' => $result['confidence'][$fieldName] ?? 0]);
}

echo json_encode([
    'status'     => 'success',
    'doc_id'     => $docId,
    'form_class' => $result['form_class'],
    'fields'     => $result['fields'],
    'confidence' => $result['confidence'],
    'preview_url'=> $result['preview_url'] ?? null,
]);
?>