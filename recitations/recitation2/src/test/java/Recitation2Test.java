
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;



public class Recitation2Test {
    private Recitation2 recitation2;

    @BeforeEach
    public void beforeEach() {
        this.recitation2 = new Recitation2();
    }

    @Test
    public void test() {
        assertEquals(2, 1 + 1);
    }

    @Test
    public void sumOfDigits() {
        assertEquals(15, recitation2.sumOfDigits(5));
    }
}