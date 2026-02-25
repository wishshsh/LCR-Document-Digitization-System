<?php
$servername = "localhost";
$username = ""; // Default XAMPP username
$password = "";     // Default XAMPP password
$dbname = "thesis_database";    // Matches your SQL Dump

try {
    $conn = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
    // Set the PDO error mode to exception
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    // Return error as JSON if connection fails
    echo json_encode(["status" => "error", "message" => "Connection failed: " . $e->getMessage()]);
    exit();
}
?>