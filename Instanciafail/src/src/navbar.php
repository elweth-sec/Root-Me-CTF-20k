<?php
$db = Database::getInstance()->getConnection();
$stmt = $db->prepare("SELECT profile_picture FROM users WHERE id = ?");
$stmt->bind_param("i", $_SESSION['user_id']);
$stmt->execute();
$stmt->bind_result($profilePicture);
$stmt->fetch();
$stmt->close();
?>
<nav>
    <div class="nav-container">
        <div class="logo">
            <a href="index.php">Pet Shop</a>
        </div>
        <ul class="nav-list">
            <li class="nav-item"><a href="index.php">Home</a></li>
            <?php if ($user->isLoggedIn()): ?>
                <li class="nav-item"><a href="account.php">Account</a></li>
                <li class="nav-item"><a href="logout.php">Logout</a></li>
                <?php if ($profilePicture): ?>
                    <li class="nav-item profile-item"><img src="<?php echo htmlspecialchars(str_replace('/var/www/html/', '', $profilePicture)); ?>" alt="Profile Picture" class="profile-picture"></li>
                <?php endif; ?>
            <?php else: ?>
                <li class="nav-item"><a href="register.php">Register</a></li>
                <li class="nav-item"><a href="login.php">Login</a></li>
            <?php endif; ?>
        </ul>
    </div>
</nav>
