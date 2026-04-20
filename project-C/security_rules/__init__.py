# This module runs all registered security checks on AST nodes.

def get_security_rules():
    """
    Dynamically loads all rule modules in this directory.
    Rules should implement a 'check(node, code, context)' function.
    """
    rules = []
    # To keep it simple and separate as requested, we can also manually list them
    # or use discovery. Let's start by manually importing for clarity and performance.
    from .banned_api_rule import BannedApiRule
    from .memory_leak_rule import MemoryLeakRule
    from .format_string_rule import FormatStringRule
    from .double_free_rule import DoubleFreeRule
    from .use_after_free_rule import UseAfterFreeRule
    from .command_injection_rule import CommandInjectionRule
    from .hardcoded_secrets_rule import HardcodedSecretsRule
    from .integer_overflow_alloc_rule import IntegerOverflowAllocRule
    from .null_pointer_dereference_rule import NullPointerDereferenceRule
    from .path_traversal_rule import PathTraversalRule
    from .uninitialized_variable_rule import UninitializedVariableRule
    from .insecure_threading_rule import InsecureThreadingRule
    
    rules = [
        BannedApiRule(), 
        MemoryLeakRule(), 
        FormatStringRule(),
        DoubleFreeRule(),
        UseAfterFreeRule(),
        CommandInjectionRule(),
        HardcodedSecretsRule(),
        IntegerOverflowAllocRule(),
        NullPointerDereferenceRule(),
        PathTraversalRule(),
        UninitializedVariableRule(),
        InsecureThreadingRule()
    ]
    
    from .yaml_rule_parser import load_yaml_rules
    import os
    yaml_dir = os.path.join(os.path.dirname(__file__), 'yaml_rules')
    yaml_rules = load_yaml_rules(yaml_dir)
    rules.extend(yaml_rules)
    
    return rules

def run_security_scans(root_node, code):
    """
    Walks the AST and executes all security rules.
    Returns a list of issue objects: {"message": str, "line": int, "function": str}
    """
    all_issues = []
    rules = get_security_rules()
    
    # Context to track state across a function (like news/deletes)
    # Some rules are per-node, some are per-function.
    
    def walk(node):
        # 1. Run per-node rules (like Banned APIs, Format Strings)
        for rule in rules:
            if hasattr(rule, 'check_node'):
                issue = rule.check_node(node, code)
                if issue:
                    all_issues.append(issue)
        
        # 2. Handle function-scope rules (like Memory Leaks)
        if node.type == 'function_definition':
            for rule in rules:
                if hasattr(rule, 'check_function'):
                    issues = rule.check_function(node, code)
                    if issues:
                        all_issues.extend(issues)
                        
        for child in node.children:
            walk(child)
            
    walk(root_node)
    return all_issues
