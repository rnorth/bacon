package mytests;

import mycode.Hello;
import org.junit.Test;

import static org.junit.Assert.assertTrue;

/**
 * @author richardnorth
 */
public class SimpleTest {

    @Test
    public void testAMethod() {
        assertTrue(Hello.alwaysTrue());
    }
}
