import tree_sitter_cpp
from tree_sitter import Language, Parser

code = b"""
void test_alloc(int width, int height) {
    // Integer overflow in alloc
    char* buf = new char[width * height];
}

void test_deref() {
    int* ptr = nullptr;
    // Null dereference
    *ptr = 10;
    
    // Hardcoded secret
    const char* api_key = "sk_live_123456789";
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
