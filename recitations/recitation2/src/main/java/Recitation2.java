

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Scanner;

public class Recitation2 {
    public static void main(String[] args) {
        System.out.println("Hello World\n");

        Recitation2 program = new Recitation2();

        // read from stdin
        try
        (
            InputStreamReader reader = new InputStreamReader(System.in);
            BufferedReader bufferedReader = new BufferedReader(reader)
        )
        {
            Integer num = Integer.parseInt(bufferedReader.readLine());
            System.out.println("the sum of the digits in " + num + " is " + program.sumOfDigits(num));

        }

        catch(IOException e) {
            e.printStackTrace();
        }

        // read from file
        try
        (
            FileReader fr = new FileReader("file.txt");
            BufferedReader br = new BufferedReader(fr)
        )
        {
            String line;
            while ((line = br.readLine()) != null) {
                System.out.println("line says " + line);
            }
        }

        catch(IOException e) {
            e.printStackTrace();
        }

//        Scanner scanner = new Scanner(System.in);
//        String str = scanner.nextLine();
//        System.out.println(str);
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