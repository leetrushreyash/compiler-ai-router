#include <stdio.h>

int main() {
    char name[50];
    gets(name); // YAML rule should catch this!
    return 0;
}
