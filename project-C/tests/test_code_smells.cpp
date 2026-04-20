// ============================================================
// TEST FILE: Code Smell Detection
// Triggers: God Method, Deeply Nested Code, Excessive Looping,
//           Spaghetti Code / Complex Branching, General Smell
// ============================================================

#include <iostream>
#include <string>
#include <vector>

// ---- SMELL 1: God Method / Giant Blob ----
// Has 300+ AST nodes, doing way too much in one function.
void godMethod() {
    int a = 1, b = 2, c = 3, d = 4, e = 5;
    int f = 6, g = 7, h = 8, i = 9, j = 10;
    int k = 11, l = 12, m = 13, n = 14, o = 15;
    int p = 16, q = 17, r = 18, s = 19, t = 20;
    int u = 21, v = 22, w = 23, x = 24, y = 25;
    int z = a + b + c + d + e + f + g + h + i + j;
    z += k + l + m + n + o + p + q + r + s + t;
    z += u + v + w + x + y;
    std::cout << z;
    // lots of repeated operations to bloat the AST
    int r1 = a * b - c + d / 2; int r2 = e * f - g + h / 2;
    int r3 = i * j - k + l / 2; int r4 = m * n - o + p / 2;
    int r5 = q * r + s - t + u; int r6 = v * w + x - y + z;
    int r7 = r1 + r2 - r3 * r4; int r8 = r5 * r6 - r7 + r1;
    int r9 = r2 + r3 - r4 * r5; int r10 = r6 * r7 - r8 + r9;
    int r11 = r1 * r2 + r3 - r4; int r12 = r5 + r6 - r7 * r8;
    int r13 = r9 * r10 + r11;    int r14 = r12 - r13 + r10;
    int r15 = r14 + r13 - r1;    int r16 = r15 * r2 + r3 - r4;
    int r17 = r16 + r15 - r14;   int r18 = r17 * r13 + r12;
    int r19 = r18 + r17 - r16;   int r20 = r19 * r18 + r17;
    std::cout << r20 << r19 << r18 << r17 << r16 << r15 << r14 << r13;
    std::cout << r12 << r11 << r10 << r9 << r8 << r7 << r6 << r5;
    std::cout << r4 << r3 << r2 << r1 << z;
}

// ---- SMELL 2: Deeply Nested Code ----
// Nesting depth > 15 levels triggers this smell.
void deeplyNested(int x) {
    if (x > 0) {
        if (x > 1) {
            if (x > 2) {
                if (x > 3) {
                    if (x > 4) {
                        if (x > 5) {
                            if (x > 6) {
                                if (x > 7) {
                                    if (x > 8) {
                                        if (x > 9) {
                                            if (x > 10) {
                                                if (x > 11) {
                                                    if (x > 12) {
                                                        if (x > 13) {
                                                            if (x > 14) {
                                                                std::cout << "Deep: " << x;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// ---- SMELL 3: Excessive Looping ----
// Has 5+ loop constructs = "Excessive Looping" smell.
void excessiveLoops(std::vector<int>& data) {
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            while (data.size() > 0) {
                data.pop_back();
            }
        }
    }
    int k = 0;
    do {
        k++;
    } while (k < 5);
    for (int m = 0; m < 3; m++) {
        std::cout << m;
    }
}

// ---- SMELL 4: Spaghetti Code / Complex Branching ----
// Has 9+ if-nodes = branching smell.
void spaghettiCode(int val) {
    if (val == 1) std::cout << "one";
    else if (val == 2) std::cout << "two";
    else if (val == 3) std::cout << "three";
    else if (val == 4) std::cout << "four";
    else if (val == 5) std::cout << "five";
    else if (val == 6) std::cout << "six";
    else if (val == 7) std::cout << "seven";
    else if (val == 8) std::cout << "eight";
    else if (val == 9) std::cout << "nine";
    else std::cout << "many";
}

// ---- CLEAN FUNCTION (for comparison) ----
int add(int a, int b) {
    return a + b;
}

int main() {
    std::vector<int> v = {1, 2, 3};
    godMethod();
    deeplyNested(20);
    excessiveLoops(v);
    spaghettiCode(7);
    std::cout << add(3, 4);
    return 0;
}
