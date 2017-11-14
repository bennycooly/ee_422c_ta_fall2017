
import java.util.*;

public class StreamDemo {
    
    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        strings.add("hello world");
        strings.add("goodbye");

        for (int i = 0; i < strings.size(); ++i) {
            System.out.println(strings.get(i));
        }

        for (String string : strings) {
            System.out.println(string);
        }

        strings.forEach(s -> System.out.println(s));
        strings.forEach(s -> {
            s += "hello";
            System.out.println(s);
        });
        strings.forEach(StreamDemo::print);


        
    }

    static void print(String s) {
        System.out.println(s);
    }


}