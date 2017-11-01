
import java.util.Scanner;

public class Problem1 {

    /**
     * Finds the max product of n adjacent digits in a 1000-digit number
     * represented as a string.
     */
    public long maxProduct(String s, int n) {
        int iBegin = 0;
        int iEnd = n;

        long maxProduct = Long.MIN_VALUE;

        while (iEnd < s.length()) {
            long product = 1;
            for (int i = iBegin; i < iEnd; ++i) {
                product = Math.multiplyExact(product, Character.getNumericValue(s.charAt(i)));
            }
            if (product > maxProduct) {
                maxProduct = product;
            }
            ++iBegin;
            ++iEnd;
        }

        return maxProduct;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = Integer.parseInt(sc.nextLine());
        String s = sc.nextLine();
        sc.close();

        System.out.println(new Problem1().maxProduct(s, n));
    }
}