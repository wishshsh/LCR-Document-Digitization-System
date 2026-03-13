<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { exit(0); }

header('Content-Type: application/json');
require 'db_connect.php';

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data['doc_id'])) {
    echo json_encode(["status" => "error", "message" => "Missing doc_id"]);
    exit();
}

$docId    = (int) $data['doc_id'];
$status   = $data['status']   ?? null;
$formData = $data['formData'] ?? [];

try {
    $conn->beginTransaction();

    // ── 1. Update document status if provided ───────────────────
    if ($status !== null) {
        $stmt = $conn->prepare("UPDATE documents SET status = :status WHERE doc_id = :doc_id");
        $stmt->execute([':status' => $status, ':doc_id' => $docId]);
    }

    // ── 2. Upsert each form field into document_data ────────────
    //    We use field_name to look up or create a field_id, then
    //    insert or update the extracted_value for this doc.
    foreach ($formData as $fieldName => $fieldValue) {
        if (trim($fieldName) === '' || trim((string)$fieldValue) === '') continue;

        // Ensure the field exists in data_fields
        $fStmt = $conn->prepare("SELECT field_id FROM data_fields WHERE field_name = :fn");
        $fStmt->execute([':fn' => $fieldName]);
        $field = $fStmt->fetch(PDO::FETCH_ASSOC);

        if ($field) {
            $fieldId = $field['field_id'];
        } else {
            // Auto-create the field if it doesn't exist yet
            $ins = $conn->prepare(
                "INSERT INTO data_fields (field_name, data_type) VALUES (:fn, 'text')"
            );
            $ins->execute([':fn' => $fieldName]);
            $fieldId = $conn->lastInsertId();
        }

        // Check if a document_data row already exists for this doc+field
        $ddStmt = $conn->prepare(
            "SELECT data_id FROM document_data WHERE doc_id = :doc_id AND field_id = :field_id"
        );
        $ddStmt->execute([':doc_id' => $docId, ':field_id' => $fieldId]);
        $existing = $ddStmt->fetch(PDO::FETCH_ASSOC);

        if ($existing) {
            // Update
            $upd = $conn->prepare(
                "UPDATE document_data 
                 SET extracted_value = :val, is_corrected = 1 
                 WHERE data_id = :data_id"
            );
            $upd->execute([':val' => $fieldValue, ':data_id' => $existing['data_id']]);
        } else {
            // Insert
            $ins2 = $conn->prepare(
                "INSERT INTO document_data (doc_id, field_id, extracted_value, ner_confidence_score, is_corrected)
                 VALUES (:doc_id, :field_id, :val, 0, 1)"
            );
            $ins2->execute([':doc_id' => $docId, ':field_id' => $fieldId, ':val' => $fieldValue]);
        }
    }

    $conn->commit();
    echo json_encode(["status" => "success", "message" => "Record saved"]);

} catch (PDOException $e) {
    $conn->rollBack();
    echo json_encode(["status" => "error", "message" => $e->getMessage()]);
}
?>
