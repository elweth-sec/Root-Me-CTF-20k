<?php
require_once 'Animal.php';

class Dog extends Animal {
    public function speak() {
        return "Woof";
    }
}
?>