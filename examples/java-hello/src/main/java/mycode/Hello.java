package mycode;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Hello {

    private static final Logger LOGGER = LoggerFactory.getLogger(Hello.class);

	public static void main(String[] args) {
		System.out.println("Hello " + Foo.FOO);
        LOGGER.warn("This is a log statement using a dependency JAR");
	}

    public static boolean alwaysTrue() {
        return true;
    }
}
