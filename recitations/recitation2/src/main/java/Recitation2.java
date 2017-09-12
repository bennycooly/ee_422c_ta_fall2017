
import org.slf4j.Logger;

public class Recitation2 {
    public static void main(String[] args) {
        System.out.println("Hello World\n");
    }

    public int sumOfDigits(int n) {
        int sum = 0;
        for (int i = n; i > 0; --i) {
            sum += n;
            --n;
        }

        return sum;
    }
}