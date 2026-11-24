import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.tools.calculator import calculate, preprocess_expression

def test_basic_arithmetic():
    assert calculate("120 * 45") == "5400"
    assert calculate("100 + 250") == "350"
    assert calculate("500 - 125") == "375"
    assert calculate("1000 / 4") == "250"

def test_percentage_calculations():
    # As requested in project specs
    assert calculate("25% of 800") == "200"
    assert calculate("15% of 2,500") == "375"
    assert calculate("10% of 50") == "5"
    assert calculate("50%") == "0.5"

def test_advanced_math_operations():
    assert calculate("sqrt(144) + 12") == "24"
    assert calculate("2^4") == "16"
    assert calculate("2**3") == "8"
    assert calculate("round(3.14159, 2)") == "3.14"

def test_division_by_zero_safety():
    res = calculate("10 / 0")
    assert "Error" in res
    assert "Division by zero" in res

def test_modulo_by_zero_safety():
    res = calculate("10 % 0")
    assert "Error" in res
    assert "zero" in res.lower()

def test_invalid_syntax_handling():
    res = calculate("10 + * 5")
    assert "Error" in res

def test_security_ast_prevents_arbitrary_code():
    res = calculate("__import__('os').system('dir')")
    assert "Error" in res
