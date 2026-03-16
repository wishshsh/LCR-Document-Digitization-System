<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

header('Content-Type: application/json');
require 'db_connect.php';

try {
    // ── 1. Total records ──────────────────────────────────────
    $total = $conn->query("SELECT COUNT(*) FROM documents")->fetchColumn();

    // ── 2. Records by document type ───────────────────────────
    $byType = $conn->query("
        SELECT t.type_code, t.type_name, COUNT(d.doc_id) as count
        FROM document_types t
        LEFT JOIN documents d ON d.type_id = t.type_id
        GROUP BY t.type_id, t.type_code, t.type_name
        ORDER BY t.type_id
    ")->fetchAll(PDO::FETCH_ASSOC);

    // Map type_code to frontend-friendly label
    $typeMap = [
        'BIRTH'    => 'Birth',
        'DEATH'    => 'Death',
        'MARRCERT' => 'Marriage Cert',
        'MARRLIC'  => 'Marriage License',
    ];
    $byTypeFormatted = array_map(fn($r) => [
        'label' => $typeMap[strtoupper(trim($r['type_code']))] ?? $r['type_name'],
        'count' => (int)$r['count'],
    ], $byType);

    // ── 3. Records by status ──────────────────────────────────
    $byStatus = $conn->query("
        SELECT status, COUNT(*) as count
        FROM documents
        GROUP BY status
        ORDER BY status
    ")->fetchAll(PDO::FETCH_ASSOC);

    // Ensure all three statuses are always present
    $statusDefaults = ['Pending' => 0, 'Approved' => 0, 'Rejected' => 0];
    foreach ($byStatus as $row) {
        $statusDefaults[$row['status']] = (int)$row['count'];
    }
    $byStatusFormatted = array_map(
        fn($s, $c) => ['label' => $s, 'count' => $c],
        array_keys($statusDefaults),
        array_values($statusDefaults)
    );

    // ── 4. Monthly upload trend (last 12 months) ──────────────
    $monthly = $conn->query("
        SELECT
            DATE_FORMAT(upload_date, '%Y-%m') as month,
            COUNT(*) as count
        FROM documents
        WHERE upload_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(upload_date, '%Y-%m')
        ORDER BY month ASC
    ")->fetchAll(PDO::FETCH_ASSOC);

    // ── 5. Recent activity (last 5 records) ───────────────────
    $recent = $conn->query("
        SELECT d.doc_id, d.status, d.upload_date,
               t.type_code, u.username
        FROM documents d
        JOIN document_types t ON d.type_id = t.type_id
        JOIN users u ON d.user_id = u.user_id
        ORDER BY d.upload_date DESC
        LIMIT 5
    ")->fetchAll(PDO::FETCH_ASSOC);

    $typeMapFull = [
        'BIRTH'    => 'Birth Certificate',
        'DEATH'    => 'Death Certificate',
        'MARRCERT' => 'Marriage Certificate',
        'MARRLIC'  => 'Marriage License',
    ];
    $recentFormatted = array_map(fn($r) => [
        'id'     => 'DOC-' . $r['doc_id'],
        'type'   => $typeMapFull[strtoupper(trim($r['type_code']))] ?? $r['type_code'],
        'status' => $r['status'],
        'date'   => substr($r['upload_date'], 0, 10),
        'user'   => $r['username'],
    ], $recent);

    echo json_encode([
        'status'   => 'success',
        'total'    => (int)$total,
        'byType'   => $byTypeFormatted,
        'byStatus' => $byStatusFormatted,
        'monthly'  => $monthly,
        'recent'   => $recentFormatted,
    ]);

} catch (PDOException $e) {
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
?>
