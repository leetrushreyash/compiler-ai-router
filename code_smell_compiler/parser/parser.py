import ast
from typing import Tuple

def parse_source(source: str) -> ast.AST:
    return ast.parse(source)

def parse_file_to_ast(path: str) -> Tuple[ast.AST, str]:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = parse_source(src)
    return tree, src
