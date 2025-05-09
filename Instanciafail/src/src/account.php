<?php
session_start();
require_once 'classes/User.php';
require_once 'classes/Database.php';

$user = new User();

if (!$user->isLoggedIn()) {
    header("Location: login.php");
    exit();
}

$db = Database::getInstance()->getConnection();
$stmt = $db->prepare("SELECT profile_picture FROM users WHERE id = ?");
$stmt->bind_param("i", $_SESSION['user_id']);
$stmt->execute();
$stmt->bind_result($profilePicture);
$stmt->fetch();
$stmt->close();

$updateMessage = '';

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_FILES['profile_picture'])) {
    $targetDir = __DIR__ . "/uploads/";
    $originalFile = $targetDir . basename($_FILES["profile_picture"]["name"]);
    $resizedFile = $targetDir . pathinfo($originalFile, PATHINFO_FILENAME) . "-resized." . pathinfo($originalFile, PATHINFO_EXTENSION);
    $uploadOk = 1;
    $imageFileType = strtolower(pathinfo($originalFile, PATHINFO_EXTENSION));
    
    $check = getimagesize($_FILES["profile_picture"]["tmp_name"]);
    if ($check === false) {
        $updateMessage = "File is not an image.";
        $uploadOk = 0;
    }
    
    if($imageFileType != "jpg" && $imageFileType != "jpeg" && $imageFileType != "png") {
        $updateMessage = "Only JPG, JPEG, & PNG files are allowed.";
        $uploadOk = 0;
    }
    
    if ($uploadOk == 0) {
        $updateMessage = "Sorry, your file was not uploaded.";
    } else {
        if (move_uploaded_file($_FILES["profile_picture"]["tmp_name"], $originalFile)) {
            $command = "convert " . escapeshellarg($originalFile) . " -resize 50% " . escapeshellarg($resizedFile);
            exec($command, $output, $returnVar);
            
            if ($returnVar == 0) {
                $stmt = $db->prepare("UPDATE users SET profile_picture = ? WHERE id = ?");
                $stmt->bind_param("si", $resizedFile, $_SESSION['user_id']);
                if ($stmt->execute()) {
                    $updateMessage = "The file " . htmlspecialchars(basename($resizedFile)) . " has been uploaded.";
                    $profilePicture = $resizedFile;
                } else {
                    $updateMessage = "Sorry, there was an error updating your profile picture.";
                }
            } else {
                $updateMessage = "Sorry, there was an error resizing your file.";
            }
        } else {
            $updateMessage = "Sorry, there was an error uploading your file.";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <?php include("navbar.php") ?>

    <h1>Update Profile Picture</h1>
    
    <?php if ($updateMessage): ?>
        <p class="<?php echo strpos($updateMessage, 'error') !== false ? 'error' : 'success'; ?>"><?php echo $updateMessage; ?></p>
    <?php endif; ?>

    <form action="account.php" method="POST" enctype="multipart/form-data">
        <label for="profile_picture">Select a profile picture (JPG, JPEG, PNG):</label>
        <input type="file" name="profile_picture" id="profile_picture" required>
        <br><br>
        <button type="submit">Upload</button>
    </form>
</body>
</html>
