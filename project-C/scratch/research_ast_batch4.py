import tree_sitter_cpp
from tree_sitter import Language, Parser

code = b"""
#include <iostream>
#include <fstream>
#include <thread>

void test_path(char* filename) {
    FILE* f = fopen(filename, "r");
    
    std::ifstream file(filename);
    file.open(filename);
}

void test_uninit() {
    int x;
    int y = x + 5;
    
    int z;
    z = 10;
    int w = z + 5;
}

void test_thread() {
    int shared_var = 0;
    std::thread t([&shared_var]() {
        shared_var++;
    });
    t.join();
}
"""

CPP_LANGUAGE = Language(tree_sitter_cpp.language())
parser = Parser(CPP_LANGUAGE)
tree = parser.parse(code)

def walk(node, depth=0):
    print(f"{'  ' * depth}{node.type}: {node.text.decode('utf-8') if node.child_count == 0 else ''}")
    for child in node.children:
        walk(child, depth + 1)
        
walk(tree.root_node)
