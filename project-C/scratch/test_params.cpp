
#include <iostream>

void complex_function(int a, float b, double c, char d, std::string e, int* f, bool g, long h) {
    if (a > 0) {
        std::cout << b << std::endl;
    }
}

int main() {
    complex_function(1, 2.0f, 3.0, 'd', "test", nullptr, true, 4L);
    return 0;
}
