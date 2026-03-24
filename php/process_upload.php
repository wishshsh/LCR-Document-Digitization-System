<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

header('Content-Type: application/json');

// NOTE: No DB connection needed here anymore.
// process_upload.php only extracts fields via Flask.
// The actual DB insert happens in save_record.php when the user clicks Save.

if (!isset($_FILES['file']) || !isset($_POST['type'])) {
    echo json_encode(['status' => 'error', 'message' => 'Missing file or type']);
    exit();
}

$file = $_FILES['file'];
$type = $_POST['type'];
$ext  = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));

if (!in_array($ext, ['jpg','jpeg','png','pdf'])) {
    echo json_encode(['status' => 'error', 'message' => 'Invalid file type. Use JPG, PNG or PDF.']);
    exit();
}

// Map frontend type to Flask form_hint
$formHintMap = ['birth' => '1A', 'death' => '2A', 'marriage-cert' => '3A', 'marriage-license' => '90'];
$formHint    = $formHintMap[$type] ?? '1A';

$ch = curl_init();
$postFields = [
    'file'      => new CURLFile($file['tmp_name'], $file['type'], $file['name']),
    'form_hint' => $formHint,
];

// Forward bride file if present (Form 90)
if (isset($_FILES['file2']) && $_FILES['file2']['error'] === UPLOAD_ERR_OK) {
    $file2 = $_FILES['file2'];
    $postFields['file2'] = new CURLFile($file2['tmp_name'], $file2['type'], $file2['name']);
}

curl_setopt_array($ch, [
    CURLOPT_URL            => 'http://127.0.0.1:5000/process',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $postFields,
    CURLOPT_TIMEOUT        => 120,
]);
$response   = curl_exec($ch);
$httpStatus = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError  = curl_error($ch);
curl_close($ch);

if ($curlError) {
    echo json_encode(['status' => 'error', 'message' => 'Flask unreachable — is python app.py running? (' . $curlError . ')']);
    exit();
}

$result = json_decode($response, true);

if (!$result || $result['status'] !== 'success') {
    echo json_encode([
        'status'  => 'error',
        'message' => $result['message'] ?? 'Pipeline failed',
        'trace'   => $result['trace']   ?? null,
        'http'    => $httpStatus,
    ]);
    exit();
}

// Return extracted fields only — no DB insert.
// Frontend shows for review/editing; DB insert happens in save_record.php.
// Pass user_id back so Flutter can include it in the save request.
$userId = isset($_POST['user_id']) ? (int)$_POST['user_id'] : 1;
echo json_encode([
    'status'      => 'success',
    'form_class'  => $result['form_class'],
    'type'        => $type,
    'user_id'     => $userId,
    'raw_text'    => $result['raw_text'] ?? '',
    'fields'      => $result['fields'],
    'confidence'  => $result['confidence'],
    'preview_url' => $result['preview_url'] ?? null,
]);
?>