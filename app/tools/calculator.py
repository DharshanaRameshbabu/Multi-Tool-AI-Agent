import ast
import math
import re
from typing import Any, Union
from app.core.logging import logger

# Supported safe functions in math
SAFE_MATH_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "pi": math.pi,
    "e": math.e,
}

class SafeMathEvaluator(ast.NodeVisitor):
    """
    Safely evaluate mathematical expressions using AST.
    Prevents any arbitrary code execution, attribute lookups, or system calls.
    """
    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise ValueError(f"Unsupported operation or syntax: {type(node).__name__}")

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    def visit_Num(self, node):  # Backward compatibility for Python AST
        return node.n

    def visit_UnaryOp(self, node):
        val = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +val
        elif isinstance(node.op, ast.USub):
            return -val
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero is undefined")
            return left / right
        elif isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("Division by zero is undefined")
            return left // right
        elif isinstance(node.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Modulo by zero is undefined")
            return left % right
        elif isinstance(node.op, (ast.Pow, ast.BitXor)):  # Support ^ as power as well
            return left ** right
        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only standard math function calls are allowed")
        func_name = node.func.id.lower()
        if func_name not in SAFE_MATH_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not allowed in safe math evaluator")
        
        args = [self.visit(arg) for arg in node.args]
        func = SAFE_MATH_FUNCTIONS[func_name]
        return func(*args)

    def visit_Name(self, node):
        name = node.id.lower()
        if name in SAFE_MATH_FUNCTIONS:
            return SAFE_MATH_FUNCTIONS[name]
        raise ValueError(f"Unknown variable: '{node.id}'")


def preprocess_expression(expr: str) -> str:
    """Preprocess human natural language arithmetic patterns into standard math expressions."""
    cleaned = expr.strip()
    
    # Replace unicode symbols
    cleaned = cleaned.replace("×", "*").replace("÷", "/").replace("−", "-").replace("—", "-")
    
    # Handle commas in numbers like 2,500 -> 2500
    cleaned = re.sub(r'(\d),(\d)', r'\1\2', cleaned)
    
    # Handle percentage patterns like "25% of 800" or "25 percent of 800"
    cleaned = re.sub(r'([0-9.]+)\s*%\s*of\s*([0-9.]+)', r'(\1 / 100) * \2', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'([0-9.]+)\s*percent\s*(?:of)?\s*([0-9.]+)', r'(\1 / 100) * \2', cleaned, flags=re.IGNORECASE)
    
    # Handle standalone percentage e.g. "25%" or "25% * 2" (not followed by a number, which would be modulo)
    cleaned = re.sub(r'([0-9.]+)\s*%(?!\s*[0-9])', r'(\1 / 100)', cleaned)
    
    # Replace ^ with **
    cleaned = cleaned.replace("^", "**")
    
    return cleaned


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression and return the formatted result.
    
    Example:
    >>> calculate("25% of 800")
    '200'
    >>> calculate("120 * 45")
    '5400'
    >>> calculate("sqrt(144) + 12")
    '24'
    """
    try:
        clean_expr = preprocess_expression(expression)
        parsed_ast = ast.parse(clean_expr, mode="eval")
        evaluator = SafeMathEvaluator()
        result = evaluator.visit(parsed_ast)
        
        # Format integer results cleanly (e.g. 200.0 -> 200)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 6)
            
        logger.info(f"Calculator evaluated: '{expression}' -> {result}")
        return str(result)
    except ZeroDivisionError as zde:
        return f"Error: {str(zde)}"
    except Exception as e:
        logger.warning(f"Calculator failed to evaluate '{expression}': {e}")
        return f"Error evaluating expression: {str(e)}"
