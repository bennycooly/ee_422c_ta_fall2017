
import java.lang.ArithmeticException;

/**
 * Helpful links:
 * https://www.programcreek.com/2009/02/diagram-for-hierarchy-of-exception-classes/
 */
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
     * Example of an unchecked exception.
     */
    public int divide(int a, int b) throws ArithmeticException {
        return a/b;
    }


    /**
     * Example of a checked exception.
     */
    public boolean checkGame(String state) throws GameException {
        if (state.equals("illegal")) {
            throw new GameException();
        }
        return true;
    }
}
