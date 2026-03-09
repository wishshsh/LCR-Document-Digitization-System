<?php
header('Content-Type: application/json');
require 'db_connect.php';

try {
    // ── 1. Fetch all documents with type and uploader info ──────────
    $sql = "SELECT 
                d.doc_id,
                d.status,
                d.upload_date,
                t.type_code,
                t.type_name,
                u.username AS uploader_name
            FROM documents d
            JOIN document_types t ON d.type_id  = t.type_id
            JOIN users          u ON d.user_id  = u.user_id
            ORDER BY d.upload_date DESC";

    $stmt = $conn->prepare($sql);
    $stmt->execute();
    $documents = $stmt->fetchAll(PDO::FETCH_ASSOC);

    if (empty($documents)) {
        echo json_encode([]);
        exit();
    }

    // ── 2. Collect all doc_ids so we can fetch their field data ─────
    $docIds = array_column($documents, 'doc_id');
    $placeholders = implode(',', array_fill(0, count($docIds), '?'));

    // ── 3. Fetch all field values for those documents ───────────────
    $fieldSql = "SELECT 
                    dd.doc_id,
                    df.field_name,
                    dd.extracted_value,
                    dd.is_corrected
                 FROM document_data dd
                 JOIN data_fields   df ON dd.field_id = df.field_id
                 WHERE dd.doc_id IN ($placeholders)";

    $fieldStmt = $conn->prepare($fieldSql);
    $fieldStmt->execute($docIds);
    $fieldRows  = $fieldStmt->fetchAll(PDO::FETCH_ASSOC);

    // ── 4. Group field values by doc_id ────────────────────────────
    $fieldsByDoc = [];
    foreach ($fieldRows as $row) {
        $fieldsByDoc[$row['doc_id']][$row['field_name']] = $row['extracted_value'];
    }

    // ── 5. Map type_code → frontend type key ───────────────────────
    //    Adjust these codes to match whatever you insert into document_types
    $typeMap = [
        'BIRTH'    => 'birth',
        'DEATH'    => 'death',
        'MARRCERT' => 'marriage-cert',
        'MARRLIC'  => 'marriage-license',
        // Fallback aliases
        'birth'            => 'birth',
        'death'            => 'death',
        'marriage-cert'    => 'marriage-cert',
        'marriage-license' => 'marriage-license',
    ];

    // ── 6. Build the final response array ──────────────────────────
    $result = [];
    foreach ($documents as $doc) {
        $typeCode    = strtoupper(trim($doc['type_code']));
        $frontendType = $typeMap[$typeCode] ?? $typeMap[$doc['type_code']] ?? 'birth';
        $formData    = $fieldsByDoc[$doc['doc_id']] ?? [];

        // Try to build a readable "name" from extracted fields
        $name = buildDisplayName($frontendType, $formData, $doc['uploader_name']);

        $result[] = [
            'id'       => 'DOC-' . $doc['doc_id'],
            'doc_id'   => $doc['doc_id'],
            'type'     => $frontendType,
            'name'     => $name,
            'date'     => substr($doc['upload_date'], 0, 10),   // YYYY-MM-DD
            'status'   => $doc['status'],
            'formData' => $formData,
        ];
    }

    echo json_encode($result);

} catch (PDOException $e) {
    echo json_encode(["error" => $e->getMessage()]);
}

// ── Helper: build a human-readable name from form fields ────
function buildDisplayName($type, $formData, $fallback) {
    switch ($type) {
        case 'birth':
            $first = $formData['child_first']  ?? '';
            $last  = $formData['child_last']   ?? '';
            $name  = trim("$first $last");
            return $name ?: $fallback;

        case 'death':
            $first = $formData['deceased_first'] ?? '';
            $last  = $formData['deceased_last']  ?? '';
            $name  = trim("$first $last");
            return $name ?: $fallback;

        case 'marriage-cert':
        case 'marriage-license':
            $hFirst = $formData['husband_first'] ?? ($formData['groom_first'] ?? '');
            $hLast  = $formData['husband_last']  ?? ($formData['groom_last']  ?? '');
            $wFirst = $formData['wife_first']    ?? ($formData['bride_first']  ?? '');
            $wLast  = $formData['wife_last']     ?? ($formData['bride_last']   ?? '');
            $husband = trim("$hFirst $hLast");
            $wife    = trim("$wFirst $wLast");
            if ($husband && $wife)  return "$husband & $wife";
            if ($husband || $wife)  return $husband ?: $wife;
            return $fallback;

        default:
            return $fallback;
    }
}
?>
