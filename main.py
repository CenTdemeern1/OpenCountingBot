import ast
import wolframalpha
from configparser import ConfigParser

cfg = ConfigParser()
cfg.read("tokens.ini")

client = wolframalpha.Client(cfg.get("tokens","wolframalphatoken"))

def parse_and_evaluate_expression(expression):
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError:
        return
    if not all(isinstance(node, (ast.Expression,
            ast.UnaryOp, ast.unaryop,
            ast.BinOp, ast.operator,
            ast.Num)) for node in ast.walk(tree)):
        raise ArithmeticError(expression+" is not a valid or safe expression.")
    result = eval(compile(tree, filename='', mode='eval'))
    return result

def solve_wolframalpha(expression):
    res = client.query(expression)
    for pod in res.pods:
        if pod.id=="Solution":
            answers = []
            for subpod in pod.subpods:
                answers.append(subpod.plaintext)
            return answers


pal=parse_and_evaluate_expression
