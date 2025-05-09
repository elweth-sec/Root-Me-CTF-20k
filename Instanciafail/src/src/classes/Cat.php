<?php
require_once 'Animal.php';

class Cat extends Animal {
    public function speak() {
        return "Meow";
    }
}
?>