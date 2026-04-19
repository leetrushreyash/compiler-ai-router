#include <iostream>

void evaluate_image(int width, int height) {
    // 1. Integer Overflow in Memory Allocation
    char* imgData = new char[width * height];
}

void login_system() {
    // 2. Hardcoded Secrets
    const char* admin_password = "super_secret_password_123";
    
    // 3. Null Pointer Dereference
    int* dbConnection = nullptr;
    
    // Attempting to use dbConnection without checking
    *dbConnection = 1;
}

int main(int argc, char* argv[]) {
    evaluate_image(10000, 10000);
    login_system();
    return 0;
}
