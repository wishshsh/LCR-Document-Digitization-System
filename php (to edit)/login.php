<?php
header('Content-Type: application/json');
require 'db_connect.php';

// Get JSON input from the JavaScript fetch request
$data = json_decode(file_get_contents("php://input"));

if(isset($data->username) && isset($data->password)) {
    $u = $data->username;
    $p = $data->password;

    // Prepare statement to prevent SQL Injection
    $stmt = $conn->prepare("SELECT user_id, username, password_hash, role FROM users WHERE username = :username");
    $stmt->bindParam(':username', $u);
    $stmt->execute();
    
    if ($stmt->rowCount() > 0) {
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // VERIFY PASSWORD
        // Note: In a real app, use password_verify($p, $user['password_hash']). 
        // For this example, we assume direct comparison or simple hash:
        if ($p == $user['password_hash']) { 
            echo json_encode([
                "status" => "success", 
                "message" => "Login successful",
                "user" => [
                    "id" => $user['user_id'],
                    "name" => $user['username'],
                    "role" => $user['role']
                ]
            ]);
        } else {
            echo json_encode(["status" => "error", "message" => "Invalid password"]);
        }
    } else {
        echo json_encode(["status" => "error", "message" => "User not found"]);
    }
} else {
    echo json_encode(["status" => "error", "message" => "Invalid input"]);
}
?>