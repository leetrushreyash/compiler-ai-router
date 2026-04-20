// ============================================================
// TEST FILE: Injection & Input Vulnerabilities
// Triggers: FormatStringRule, CommandInjectionRule,
//           PathTraversalRule, HardcodedSecretsRule
// ============================================================

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

// TRIGGER: Format String Attack - user input passed as format string
void test_format_string(char* user_input) {
    printf(user_input);    // FORMAT STRING: should be printf("%s", user_input)
    fprintf(stdout, user_input); // Also a format string bug
}

// TRIGGER: Command Injection - unsanitized input to system()
void test_command_injection(const char* filename) {
    char cmd[256];
    sprintf(cmd, "ls -la %s", filename);
    system(cmd); // COMMAND INJECTION: filename could contain "; rm -rf /"
}

// TRIGGER: Path Traversal - no sanitization of file path from user
void test_path_traversal(const char* user_path) {
    char full_path[512];
    sprintf(full_path, "/var/data/%s", user_path);
    // user_path could be "../../etc/passwd"
    FILE* f = fopen(full_path, "r"); // PATH TRAVERSAL
    if (f) fclose(f);
}

// TRIGGER: Hardcoded Secrets
void test_hardcoded_secrets() {
    const char* password   = "SuperSecret123!";   // HARDCODED PASSWORD
    const char* api_key    = "sk-abcdef1234567890"; // HARDCODED API KEY
    const char* db_password = "root_pass_2024";   // HARDCODED DB PASSWORD
    const char* token      = "Bearer eyJhbGciO";  // HARDCODED TOKEN

    printf("Connecting with key: %s\n", api_key);
    printf("DB password: %s\n", db_password);
    (void)password;
    (void)token;
}

// Clean function: sanitized path joining
void safe_open(const char* filename) {
    // Only allow alphanumeric filenames
    for (const char* c = filename; *c; c++) {
        if (!isalnum(*c) && *c != '.') {
            printf("Invalid filename\n");
            return;
        }
    }
    FILE* f = fopen(filename, "r");
    if (f) fclose(f);
}

int main() {
    char input[] = "%s%s%s%s";
    test_format_string(input);
    test_command_injection("report.txt; rm -rf /");
    test_path_traversal("../../etc/passwd");
    test_hardcoded_secrets();
    safe_open("data.txt");
    return 0;
}
