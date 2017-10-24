
import java.lang.ArithmeticException;

public class ExceptionDemo {

    public static void main(String[] args) {
        new ExceptionDemo().divide(1, 3);

        try {
            new ExceptionDemo().checkGame("illegal");
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        finally {
            System.out.println("DONE");
        }
    }



    /**
     * Example of a checked exception.
     */
    public int divide(int a, int b) throws ArithmeticException {
        return a/b;
    }


    public boolean checkGame(String state) throws GameException {
        if (state.equals("illegal")) {
            throw new GameException();
        }
        return true;
    }
}
