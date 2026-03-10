<?php
header('Content-Type: application/json');
require 'db_connect.php';

if (!isset($_FILES['file']) || !isset($_POST['type'])) {
    echo json_encode(['status' => 'error', 'message' => 'Missing file or type']);
    exit();
}

$uploadType = $_POST['type']; // 'cert' or 'marriage'
$file       = $_FILES['file'];
$ext        = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
$allowed    = ['jpg', 'jpeg', 'png', 'pdf'];

if (!in_array($ext, $allowed)) {
    echo json_encode(['status' => 'error', 'message' => 'Invalid file type']);
    exit();
}

// Save uploaded file to a temp folder
$uploadDir  = __DIR__ . '/../uploads/temp/';
if (!is_dir($uploadDir)) mkdir($uploadDir, 0777, true);
$filename   = uniqid('doc_', true) . '.' . $ext;
$filepath   = $uploadDir . $filename;

if (!move_uploaded_file($file['tmp_name'], $filepath)) {
    echo json_encode(['status' => 'error', 'message' => 'Failed to save file']);
    exit();
}

// ── Call Python pipeline ──────────────────────────────────────
// Python prints a JSON result to stdout which we capture here
$pythonPath  = 'python'; // or 'python3' depending on your system
$scriptPath  = __DIR__ . '/../python/pipeline.py';
$escapedPath = escapeshellarg($filepath);
$command     = "$pythonPath $scriptPath $escapedPath 2>&1";
$output      = shell_exec($command);

$result = json_decode($output, true);
if (!$result || isset($result['error'])) {
    echo json_encode([
        'status'  => 'error',
        'message' => 'Pipeline failed: ' . ($result['error'] ?? $output)
    ]);
    exit();
}

// ── Save document record to DB ────────────────────────────────
// Map MNB form class → type_id in your document_types table
$typeMap = [
    '1A' => 1, // BIRTH
    '2A' => 2, // DEATH
    '3A' => 3, // MARRCERT
];
$typeId  = $typeMap[$result['form_class']] ?? 1;
$userId  = 1; // TODO: replace with $_SESSION['user_id'] when sessions are added

$stmt = $conn->prepare(
    "INSERT INTO documents (type_id, user_id, status, upload_date)
     VALUES (:type_id, :user_id, 'Pending', NOW())"
);
$stmt->execute([':type_id' => $typeId, ':user_id' => $userId]);
$docId = $conn->lastInsertId();

// ── Save extracted fields to document_data ────────────────────
foreach ($result['fields'] as $fieldName => $fieldValue) {
    if (trim((string)$fieldValue) === '') continue;

    // Get or create field_id
    $fStmt = $conn->prepare("SELECT field_id FROM data_fields WHERE field_name = :fn");
    $fStmt->execute([':fn' => $fieldName]);
    $field = $fStmt->fetch(PDO::FETCH_ASSOC);

    if ($field) {
        $fieldId = $field['field_id'];
    } else {
        $ins = $conn->prepare(
            "INSERT INTO data_fields (field_name, data_type) VALUES (:fn, 'text')"
        );
        $ins->execute([':fn' => $fieldName]);
        $fieldId = $conn->lastInsertId();
    }

    $ins2 = $conn->prepare(
        "INSERT INTO document_data
            (doc_id, field_id, extracted_value, ner_confidence_score, is_corrected)
         VALUES (:doc_id, :field_id, :val, :conf, 0)"
    );
    $ins2->execute([
        ':doc_id'   => $docId,
        ':field_id' => $fieldId,
        ':val'      => $fieldValue,
        ':conf'     => $result['confidence'][$fieldName] ?? 0,
    ]);
}

echo json_encode([
    'status'     => 'success',
    'doc_id'     => $docId,
    'form_class' => $result['form_class'], // '1A', '2A', or '3A'
    'fields'     => $result['fields'],
]);
?>