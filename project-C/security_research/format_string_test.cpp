#include <iostream>
#include <cstdio>
#include <string>

void secure_usage(const char* userInput) {
    // SECURE: Format string is a literal
    printf("User input is: %s\n", userInput);
    
    // SECURE: fprintf with literal
    fprintf(stdout, "Log: %s\n", userInput);
}

void insecure_usage(const char* userInput) {
    // INSECURE: First argument is a variable
    printf(userInput); 
    
    char buffer[100];
    // INSECURE: Second argument is a variable
    sprintf(buffer, userInput);
    
    // INSECURE: fprintf with variable format
    fprintf(stderr, userInput);
}

int main(int argc, char* argv[]) {
    if (argc > 1) {
        secure_usage(argv[1]);
        insecure_usage(argv[1]);
    }
    return 0;
}
