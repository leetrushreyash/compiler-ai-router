import tree_sitter_cpp
from tree_sitter import Language, Parser
import sys

code = b"""
#include <iostream>
#include <cstdlib>

void bad_memory_management() {
    int* data = new int[100];
    
    // First free
    delete data;
    
    // Use After Free: accessing data after it's been deleted!
    data[0] = 50; 
    std::cout << data[0] << std::endl;
    
    // Double Free: deleting it again!
    delete data;
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
