<?php
header('Content-Type: application/json');
require 'db_connect.php';

$data = json_decode(file_get_contents("php://input"));

if (!isset($data->username) || !isset($data->password)) {
    echo json_encode(["status" => "error", "message" => "Invalid input"]);
    exit();
}

$u = $data->username;
$p = $data->password;

$stmt = $conn->prepare("SELECT user_id, username, password_hash, role FROM users WHERE username = :username");
$stmt->bindParam(':username', $u);
$stmt->execute();

if ($stmt->rowCount() > 0) {
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    // Supports both plain-text passwords (dev) and hashed passwords (production)
    $passwordMatch = password_verify($p, $user['password_hash']) || ($p === $user['password_hash']);

    if ($passwordMatch) {
        echo json_encode([
            "status"  => "success",
            "message" => "Login successful",
            "user"    => [
                "id"   => $user['user_id'],
                "name" => $user['username'],
                "role" => $user['role']
            ]
        ]);
    } else {
        echo json_encode(["status" => "error", "message" => "Invalid username or password"]);
    }
} else {
    echo json_encode(["status" => "error", "message" => "Invalid username or password"]);
}
?>
