// ============================================================
// TEST FILE: Integer Safety & Threading Issues
// Triggers: IntegerOverflowAllocRule, UninitializedVariableRule,
//           InsecureThreadingRule
// ============================================================

#include <cstdlib>
#include <cstdio>
#include <string>
#include <pthread.h>

// TRIGGER: Integer Overflow in malloc/new allocation size
// An attacker can pass n=0x80000001 to cause (n * 8) to overflow to 8
void test_integer_overflow_alloc(int n) {
    // n * sizeof(int) can overflow if n is large enough
    int* arr = (int*)malloc(n * sizeof(int)); // INT OVERFLOW IN ALLOC
    if (!arr) return;

    for (int i = 0; i < 10; i++) {
        arr[i] = i;
    }
    free(arr);
}

// TRIGGER: Integer overflow in new[]
void test_new_overflow(unsigned int count) {
    // count * 4 can wrap around to 0 or a small number
    char* buf = new char[count * 4]; // INT OVERFLOW IN ALLOC
    buf[0] = 'A';
    delete[] buf;
}

// TRIGGER: Uninitialized Variable - used before being set
void test_uninitialized_var() {
    int result;     // UNINITIALIZED: declared but not assigned
    int x = 5;
    // 'result' is used before initialization
    if (x > 3) {
        printf("Result: %d\n", result); // Using uninitialized 'result'
    }
}

// TRIGGER: Uninitialized Pointer
void test_uninitialized_ptr() {
    int* ptr;   // UNINITIALIZED pointer
    *ptr = 42;  // Dereferencing uninitialized pointer
}

// TRIGGER: Insecure Threading - using rand() without seeding (not thread-safe)
// and using global state without synchronization
int g_shared_counter = 0; // Global mutable state

void* thread_func(void* arg) {
    // rand() is not thread-safe (uses shared global state)
    int val = rand(); // INSECURE THREADING
    g_shared_counter += val; // Race condition - no mutex
    return nullptr;
}

void test_insecure_threading() {
    pthread_t t1, t2;
    pthread_create(&t1, nullptr, thread_func, nullptr);
    pthread_create(&t2, nullptr, thread_func, nullptr);
    pthread_join(t1, nullptr);
    pthread_join(t2, nullptr);
    printf("Counter: %d\n", g_shared_counter);
}

// Clean function (no issues)
int safe_add(int a, int b) {
    return a + b;
}

int main() {
    test_integer_overflow_alloc(1000);
    test_new_overflow(1000);
    test_uninitialized_var();
    test_insecure_threading();
    printf("%d\n", safe_add(1, 2));
    return 0;
}
