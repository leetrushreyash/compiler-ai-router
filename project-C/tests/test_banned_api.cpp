// ============================================================
// TEST FILE: Banned API Usage
// Triggers: BannedApiRule
// Banned functions: gets, strcpy, strcat, sprintf, scanf, system
// ============================================================

#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <iostream>

// TRIGGER: gets() - no bounds checking, classic buffer overflow
void test_gets() {
    char buffer[64];
    gets(buffer); // BANNED: use fgets() instead
    printf("You entered: %s\n", buffer);
}

// TRIGGER: strcpy() - no bounds check
void test_strcpy(const char* input) {
    char dest[32];
    strcpy(dest, input); // BANNED: use strncpy() or strlcpy() instead
    printf("%s\n", dest);
}

// TRIGGER: strcat() - can overflow buffer
void test_strcat(const char* extra) {
    char buf[32] = "Hello ";
    strcat(buf, extra); // BANNED: use strncat() instead
}

// TRIGGER: sprintf() - no limit on output length
void test_sprintf(int val) {
    char out[16];
    sprintf(out, "value=%d", val); // BANNED: use snprintf() instead
    printf("%s\n", out);
}

// TRIGGER: scanf() - no bounds checking
void test_scanf() {
    char name[16];
    scanf("%s", name); // BANNED: use scanf with field width: %15s
}

// TRIGGER: system() - command injection risk
void test_system(const char* cmd) {
    system(cmd); // BANNED: use exec family with args instead
}

// Clean function (no issues)
int add(int a, int b) {
    return a + b;
}

int main() {
    test_gets();
    test_strcpy("hello world");
    test_strcat("world");
    test_sprintf(42);
    test_scanf();
    test_system("ls -la");
    return 0;
}
