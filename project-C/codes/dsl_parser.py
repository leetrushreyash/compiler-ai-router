import ply.lex as lex
import ply.yacc as yacc

# --- LEXER (Tokenization) ---
tokens = (
    'RULE',
    'ID',
    'NUMBER',
    'EQUALS',
    'GT',
    'LT',
    'GTE',
    'LTE',
    'AND',
    'OR'
)

t_ignore = ' \t'

t_RULE = r'RULE'
t_EQUALS = r'='
t_GT = r'>'
t_LT = r'<'
t_GTE = r'>='
t_LTE = r'<='
t_AND = r'AND'
t_OR = r'OR'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Check for reserved words
    if t.value == 'RULE':
        t.type = 'RULE'
    elif t.value == 'AND':
        t.type = 'AND'
    elif t.value == 'OR':
        t.type = 'OR'
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    if t.value[0] != '#': # Ignore comments manually if needed
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

# --- PARSER (Syntax & Semantics) ---
# Global state to hold rules and the current metrics being evaluated
parsed_rules = {}
current_metrics = {}

def p_statements_multiple(p):
    '''statements : statements statement
                  | statement'''
    pass

def p_statement_rule(p):
    '''statement : RULE ID EQUALS expression'''
    rule_name = p[2]
    rule_result = p[4]
    parsed_rules[rule_name] = rule_result

def p_expression_and(p):
    '''expression : expression AND condition'''
    p[0] = p[1] and p[3]

def p_expression_or(p):
    '''expression : expression OR condition'''
    p[0] = p[1] or p[3]

def p_expression_single(p):
    '''expression : condition'''
    p[0] = p[1]

def p_condition_gt(p):
    '''condition : ID GT NUMBER'''
    metric_val = current_metrics.get(p[1], 0)
    p[0] = metric_val > p[3]

def p_condition_lt(p):
    '''condition : ID LT NUMBER'''
    metric_val = current_metrics.get(p[1], 0)
    p[0] = metric_val < p[3]

def p_condition_gte(p):
    '''condition : ID GTE NUMBER'''
    metric_val = current_metrics.get(p[1], 0)
    p[0] = metric_val >= p[3]

def p_condition_lte(p):
    '''condition : ID LTE NUMBER'''
    metric_val = current_metrics.get(p[1], 0)
    p[0] = metric_val <= p[3]

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' on line {p.lineno}")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()

def evaluate_dsl(dsl_file_path, metrics_dict):
    """
    Reads the rules.dsl file, injects the extracted metrics, 
    and returns a list of Code Smells that evaluated to True.
    """
    global current_metrics, parsed_rules
    current_metrics = metrics_dict
    parsed_rules = {} # Reset

    try:
        with open(dsl_file_path, 'r') as f:
            dsl_code = f.read()
            
        # Remove comments from DSL code before parsing
        clean_code = "\n".join([line for line in dsl_code.split('\n') if not line.strip().startswith('#')])
        
        parser.parse(clean_code)
        
        # Filter rules that evaluated to True
        triggered_smells = [name for name, is_true in parsed_rules.items() if is_true]
        return triggered_smells
        
    except FileNotFoundError:
        print("Error: rules.dsl file not found!")
        return []
        
# For standalone testing
if __name__ == "__main__":
    dummy_metrics = {
        'FUNC_LOC': 250,
        'METHOD_COUNT': 15,
        'CYCLO_COMPLEXITY': 20,
        'MAX_NEST_DEPTH': 4
    }
    smells = evaluate_dsl('rules.dsl', dummy_metrics)
    print("Mock Metrics:", dummy_metrics)
    print("Triggered Smells:", smells)
