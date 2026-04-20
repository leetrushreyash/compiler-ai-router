// ============================================================
// TEST FILE: Clean Code (No Issues Expected)
// Purpose: Verify the analyzer correctly identifies CLEAN code
//          and shows "CLEAN CODE (All Clear)" verdict.
// ============================================================

#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>

// Clean utility function
int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

// Clean string handling - no banned APIs
std::string greet(const std::string& name) {
    return "Hello, " + name + "!";
}

// Clean memory management using smart pointers
std::unique_ptr<int[]> safeAllocate(int size) {
    if (size <= 0 || size > 10000) {
        return nullptr;
    }
    return std::make_unique<int[]>(size);
}

// Clean iteration - no excessive loops
int sumVector(const std::vector<int>& data) {
    int total = 0;
    for (const auto& val : data) {
        total += val;
    }
    return total;
}

// Clean conditional logic - flat, readable branching
std::string classify(int score) {
    if (score >= 90) return "Excellent";
    if (score >= 75) return "Good";
    if (score >= 50) return "Average";
    return "Needs Improvement";
}

// Clean file handling
void readFileClean(const std::string& hardcodedPath) {
    std::ifstream file(hardcodedPath);
    if (!file.is_open()) {
        std::cerr << "Could not open file.\n";
        return;
    }
    std::string line;
    while (std::getline(file, line)) {
        std::cout << line << "\n";
    }
}

int main() {
    std::cout << add(3, 4) << "\n";
    std::cout << subtract(10, 5) << "\n";
    std::cout << greet("World") << "\n";

    auto arr = safeAllocate(10);
    if (arr) {
        for (int i = 0; i < 10; i++) arr[i] = i * 2;
        std::cout << arr[5] << "\n";
    }

    std::vector<int> nums = {1, 2, 3, 4, 5};
    std::cout << sumVector(nums) << "\n";
    std::cout << classify(85) << "\n";

    return 0;
}
