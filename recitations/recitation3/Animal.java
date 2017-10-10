
/**
 * Animal class represents an abstract animal.
 * @author Ben Fu
 */
public class Animal {
    public static int population = 0;

    public int id;

    public String type;
    
    public String name;

    // lifespan in years
    private int lifespan;


    /**
     * Constructs animal with type and name.
     * @param type the type of animal
     * @param name the name of the animal
     */
    public Animal(String type, String name) {
        id = population;
        this.type = type;
        this.name = name;
        lifespan = 100;
        ++population;
    }
    
    public int getLifespan() {
        return lifespan;
    }

    // public void setLifespan(int lifespan) {
    //     this.lifespan = lifespan;
    // }

    public void speak() {
        if (this.type.equals("Elephant")) {
            System.out.println("trumpet");
        }
        else {
            System.out.println("weird animal noise");
        }
        
    }
}
