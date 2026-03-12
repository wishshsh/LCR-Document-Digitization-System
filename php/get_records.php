<?php
header('Content-Type: application/json');
require 'db_connect.php';

try {
    $sql = "SELECT d.doc_id, d.status, d.upload_date, d.mnb_confidence_score,
                   t.type_code, t.type_name, u.username AS uploader_name
            FROM documents d
            JOIN document_types t ON d.type_id = t.type_id
            JOIN users          u ON d.user_id  = u.user_id
            ORDER BY d.upload_date DESC";
    $stmt = $conn->prepare($sql);
    $stmt->execute();
    $documents = $stmt->fetchAll(PDO::FETCH_ASSOC);

    if (empty($documents)) { echo json_encode([]); exit(); }

    $docIds       = array_column($documents, 'doc_id');
    $placeholders = implode(',', array_fill(0, count($docIds), '?'));

    $fieldStmt = $conn->prepare(
        "SELECT dd.doc_id, df.field_name, dd.extracted_value
         FROM document_data dd
         JOIN data_fields df ON dd.field_id = df.field_id
         WHERE dd.doc_id IN ($placeholders)"
    );
    $fieldStmt->execute($docIds);

    $fieldsByDoc = [];
    foreach ($fieldStmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $fieldsByDoc[$row['doc_id']][$row['field_name']] = $row['extracted_value'];
    }

    $typeMap = [
        'BIRTH'    => 'birth',
        'DEATH'    => 'death',
        'MARRCERT' => 'marriage-cert',
        'MARRLIC'  => 'marriage-license',
    ];

    $result = [];
    foreach ($documents as $doc) {
        $frontendType = $typeMap[strtoupper(trim($doc['type_code']))] ?? 'birth';
        $raw          = $fieldsByDoc[$doc['doc_id']] ?? [];

        // ── Assemble the formData keys the form renderers expect ──
        $formData = buildFormData($frontendType, $raw);

        $result[] = [
            'id'       => 'DOC-' . $doc['doc_id'],
            'doc_id'   => $doc['doc_id'],
            'type'     => $frontendType,
            'name'     => buildDisplayName($frontendType, $raw, $doc['uploader_name']),
            'date'     => substr($doc['upload_date'], 0, 10),
            'status'   => $doc['status'],
            'formData' => $formData,
        ];
    }

    echo json_encode($result);

} catch (PDOException $e) {
    echo json_encode(['error' => $e->getMessage()]);
}

// ── Assemble form renderer keys from granular DB fields ───────
function buildFormData($type, $r) {
    $f = [];

    // Shared across all forms
    $f['registry_number']      = $r['registry_no']        ?? '';
    $f['city']                 = $r['city_municipality']   ?? '';
    $f['date']                 = $r['date_issuance']       ?? '';
    $f['date_of_registration'] = $r['date_submitted']      ?? ($r['date_received'] ?? '');
    $f['verified_by']          = $r['processed_by']        ?? '';
    $f['verified_position']    = $r['verified_position']   ?? '';
    $f['issued_to']            = $r['issued_to']           ?? '';
    $f['amount_paid']          = $r['amount_paid']         ?? '';
    $f['or_number']            = $r['or_number']           ?? '';
    $f['date_paid']            = $r['date_paid']           ?? '';

    if ($type === 'birth') {
        $f['child_name']             = trim(($r['child_first'] ?? '') . ' ' . ($r['child_middle'] ?? '') . ' ' . ($r['child_last'] ?? ''));
        $f['sex']                    = $r['sex']               ?? '';
        $f['date_of_birth']          = trim(($r['dob_month'] ?? '') . ' ' . ($r['dob_day'] ?? '') . ', ' . ($r['dob_year'] ?? ''));
        $f['place_of_birth']         = trim(($r['pob_city'] ?? '') . (($r['pob_province'] ?? '') ? ', ' . $r['pob_province'] : ''));
        $f['mother_name']            = trim(($r['mother_first'] ?? '') . ' ' . ($r['mother_middle'] ?? '') . ' ' . ($r['mother_last'] ?? ''));
        $f['mother_nationality']     = $r['mother_citizenship'] ?? '';
        $f['father_name']            = trim(($r['father_first'] ?? '') . ' ' . ($r['father_middle'] ?? '') . ' ' . ($r['father_last'] ?? ''));
        $f['father_nationality']     = $r['father_citizenship'] ?? '';
        $f['parents_marriage_date']  = trim(($r['parents_marriage_month'] ?? '') . ' ' . ($r['parents_marriage_day'] ?? '') . ', ' . ($r['parents_marriage_year'] ?? ''));
        $f['parents_marriage_place'] = trim(($r['parents_marriage_city'] ?? '') . (($r['parents_marriage_province'] ?? '') ? ', ' . $r['parents_marriage_province'] : ''));

    } elseif ($type === 'death') {
        $f['deceased_name']  = trim(($r['deceased_first'] ?? '') . ' ' . ($r['deceased_middle'] ?? '') . ' ' . ($r['deceased_last'] ?? ''));
        $f['sex']            = $r['sex']            ?? '';
        $f['age']            = $r['age_years']      ?? '';
        $f['civil_status']   = $r['civil_status']   ?? '';
        $f['nationality']    = $r['citizenship']    ?? '';
        $f['date_of_death']  = trim(($r['dod_month'] ?? '') . ' ' . ($r['dod_day'] ?? '') . ', ' . ($r['dod_year'] ?? ''));
        $f['place_of_death'] = trim(($r['pod_hospital'] ?? '') . (($r['pod_city'] ?? '') ? ', ' . $r['pod_city'] : ''));
        $f['cause_of_death'] = $r['cause_immediate'] ?? '';

    } elseif ($type === 'marriage-cert') {
        $f['husband_name']                = trim(($r['husband_first'] ?? '') . ' ' . ($r['husband_middle'] ?? '') . ' ' . ($r['husband_last'] ?? ''));
        $f['husband_age']                 = $r['husband_age']              ?? '';
        $f['husband_nationality']         = $r['husband_citizenship']      ?? '';
        $f['husband_mother_name']         = trim(($r['husband_mother_first'] ?? '') . ' ' . ($r['husband_mother_last'] ?? ''));
        $f['husband_mother_nationality']  = $r['husband_mother_citizenship'] ?? '';
        $f['husband_father_name']         = trim(($r['husband_father_first'] ?? '') . ' ' . ($r['husband_father_last'] ?? ''));
        $f['husband_father_nationality']  = $r['husband_father_citizenship'] ?? '';
        $f['wife_name']                   = trim(($r['wife_first'] ?? '') . ' ' . ($r['wife_middle'] ?? '') . ' ' . ($r['wife_last'] ?? ''));
        $f['wife_age']                    = $r['wife_age']                 ?? '';
        $f['wife_nationality']            = $r['wife_citizenship']         ?? '';
        $f['wife_mother_name']            = trim(($r['wife_mother_first'] ?? '') . ' ' . ($r['wife_mother_last'] ?? ''));
        $f['wife_mother_nationality']     = $r['wife_mother_citizenship']  ?? '';
        $f['wife_father_name']            = trim(($r['wife_father_first'] ?? '') . ' ' . ($r['wife_father_last'] ?? ''));
        $f['wife_father_nationality']     = $r['wife_father_citizenship']  ?? '';
        $f['date_of_marriage']            = trim(($r['marriage_month'] ?? '') . ' ' . ($r['marriage_day'] ?? '') . ', ' . ($r['marriage_year'] ?? ''));
        $f['place_of_marriage']           = trim(($r['marriage_venue'] ?? '') . (($r['marriage_city'] ?? '') ? ', ' . $r['marriage_city'] : ''));

    } elseif ($type === 'marriage-license') {
        // Marriage license uses groom/bride field names
        $f['husband_name']      = trim(($r['groom_first'] ?? '') . ' ' . ($r['groom_middle'] ?? '') . ' ' . ($r['groom_last'] ?? ''));
        $f['husband_age']       = $r['groom_age']         ?? '';
        $f['husband_nationality']= $r['groom_citizenship'] ?? '';
        $f['husband_mother_name']= trim(($r['groom_mother_first'] ?? '') . ' ' . ($r['groom_mother_last'] ?? ''));
        $f['husband_father_name']= trim(($r['groom_father_first'] ?? '') . ' ' . ($r['groom_father_last'] ?? ''));
        $f['wife_name']         = trim(($r['bride_first'] ?? '') . ' ' . ($r['bride_middle'] ?? '') . ' ' . ($r['bride_last'] ?? ''));
        $f['wife_age']          = $r['bride_age']         ?? '';
        $f['wife_nationality']  = $r['bride_citizenship'] ?? '';
        $f['wife_mother_name']  = trim(($r['bride_mother_first'] ?? '') . ' ' . ($r['bride_mother_last'] ?? ''));
        $f['wife_father_name']  = trim(($r['bride_father_first'] ?? '') . ' ' . ($r['bride_father_last'] ?? ''));
        $f['date_of_marriage']  = trim(($r['marriage_month'] ?? '') . ' ' . ($r['marriage_day'] ?? '') . ', ' . ($r['marriage_year'] ?? ''));
        $f['place_of_marriage'] = trim(($r['marriage_venue'] ?? '') . (($r['marriage_city'] ?? '') ? ', ' . $r['marriage_city'] : ''));
        $f['license_no']        = $r['license_no'] ?? '';
    }

    // Clean up empty date strings like " , "
    foreach ($f as $k => $v) {
        if (trim($v, ' ,') === '') $f[$k] = '';
    }

    return $f;
}

// ── Build display name for the records table ──────────────────
function buildDisplayName($type, $r, $fallback) {
    switch ($type) {
        case 'birth':
            $name = trim(($r['child_first'] ?? '') . ' ' . ($r['child_last'] ?? ''));
            return $name ?: $fallback;
        case 'death':
            $name = trim(($r['deceased_first'] ?? '') . ' ' . ($r['deceased_last'] ?? ''));
            return $name ?: $fallback;
        case 'marriage-cert':
            $h = trim(($r['husband_first'] ?? '') . ' ' . ($r['husband_last'] ?? ''));
            $w = trim(($r['wife_first']    ?? '') . ' ' . ($r['wife_last']    ?? ''));
            if ($h && $w) return "$h & $w";
            return $h ?: $w ?: $fallback;
        case 'marriage-license':
            $h = trim(($r['groom_first'] ?? '') . ' ' . ($r['groom_last'] ?? ''));
            $w = trim(($r['bride_first'] ?? '') . ' ' . ($r['bride_last'] ?? ''));
            if ($h && $w) return "$h & $w";
            return $h ?: $w ?: $fallback;
        default:
            return $fallback;
    }
}
?>