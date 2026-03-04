from typing import Dict, Any, Tuple
from ast import AST
from code_smell_compiler.ast_analysis.ast_utils import (
    get_function_nodes,
    get_class_nodes,
    get_method_nodes,
    function_length,
    class_length,
    max_nesting,
    count_nested_loops,
    find_nested_loop_lines,
    uses_eval_exec,
    find_hardcoded_secrets,
    find_exception_swallowing,
    detect_duplicate_functions,
    class_method_count,
    class_attribute_count,
    method_attribute_access_profile,
)

THRESHOLDS = {
    "long_method": 50,
    "deep_nesting": 4,
    "nested_loops": 1,
    "feature_envy_ratio": 2.0,
    "feature_envy_min_foreign": 3,
}

CLASS_THRESHOLDS = {
    "god_class_methods": 12,
    "god_class_attrs": 10,
    "god_class_lines": 300,
    "data_class_attrs": 6,
    "data_class_max_methods": 1,
}

def extract_features(tree: AST) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    features = {
        "long_method": 0,
        "deep_nesting": 0,
        "nested_loops": 0,
        "unsafe_eval_exec": 0,
        "hardcoded_secrets": 0,
        "exception_swallowing": 0,
        "duplicate_code_blocks": 0,
        "god_class": 0,
        "feature_envy": 0,
        "data_class": 0,
    }

    locations = {k: [] for k in features.keys()}

    funcs = get_function_nodes(tree)
    for f in funcs:
        length = function_length(f)
        if length >= THRESHOLDS["long_method"]:
            features["long_method"] = 1
            locations["long_method"].append(getattr(f, 'lineno', -1))

        nesting = max_nesting(f)
        if nesting >= THRESHOLDS["deep_nesting"]:
            features["deep_nesting"] = 1
            locations["deep_nesting"].append(getattr(f, 'lineno', -1))

        nested_loops = count_nested_loops(f)
        if nested_loops > THRESHOLDS["nested_loops"]:
            features["nested_loops"] = 1
            # collect specific nested loop line numbers
            lines = find_nested_loop_lines(f)
            if lines:
                locations["nested_loops"].extend(lines)

    for cls in get_class_nodes(tree):
        method_count = class_method_count(cls)
        attr_count = class_attribute_count(cls)
        cls_len = class_length(cls)

        if (
            method_count >= CLASS_THRESHOLDS["god_class_methods"]
            or attr_count >= CLASS_THRESHOLDS["god_class_attrs"]
            or cls_len >= CLASS_THRESHOLDS["god_class_lines"]
        ):
            features["god_class"] = 1
            locations["god_class"].append(getattr(cls, 'lineno', -1))

        if (
            attr_count >= CLASS_THRESHOLDS["data_class_attrs"]
            and method_count <= CLASS_THRESHOLDS["data_class_max_methods"]
        ):
            features["data_class"] = 1
            locations["data_class"].append(getattr(cls, 'lineno', -1))

        for fn in get_method_nodes(cls):
            self_attrs, foreign_attrs = method_attribute_access_profile(fn)
            if (
                foreign_attrs >= THRESHOLDS["feature_envy_min_foreign"]
                and foreign_attrs >= THRESHOLDS["feature_envy_ratio"] * max(1, self_attrs)
            ):
                features["feature_envy"] = 1
                locations["feature_envy"].append(getattr(fn, 'lineno', -1))

    evals = uses_eval_exec(tree)
    if evals:
        features["unsafe_eval_exec"] = 1
        for ln, name in evals:
            locations["unsafe_eval_exec"].append(ln)

    secrets = find_hardcoded_secrets(tree)
    if secrets:
        features["hardcoded_secrets"] = 1
        for ln, var in secrets:
            locations["hardcoded_secrets"].append(ln)

    swallowed = find_exception_swallowing(tree)
    if swallowed:
        features["exception_swallowing"] = 1
        for ln in swallowed:
            locations["exception_swallowing"].append(ln)

    dupes = detect_duplicate_functions(tree)
    if dupes:
        features["duplicate_code_blocks"] = 1
        for a, b in dupes:
            locations["duplicate_code_blocks"].append(a)
            locations["duplicate_code_blocks"].append(b)

    return features, locations
