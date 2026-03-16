<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

header('Content-Type: application/json');
require 'db_connect.php';

$data = json_decode(file_get_contents("php://input"), true);

// doc_id is optional now — if missing, we INSERT a new document
$docId    = isset($data['doc_id']) ? (int)$data['doc_id'] : null;
$status   = $data['status']    ?? 'Pending';
$formData = $data['formData']  ?? [];
$docType  = $data['type']      ?? null;   // e.g. 'birth', 'death', 'marriage-cert', 'marriage-license'
$rawText  = $data['raw_text']  ?? '';

// Map frontend type → type_id
$typeIdMap = [
    'birth'            => 1,
    'death'            => 2,
    'marriage-cert'    => 3,
    'marriage-license' => 4,
];

try {
    $conn->beginTransaction();

    if ($docId === null) {
        // ── NEW record: insert document row ──────────────────
        if ($docType === null) {
            echo json_encode(['status' => 'error', 'message' => 'Missing type for new record']);
            $conn->rollBack();
            exit();
        }

        $typeId = $typeIdMap[$docType] ?? 1;
        // Use user_id from request (sent by Flutter from SharedPreferences)
        // Fall back to 1 only if missing
        $userId = isset($data['user_id']) ? (int)$data['user_id'] : 1;

        $stmt = $conn->prepare(
            "INSERT INTO documents (type_id, user_id, status, upload_date)
             VALUES (:type_id, :user_id, :status, NOW())"
        );
        $stmt->execute([
            ':type_id' => $typeId,
            ':user_id' => $userId,
            ':status'  => $status,
        ]);
        $docId = (int)$conn->lastInsertId();

        // Write OCR log if raw text provided
        if ($rawText) {
            try {
                $conn->prepare(
                    "INSERT INTO ocr_logs (doc_id, raw_text, clean_text, created_at)
                     VALUES (:doc_id, :raw, :clean, NOW())"
                )->execute([':doc_id' => $docId, ':raw' => $rawText, ':clean' => $rawText]);
            } catch (PDOException $e) {
                error_log('ocr_logs insert: ' . $e->getMessage());
            }
        }
    } else {
        // ── EXISTING record: update status if provided ────────
        $stmt = $conn->prepare(
            "UPDATE documents SET status = :status WHERE doc_id = :doc_id"
        );
        $stmt->execute([':status' => $status, ':doc_id' => $docId]);
    }

    // ── Upsert each form field into document_data ─────────────
    foreach ($formData as $fieldName => $fieldValue) {
        if (trim($fieldName) === '' || trim((string)$fieldValue) === '') continue;

        // Ensure field exists in data_fields
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

        // Check if document_data row already exists
        $ddStmt = $conn->prepare(
            "SELECT data_id FROM document_data WHERE doc_id = :doc_id AND field_id = :field_id"
        );
        $ddStmt->execute([':doc_id' => $docId, ':field_id' => $fieldId]);
        $existing = $ddStmt->fetch(PDO::FETCH_ASSOC);

        if ($existing) {
            $conn->prepare(
                "UPDATE document_data SET extracted_value = :val, is_corrected = 1
                 WHERE data_id = :data_id"
            )->execute([':val' => $fieldValue, ':data_id' => $existing['data_id']]);
        } else {
            $conn->prepare(
                "INSERT INTO document_data (doc_id, field_id, extracted_value, ner_confidence_score, is_corrected)
                 VALUES (:doc_id, :field_id, :val, 0, 1)"
            )->execute([':doc_id' => $docId, ':field_id' => $fieldId, ':val' => $fieldValue]);
        }
    }

    $conn->commit();
    echo json_encode([
        'status'  => 'success',
        'message' => 'Record saved',
        'doc_id'  => $docId,
    ]);

} catch (PDOException $e) {
    $conn->rollBack();
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
?>