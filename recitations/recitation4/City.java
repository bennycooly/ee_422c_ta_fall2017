import java.io.IOException;

class City {
    static public final double PI = 3.14;
    static public int numInstances = 0;


    private int population;
    private String name;
    private int area;

    private int numCounties;

    public City() {
        this.population = 0;
        this.name = "";
        this.area = 0;
    }

    public City(String name, int population, int area) {
        if (population < 0) {
            throw new IllegalArgumentException("Population cannot be negative.");
        }

        this.name = name;
        this.population = population;
        this.area = area;
        numCounties++;
    }


    @Override
    public String toString() {
        return this.name + ": " + this.population + ": " + this.area;
    }

    // @Override
    // public boolean equals(City other) {
    //     return this.area == other.area
    //         && this.name.equals(other.name)
    //         && this.population == other.population;
    // }



    public City merge(City other) {
        City result = new City();
        if (this.population >= other.population) {
            result.name = this.name + "-" + other.name;
        }
        else {
            result.name = other.name + "-" + this.name;
        }

        result.population = this.population + other.population;
        result.area = this.area + other.area;
        return result;
    }

    public static void main(String[] args) {
        City austin = new City("Austin", 1000, 1000);
        City dallas = new City("Dallas", 2000, 2000);
        City merged = austin.merge(dallas);
        System.out.println(merged);
    }
}
