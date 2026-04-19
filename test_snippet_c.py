import urllib.request as r, json

code = r'''
#include <bits/stdc++.h>
using namespace std;

// Global variable (bad practice)
char globalBuffer[50];

// Simulate user authentication
bool authenticate(char *username, char *password) {
    char storedUser[10] = "admin";
    char storedPass[10] = "1234";

    // ❌ Vulnerable: strcmp without length check
    if (strcmp(username, storedUser) == 0 &&
        strcmp(password, storedPass) == 0) {
        return true;
    }
    return false;
}

// Function with buffer overflow vulnerability
void readInput() {
    char buffer[20];

    cout << "Enter your name: ";
    
    // ❌ gets is unsafe (removed from modern C++)
    gets(buffer);

    // ❌ copying without bounds check
    strcpy(globalBuffer, buffer);

    cout << "Hello " << globalBuffer << endl;
}

// Function with command injection
void runCommand(string userInput) {
    string command = "echo " + userInput;

    // ❌ Direct system call with user input
    system(command.c_str());
}

// File reading without validation
void readFile(string filename) {
    ifstream file(filename);

    // ❌ No validation for path traversal
    if (!file) {
        cout << "File not found\n";
        return;
    }

    string line;
    while (getline(file, line)) {
        cout << line << endl;
    }
}

// Integer overflow example
void processData(int n) {
    int arr[10];

    // ❌ No bounds check
    for (int i = 0; i < n; i++) {
        arr[i] = i * 1000000;  // potential overflow
    }

    cout << "Processed data\n";
}

int main() {
    char username[20];
    char password[20];

    cout << "Username: ";
    cin >> username;

    cout << "Password: ";
    cin >> password;

    if (!authenticate(username, password)) {
        cout << "Access denied\n";
        return 0;
    }

    cout << "Access granted\n";

    int choice;
    cout << "1. Enter Name\n2. Run Command\n3. Read File\n4. Process Data\n";
    cin >> choice;

    if (choice == 1) {
        readInput();
    }
    else if (choice == 2) {
        string input;
        cin.ignore();
        getline(cin, input);
        runCommand(input);
    }
    else if (choice == 3) {
        string filename;
        cin >> filename;
        readFile(filename);
    }
    else if (choice == 4) {
        int n;
        cin >> n;
        processData(n);
    }

    return 0;
}
'''

req = r.Request('http://127.0.0.1:5001/analyze', data=json.dumps({'code': code}).encode(), headers={'Content-Type': 'application/json'})
try:
    print(r.urlopen(req).read().decode())
except BaseException as e:
    try:
        print(e.read().decode())
    except:
        print(str(e))