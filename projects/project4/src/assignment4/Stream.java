
import java.util.stream.*;
import java.util.*;

public class Stream {
    public static class Tweet {
        int id;
        String content;

        public Tweet(int id, String content) {
            this.id = id;
            this.content = content;
        }
    }

    public static void main(String[] args) {
        List<Tweet> tweets = new ArrayList<>();

        tweets.add(new Tweet(1, "hello world"));
        tweets.add(new Tweet(2, "this is a tweet 2"));
        tweets.add(new Tweet(3, "this is a tweet 3"));
        tweets.add(new Tweet(4, "this is a tweet 4"));
        tweets.add(new Tweet(5, "this is a tweet 5"));
        tweets.add(new Tweet(6, "this is a tweet 6"));
        tweets.add(new Tweet(7, "this is a tweet 7"));
        tweets.add(new Tweet(8, "this is a tweet 8"));
        
        // use streams
        List<String> resultWithStream = processWithStream(tweets);
        // don't use streams
        List<String> resultWithoutStream = processWithStream(tweets);

        resultWithStream.forEach(System.out::println);
        resultWithoutStream.forEach(System.out::println);
        
    }

    /**
     * Filters a list of tweets to those with an ID of
     * less than 5 and then returns those tweets' contents.
     * 
     * @param tweets a list of tweets
     * @return the list of the contents of all tweets with id < 5
     */
    public static List<String> processWithStream(List<Tweet> tweets) {
        List<String> contents = tweets
            .parallelStream()
            .filter(t -> t.id < 5)
            .map(t -> t.content)
            .collect(Collectors.toList());
        
        return contents;
    }

    /**
     * Filters a list of tweets to those with an ID of
     * less than 5 and then returns those tweets' contents.
     * 
     * @param tweets a list of tweets
     * @return the list of the contents of all tweets with id < 4
     */
    public static List<String> processWithoutStream(List<Tweet> tweets) {
        // filter
        List<Tweet> filtered = new ArrayList<>();
        for (int i = 0; i < tweets.size(); ++i) {
            if (tweets.get(i).id < 5) {
                filtered.add(tweets.get(i));
            }
        }

        // map
        List<String> contents = new ArrayList<>();
        for (int i = 0; i < filtered.size(); ++i) {
            contents.add(filtered.get(i).content);
        }
        
        return contents;
    }

    public static boolean filter(String tweet) {
        return tweet.contains("hello");
    }

    public static String mapContent(Tweet t) {
        return t.content;
    }
}



