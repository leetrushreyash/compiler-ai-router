#include <iostream>
#include <cstring>
#include <cstdio>

void unsafe_buffer_copy(const char* input) {
    char buffer[10];
    // BANNED FUNCTION USAGE (Buffer Overflow Risk)
    strcpy(buffer, input); 
}

void formatting_vulnerability(const char* format_str) {
    char buffer[50];
    // BANNED FUNCTION USAGE (Format String Attack Risk)
    sprintf(buffer, format_str); 
}

void memory_leak_example() {
    int* ptr = new int[100];
    // MEMORY LEAK (Forgot to delete ptr before function ends)
}

void safe_method() {
    int* safe_ptr = new int[50];
    delete[] safe_ptr; // Safe, memory freed
}

int main() {
    unsafe_buffer_copy("This is a very long string that will break the buffer!");
    formatting_vulnerability("%s %s %s %s");
    memory_leak_example();
    safe_method();
    return 0;
}
