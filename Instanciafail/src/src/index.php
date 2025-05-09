<?php
session_start();
require_once 'classes/User.php';
require_once 'classes/Animal.php';
require_once 'classes/Cat.php';
require_once 'classes/Dog.php';
require_once 'classes/Bird.php';
require_once 'classes/Fish.php';
require_once 'classes/Hamster.php';
require_once 'classes/Rabbit.php';
require_once 'classes/Turtle.php';
require_once 'classes/Database.php';

$user = new User();

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['delete_all_animals'])) {
    $db = Database::getInstance()->getConnection();
    $result = $db->query("DELETE FROM animals");

    if ($result) {
        $confirmationMessage = "All animals have been successfully removed from the pet shop.";
        $additionalInfo = "No animal was mistreated during the operation.";
    } else {
        $confirmationMessage = "An error occurred while trying to delete the animals.";
        $additionalInfo = "";
    }
}

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_REQUEST['animal_type']) && isset($_REQUEST['animal_name'])) {
    $animal_type = $_REQUEST['animal_type'];
    $animal_name = $_REQUEST['animal_name'];

    if ($animal_type == 'Cat') {
        $animal = new Cat($animal_name);
    } elseif ($animal_type == 'Dog') {
        $animal = new Dog($animal_name);
    } elseif ($animal_type == 'Bird') {
        $animal = new Bird($animal_name);
    } elseif ($animal_type == 'Fish') {
        $animal = new Fish($animal_name);
    } elseif ($animal_type == 'Hamster') {
        $animal = new Hamster($animal_name);
    } elseif ($animal_type == 'Rabbit') {
        $animal = new Rabbit($animal_name);
    } elseif ($animal_type == 'Turtle') {
        $animal = new Turtle($animal_name);
    } else {
        $animal = new $animal_type($animal_name);
    }

    if ($animal) {
        $animal->save();
    } else {
        echo "<p>Error adding animal.</p>";
    }
}
?>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet Shop</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <?php include("navbar.php") ?>

    <h1>Welcome to the pet shop</h1>

    <?php if ($user->isLoggedIn()): ?>
        <form action="index.php" method="POST">
            <label for="animal_type">Type of animal:</label>
            <select name="animal_type" id="animal_type">
                <option value="Cat">Cat</option>
                <option value="Dog">Dog</option>
                <option value="Bird">Bird</option>
                <option value="Fish">Fish</option>
                <option value="Hamster">Hamster</option>
                <option value="Rabbit">Rabbit</option>
                <option value="Turtle">Turtle</option>
            </select>
            <br>
            <label for="animal_name">Name of the animal:</label>
            <input type="text" id="animal_name" name="animal_name" required>
            <br>
            <button type="submit">Add a new animal!</button>
        </form>

        <form action="index.php" method="POST">
            <button type="submit" name="delete_all_animals" onclick="return confirm('Are you sure you want to delete all animals? This action cannot be undone.');">Delete All Animals</button>
        </form>
    <?php else: ?>
        <p>Please <a href="login.php">login</a> or <a href="register.php">register</a> to add a new animal.</p>
    <?php endif; ?>

    <hr>
    <h2>List of animals in the pet shop</h2>

    <?php
    $db = Database::getInstance()->getConnection();
    $result = $db->query("SELECT * FROM animals");

    echo "<ul>";
    while ($row = $result->fetch_assoc()) {
        echo "<li>Type: " . htmlspecialchars($row['species']) . ", Name: " . htmlspecialchars($row['name']) . "</li>";
    }
    echo "</ul>";
    ?>

    <?php if (isset($confirmationMessage)): ?>
        <div class="message">
            <p><?php echo htmlspecialchars($confirmationMessage); ?></p>
            <?php if (!empty($additionalInfo)): ?>
                <span class="additional-info"><?php echo htmlspecialchars($additionalInfo); ?></span>
            <?php endif; ?>
            <button class="close-btn" onclick="this.parentElement.style.display='none';">&times;</button>
        </div>
    <?php endif; ?>
</body>
</html>
