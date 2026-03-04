import textwrap
from code_smell_compiler.feature_extraction.extractor import extract_features
from code_smell_compiler.parser.parser import parse_source


def test_long_method_detected():
    body = "\n".join([f"    x{i} = {i}" for i in range(70)])
    src = f"def huge():\n{body}\n"
    tree = parse_source(src)
    features, locations = extract_features(tree)
    assert features["long_method"] == 1
    assert locations["long_method"], "Should record line numbers for long methods"


def test_god_class_detected():
    methods = "\n\n".join([f"def m{i}(self):\n        return {i}" for i in range(13)])
    methods = textwrap.indent(methods, "    ")
    attrs = "\n".join([f"attr{i} = {i}" for i in range(11)])
    attrs = textwrap.indent(attrs, "    ")
    src = f"class Massive:\n{attrs}\n\n{methods}\n"
    tree = parse_source(src)
    features, locations = extract_features(tree)
    assert features["god_class"] == 1
    assert locations["god_class"], "Should record class line number"


def test_feature_envy_detected():
    src = textwrap.dedent(
        """
        class Helper:
            def __init__(self):
                self.value = 1
                self.other = 2
                self.extra = 3
                self.count = 4

        class RemoteUser:
            def __init__(self, helper):
                self.helper = helper

            def compute(self):
                helper_obj = self.helper
                return helper_obj.value + helper_obj.other + helper_obj.extra + helper_obj.count
        """
    )
    tree = parse_source(src)
    features, locations = extract_features(tree)
    assert features["feature_envy"] == 1
    assert locations["feature_envy"], "Should capture feature envy method location"


def test_data_class_detected():
    assigns = "\n".join([f"        self.field{i} = field{i}" for i in range(7)])
    params = ", ".join([f"field{i}=0" for i in range(7)])
    src = (
        f"class DataHolder:\n"
        f"    def __init__(self, {params}):\n"
        f"{assigns}\n"
    )
    tree = parse_source(src)
    features, locations = extract_features(tree)
    assert features["data_class"] == 1
    assert locations["data_class"], "Should capture data class line number"
