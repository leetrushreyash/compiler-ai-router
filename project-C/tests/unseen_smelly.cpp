#include <iostream>

// This is a clean function
void say_hello() {
    std::cout << "Hello, World!" << std::endl;
}

// This function has deep nesting and complexity (Code Smell)
int complex_nested_loop(int x) {
    int result = 0;
    if (x > 0) {
        for (int i = 0; i < 10; ++i) {
            if (i % 2 == 0) {
                while (x < 100) {
                    if (x == 50) {
                        result += 1;
                        if (result > 5) {
                            for (int j = 0; j < 5; ++j) {
                                result *= 2;
                            }
                        }
                    }
                    x++;
                }
            }
        }
    }
    return result;
}
