
package assignment1;

import java.util.Scanner;

public class Problem2 {
    /**
     * Print out all dollar words from a String. Each character is worth its position in the alphabet,
     * e.g. a = 1, b = 2, ... , z = 26
     */
    public void pringDollarWords(String s) {
        // first split words by spaces
        String[] words = s.split("\\s+");
        for (String word : words) {
            // make a copy of the word and convert it to all lower case
            // this makes it easy to check the word value
            int value = 0;
            for (int i = 0; i < word.length(); ++i) {
                if (!Character.isAlphabetic(word.charAt(i))) {
                    continue;
                }
                value += Character.toLowerCase(word.charAt(i)) - 'a' + 1;
            }

            if (value == 100) {
                System.out.println(word);
            }
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        sc.close();

        new Problem2().pringDollarWords(s);
    }
}
