
public class GameException extends Exception {

    public GameException() {
        super();
    }
    
    public GameException(String message) {
        super(message);
    }

    @Override
    public String getMessage() {
        return "game gone wrong";
    }
}
