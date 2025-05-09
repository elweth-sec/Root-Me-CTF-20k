<?php
require_once 'Database.php';

abstract class Animal {
    protected $name;

    public function __construct($name) {
        $this->name = $name;
    }

    public function getName() {
        return $this->name;
    }

    abstract public function speak();

    public function save() {
        $db = Database::getInstance()->getConnection();
        $species = get_class($this);
        $stmt = $db->prepare("INSERT INTO animals (species, name) VALUES (?, ?)");
        if ($stmt === false) {
            die('Erreur de préparation de la requête : ' . $db->error);
        }
        $stmt->bind_param("ss", $species, $this->name);
        $stmt->execute();
        $stmt->close();
    }
}
?>