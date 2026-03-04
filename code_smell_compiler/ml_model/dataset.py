import os
import random
import string
from typing import Tuple, List, Dict, Any
from pathlib import Path
from code_smell_compiler.parser.parser import parse_source
from code_smell_compiler.feature_extraction.extractor import extract_features

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "data"

VERBS = ["get", "set", "calculate", "fetch", "update", "process", "handle", "validate", "parse", "format", "load", "save", "delete", "create"]
NOUNS = ["user", "data", "config", "item", "record", "score", "value", "result", "buffer", "index", "counter", "response", "request", "event", "message", "file", "path"]
ADJECTIVES = ["active", "valid", "current", "temp", "max", "min", "total", "raw", "parsed", "new", "old"]

def identifier_generator(id_type="variable") -> str:
    if id_type == "variable":
        if random.random() < 0.5:
            return f"{random.choice(ADJECTIVES)}_{random.choice(NOUNS)}"
        else:
            return f"{random.choice(NOUNS)}_{random.choice(['id', 'list', 'dict', 'count', 'value'])}"
    elif id_type == "function":
        return f"{random.choice(VERBS)}_{random.choice(NOUNS)}"
    elif id_type == "class":
        return f"{random.choice(ADJECTIVES).capitalize()}{random.choice(NOUNS).capitalize()}Manager"
    return "var"

def statement_generator(indent=1) -> str:
    ind = "    " * indent
    stmt_types = ["assign", "call", "calc", "dict", "list", "print"]
    chosen = random.choice(stmt_types)
    var_name = identifier_generator("variable")
    
    if chosen == "assign":
        val = random.choice(["None", "True", "False", random.randint(0, 100), f'"{identifier_generator()}"'])
        return f"{ind}{var_name} = {val}"
    elif chosen == "call":
        func = identifier_generator("function")
        return f"{ind}{var_name} = self.{func}()" if random.random() < 0.3 else f"{ind}{var_name} = {func}()"
    elif chosen == "calc":
        return f"{ind}{var_name} = {random.randint(1,10)} * {random.randint(1,10)} + {random.randint(0,5)}"
    elif chosen == "dict":
        return f"{ind}{var_name} = {{'{identifier_generator()}': {random.randint(1, 100)}}}"
    elif chosen == "list":
        return f"{ind}{var_name} = [x for x in range({random.randint(2, 10)})]"
    elif chosen == "print":
        return f"{ind}print({var_name}) if '{var_name}' in locals() else None"
    
    return f"{ind}pass"

def function_generator(name=None, lines=5, indent=0, include_doc=True) -> str:
    ind = "    " * indent
    func_name = name or identifier_generator("function")
    body = [f"{ind}def {func_name}():"]
    if include_doc and random.random() < 0.4:
        body.append(f'{ind}    """Executes the {func_name} operation."""')
    for _ in range(lines):
        body.append(statement_generator(indent + 1))
    body.append(f"{ind}    return {identifier_generator('variable')}")
    return "\n".join(body)

def class_generator(name=None, methods=3, attrs=3, indent=0) -> str:
    ind = "    " * indent
    cls_name = name or identifier_generator("class")
    lines = [f"{ind}class {cls_name}:"]
    lines.append(f'{ind}    """Handles {cls_name} related business logic."""')
    
    lines.append(f"{ind}    def __init__(self):")
    for _ in range(max(1, attrs)):
        lines.append(f"{ind}        self.{identifier_generator('variable')} = {random.randint(0, 100)}")
        
    for _ in range(methods):
        lines.append("")
        method_name = identifier_generator("function")
        lines.append(f"{ind}    def {method_name}(self, data=None):")
        for _ in range(random.randint(2, 5)):
            lines.append(statement_generator(indent + 2))
        lines.append(f"{ind}        return True")
        
    return "\n".join(lines)
    
def generate_secret() -> str:
    style = random.choice(["aws", "github", "openai", "hex"])
    if style == "aws":
        return "AKIA" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    elif style == "github":
        return "ghp_" + "".join(random.choices(string.ascii_letters + string.digits, k=36))
    elif style == "openai":
        return "sk-" + "".join(random.choices(string.ascii_letters + string.digits, k=48))
    else:
        return "".join(random.choices(string.hexdigits, k=32))

def clean_module_generator() -> str:
    lines = ["import os", "import sys", "import math", "import collections"]
    
    if random.random() < 0.5:
        lines.append("\n# Configuration constants")
        lines.append(f"{identifier_generator('variable').upper()} = {random.randint(100, 5000)}")
    
    lines.append("\n" + function_generator(lines=random.randint(3, 8)))
    lines.append("\n" + class_generator(methods=random.randint(1, 3), attrs=random.randint(1, 4)))
    
    return "\n".join(lines)

def smell_injector(flags: dict) -> str:
    parts = ["import json\nimport requests\nfrom datetime import datetime"]
    
    if flags.get("hardcoded_secrets"):
        api_name = random.choice(["AWS_ACCESS_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "SECRET_KEY"])
        parts.append(f'{api_name} = "{generate_secret()}"')
        
    if flags.get("long_method"):
        parts.append(function_generator(name="process_large_dataset", lines=65))
        
    if flags.get("deep_nesting"):
        nest = "def check_complex_conditions(data):\n"
        nest += "    if data:\n"
        nest += "        for item in data:\n"
        nest += "            if item.get('valid'):\n"
        nest += "                with open('log.txt', 'a') as f:\n"
        nest += "                    if True:\n"
        nest += "                        f.write('Nested!')\n"
        nest += "    return False"
        parts.append(nest)
        
    if flags.get("nested_loops"):
        loops = "def crunch_numbers(matrix):\n"
        loops += "    total = 0\n"
        loops += "    for i in range(10):\n"
        loops += "        for j in range(10):\n"
        loops += "            for k in range(5):\n"
        loops += "                total += i * j * k\n"
        loops += "    return total"
        parts.append(loops)
        
    if flags.get("unsafe_eval_exec"):
        ev = "def evaluate_user_input(payload):\n"
        ev += "    try:\n"
        ev += "        result = eval(payload.get('formula', '0'))\n"
        ev += "        return result\n"
        ev += "    except Exception:\n"
        ev += "        return None"
        parts.append(ev)
        
    if flags.get("exception_swallowing"):
        sw = "def fetch_remote_config():\n"
        sw += "    try:\n"
        sw += "        with open('remote.cfg', 'r') as f:\n"
        sw += "            return f.read()\n"
        sw += "    except Exception:\n"
        sw += "        pass"
        parts.append(sw)
        
    if flags.get("duplicate_code_blocks"):
        name_1 = identifier_generator("function")
        name_2 = identifier_generator("function")
        body = "\n".join(statement_generator(indent=1) for _ in range(5))
        dup = f"def {name_1}(a, b):\n{body}\n    return a + b\n\n"
        dup += f"def {name_2}(a, b):\n{body}\n    return a + b"
        parts.append(dup)
        
    if flags.get("god_class"):
        gc = "class GlobalFacadeSystem:\n"
        for i in range(12):
            gc += f"    attr_{i} = {i}\n"
        gc += "\n"
        domains = ["payment", "email", "database", "ui", "auth"]
        for i in range(14):
            domain = random.choice(domains)
            gc += f"    def handle_{domain}_{i}(self, data):\n"
            gc += f"        self.attr_{i} += 1\n"
            gc += f"        return True\n\n"
        parts.append(gc)

    if flags.get("data_class"):
        dc = "class UserRecordEntity:\n"
        dc += "    def __init__(self, "
        params = [f"field_{i}=None" for i in range(8)]
        dc += ", ".join(params) + "):\n"
        for i in range(8):
            dc += f"        self.field_{i} = field_{i}\n"
        parts.append(dc)

    if flags.get("feature_envy"):
        fe = "class OrderProcessor:\n"
        fe += "    def calculate_totals(self, order, customer):\n"
        fe += "        address = customer.get_address()\n"
        fe += "        discount = customer.get_discount_tier().get_rate()\n"
        fe += "        tax = customer.get_tax_profile().calculate(order.amount)\n"
        fe += "        zipcode = address.zipcode.upper()\n"
        fe += "        return (order.amount - discount) + tax\n"
        parts.append(fe)
        
    if random.random() < 0.5:
        parts.append(class_generator(methods=1, attrs=1))

    return "\n\n".join(parts)

def dataset_balancer(n: int) -> List[dict]:
    num_clean = int(n * random.uniform(0.6, 0.8))
    labels = []
    
    for _ in range(num_clean):
        labels.append({
            "long_method": False, "deep_nesting": False, "nested_loops": False,
            "unsafe_eval_exec": False, "hardcoded_secrets": False, 
            "exception_swallowing": False, "duplicate_code_blocks": False,
            "god_class": False, "feature_envy": False, "data_class": False,
            "_is_clean": True
        })
        
    for _ in range(n - num_clean):
        flags = {"_is_clean": False}
        smell_pool = [
            "long_method", "deep_nesting", "nested_loops", "unsafe_eval_exec",
            "hardcoded_secrets", "exception_swallowing", "duplicate_code_blocks",
            "god_class", "feature_envy", "data_class"
        ]
        
        chosen_smells = random.sample(smell_pool, k=random.randint(1, 3))
        for smell in smell_pool:
            flags[smell] = smell in chosen_smells
            
        labels.append(flags)
        
    random.shuffle(labels)
    return labels

def generate_dataset(n: int = 200, out_csv: str = None) -> Tuple[List[dict], List[dict]]:
    samples = []
    actual_labels = []
    os.makedirs(EXAMPLES_DIR, exist_ok=True)
    
    target_labels = dataset_balancer(n)
    
    for i, flags in enumerate(target_labels):
        if flags.pop("_is_clean", False):
            src = clean_module_generator()
        else:
            src = smell_injector(flags)
            
        path = EXAMPLES_DIR / f"sample_{i}.py"
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)

        tree = parse_source(src)
        feats, locs = extract_features(tree)
        samples.append(feats)
        actual_labels.append(flags)

    return samples, actual_labels
