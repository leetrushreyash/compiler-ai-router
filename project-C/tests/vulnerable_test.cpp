#include <iostream>
#include <cstring>
#include <cstdio>


void processUserInput(const char* inputData) {
    char buffer[20];
    
    strcpy(buffer, inputData); 
    

    strcat(buffer, " processed");
    
    std::cout << "Data: " << buffer << std::endl;
}

void generateReport() {
    char reportMsg[50];
    int severity = 9;
    

    sprintf(reportMsg, "User report severity level: %d", severity);
    
    std::cout << reportMsg << std::endl;

    int* leakArray = new int[500];
    leakArray[0] = severity;
}

void promptUserName() {
    char name[40];
    std::cout << "Please enter your name: ";

    gets(name);
    

    char department[20];
    std::cout << "Enter department: ";
    scanf("%s", department);
    
    std::cout << "Hello " << name << " from " << department << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc > 1) {
        processUserInput(argv[1]);
    }
    generateReport();
    promptUserName();
    
    return 0;
}
