// ============================================================
// TEST FILE: Memory Safety Issues
// Triggers: MemoryLeakRule, DoubleFreeRule, UseAfterFreeRule,
//           NullPointerDereferenceRule
// ============================================================

#include <cstdlib>
#include <cstdio>
#include <cstring>

// TRIGGER: Memory Leak - malloc with no corresponding free
void test_memory_leak() {
    int* data = (int*)malloc(100 * sizeof(int));
    data[0] = 42;
    printf("Value: %d\n", data[0]);
    // No free(data) -- MEMORY LEAK
}

// TRIGGER: Double Free - freeing a pointer twice
void test_double_free() {
    char* buf = (char*)malloc(64);
    strcpy(buf, "hello");
    printf("%s\n", buf);
    free(buf);   // First free -- OK
    free(buf);   // DOUBLE FREE -- undefined behavior
}

// TRIGGER: Use After Free - using a pointer after it's been freed
void test_use_after_free() {
    int* ptr = (int*)malloc(sizeof(int));
    *ptr = 10;
    free(ptr);          // Free
    printf("%d\n", *ptr); // USE AFTER FREE -- undefined behavior
}

// TRIGGER: Null Pointer Dereference - not checking malloc return
void test_null_deref() {
    int* p = (int*)malloc(sizeof(int));
    // No null check before dereferencing
    *p = 99;  // If malloc returns NULL, this is a null deref
    printf("%d\n", *p);
    free(p);
}

// TRIGGER: Null Pointer Dereference - explicit null
void test_explicit_null_deref() {
    int* p = nullptr;
    printf("%d\n", *p); // Explicit null dereference
}

// Clean version: proper allocation and check
int* safeAlloc(int size) {
    int* p = (int*)malloc(size * sizeof(int));
    if (p == nullptr) {
        return nullptr;
    }
    return p;
}

int main() {
    test_memory_leak();
    test_double_free();
    test_use_after_free();
    test_null_deref();
    test_explicit_null_deref();

    int* safe = safeAlloc(10);
    if (safe) {
        safe[0] = 1;
        free(safe);
    }
    return 0;
}
