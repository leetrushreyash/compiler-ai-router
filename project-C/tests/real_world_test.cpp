#include <iostream>
#include <vector>
#include <string>

// A completely standard, clean Binary Search function
// Should be predicted as CLEAN.
int binary_search(const std::vector<int>& arr, int target) {
    int left = 0;
    int right = arr.size() - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) {
            return mid;
        }
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}

// A monstrous string parser full of deeply nested loops, massive branching,
// and excessive node complexity. This is highly error-prone.
// Should be predicted as SMELLY.
void parse_legacy_data_format(std::string data) {
    std::vector<std::string> tokens;
    std::string current_token = "";
    
    for (size_t i = 0; i < data.length(); ++i) {
        if (data[i] == '{') {
            // Found an object
            for (size_t j = i + 1; j < data.length(); ++j) {
                if (data[j] == ':') {
                    for (size_t k = j + 1; k < data.length(); ++k) {
                        if (data[k] == '[') {
                            // Deep array processing inside object
                            while (data[k] != ']') {
                                if (data[k] == '"') {
                                    int q = k + 1;
                                    while (data[q] != '"') {
                                        current_token += data[q];
                                        q++;
                                        if (q > 1000) break; // Defensive break
                                    }
                                }
                                k++;
                            }
                        } else if (data[k] == '}') {
                            tokens.push_back(current_token);
                            current_token = "";
                            break;
                        }
                    }
                }
            }
        } else if (data[i] == ';') {
            tokens.clear();
        }
    }
}
