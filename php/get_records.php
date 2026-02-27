<?php
header('Content-Type: application/json');
require 'db_connect.php';

try {
    // SQL query to join documents with types and users to get readable names
    $sql = "SELECT 
                d.doc_id, 
                t.type_name, 
                u.username as uploader_name, 
                d.upload_date, 
                d.status 
            FROM documents d
            JOIN document_types t ON d.type_id = t.type_id
            JOIN users u ON d.user_id = u.user_id
            ORDER BY d.upload_date DESC";

    $stmt = $conn->prepare($sql);
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($result);

} catch(PDOException $e) {
    echo json_encode(["error" => $e->getMessage()]);
}
?>