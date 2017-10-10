
class Elephant extends Animal {

    public Elephant(String name) {
        super("Elephant", name);
        // elephant-specific construction goes here

    }


    @Override
    void speak() {
        System.out.println("trumpet");
    }

    void speak(int volume) {
        System.out.println("TRUMPET");
    }
}
