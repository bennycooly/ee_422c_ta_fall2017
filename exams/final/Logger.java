

public class Logger {

    private static Logger logger = null;

    private Logger() {
        
    }

    // return the singleton instance
    public static Logger getLogger() {
        if (logger == null) {
            logger = new Logger();
        }
        return logger;
    }

    // instance methods

    public void info(String message) {
        System.out.println(message);
    }

    public void error(String message) {
        System.err.println(message);
    }


    public class Student {

        private String name;

        public Student(String name) {
            if (name == null) {
                // FIX THE LINE BELOW
                // this uses System.err.println()
                System.err.println("Name should not be null.");
                // write the Logger counterpart here



                return;
            }

            this.name = name;

            // FIX THE LINE BELOW
            // this uses System.out.println()
            System.out.println("Created a student with name: " + name);
            // write the Logger counterpart here




        }


    }




}




