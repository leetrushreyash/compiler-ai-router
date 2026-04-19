#include <iostream>
#include <cstdlib>

void bad_memory_management() {
    int* data = new int[100];
    
    // First free
    delete data;
    
    // Use After Free: accessing data after it's been deleted!
    data[0] = 50; 
    std::cout << data[0] << std::endl;
    
    // Double Free: deleting it again!
    delete data;
}

void risky_command_execution(char* userCommand) {
    // Command Injection: system call with user-controlled string!
    system(userCommand);
}

void secure_command() {
    // SECURE: Literal string
    system("ls -la");
}

int main(int argc, char* argv[]) {
    bad_memory_management();
    if (argc > 1) {
        risky_command_execution(argv[1]);
    }
    secure_command();
    return 0;
}
