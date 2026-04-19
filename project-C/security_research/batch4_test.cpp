#include <iostream>
#include <fstream>
#include <thread>

void test_path(char* filename) {
    // 8. Path Traversal Risk (dynamic path)
    FILE* f = fopen(filename, "r");
}

void test_uninit() {
    // 9. Uninitialized Variable Usage
    int x;
    int y = x + 5;
    
    // Correct usage
    int z = 10;
    int w = z + 5;
}

void test_thread() {
    // 10. Insecure Threading (No mutex)
    int shared_var = 0;
    std::thread t([&shared_var]() {
        shared_var++;
    });
    t.join();
}

int main(int argc, char* argv[]) {
    if (argc > 1) {
        test_path(argv[1]);
    }
    test_uninit();
    test_thread();
    return 0;
}
