

public class Main {
    public static void main(String[] args) {
        Animal elephant = new Animal("Elephant", "Dumbo");
        System.out.println("Population is now " + Animal.population);
        elephant.speak();
        System.out.println("elephant " + elephant.name + "'s lifespan is " + elephant.lifespan + " years");
    
        elephant.lifespan = -100;
    }
}
