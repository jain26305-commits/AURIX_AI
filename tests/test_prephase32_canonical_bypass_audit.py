import ast
from pathlib import Path


def _tree(path: str):
    return ast.parse(
        Path(path).read_text(encoding="utf-8-sig")
    )


def test_service_contains_canonical_claim_validator():
    tree = _tree("aurix_core/intelligence/service.py")

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ClaimValidator"
        and node.func.attr == "validate"
    ]

    assert calls


def test_service_contains_canonical_answer_composer():
    tree = _tree("aurix_core/intelligence/service.py")

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "AnswerComposer"
        and node.func.attr == "compose_validated_claims"
    ]

    assert calls


def test_canonical_validator_precedes_composer():
    tree = _tree("aurix_core/intelligence/service.py")

    validator_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ClaimValidator"
        and node.func.attr == "validate"
    ]

    composer_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "AnswerComposer"
        and node.func.attr == "compose_validated_claims"
    ]

    assert validator_lines
    assert composer_lines
    assert min(validator_lines) < min(composer_lines)


def test_composer_receives_validation_result():
    tree = _tree("aurix_core/intelligence/service.py")

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "AnswerComposer"
            and node.func.attr == "compose_validated_claims"
        ):
            keywords = {kw.arg for kw in node.keywords}
            assert "validation_result" in keywords
            assert "claims" in keywords
            return

    raise AssertionError(
        "Canonical AnswerComposer call not found."
    )


def test_service_returns_ai_response_contract():
    tree = _tree("aurix_core/intelligence/service.py")

    found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            value = node.value
            if isinstance(value, ast.Name):
                if value.id == "response_contract":
                    found = True

    assert found


def test_no_second_claim_validator_definition():
    paths = list(Path("aurix_core").rglob("*.py"))

    definitions = []

    for path in paths:
        tree = _tree(str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "ClaimValidator":
                    definitions.append(str(path))

    assert len(definitions) == 1


def test_no_second_answer_composer_definition():
    paths = list(Path("aurix_core").rglob("*.py"))

    definitions = []

    for path in paths:
        tree = _tree(str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "AnswerComposer":
                    definitions.append(str(path))

    assert len(definitions) == 1
