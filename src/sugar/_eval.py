from ast import (
    Add,
    BinOp,
    Call,
    Constant,
    Dict,
    Expression,
    List,
    Name,
    PyCF_ONLY_AST,
    Set,
    Sub,
    Tuple,
    UAdd,
    UnaryOp,
    USub,
    dump,
    expr,
    literal_eval,
)
from typing import Any

from sugar._utils import set_name


def convert(node: expr) -> Any:
    node_stack = [(node, True)]
    value_stack = []

    while node_stack:
        node, not_visited = node_stack.pop()

        if isinstance(node, Constant):
            value_stack.append(node.value)
        elif isinstance(node, Name):
            value_stack.append(node.id)
        elif isinstance(node, Tuple):
            if not_visited:
                node_stack.append((node, False))
                for elt in node.elts:
                    node_stack.append((elt, True))
            else:
                value_stack.append((*[value_stack.pop() for _ in node.elts],))
        elif isinstance(node, List):
            if not_visited:
                node_stack.append((node, False))
                for elt in node.elts:
                    node_stack.append((elt, True))
            else:
                value_stack.append([value_stack.pop() for _ in node.elts])
        elif isinstance(node, Set):
            if not_visited:
                node_stack.append((node, False))
                for elt in node.elts:
                    node_stack.append((elt, True))
            else:
                value_stack.append({value_stack.pop() for _ in node.elts})
        elif isinstance(node, Call):
            func = node.func
            if (
                isinstance(func, Name)
                and func.id == "set"
                and not (node.args or node.keywords)
            ):
                value_stack.append(set())
            else:
                break
        elif isinstance(node, Dict):
            if not_visited:
                node_stack.append((node, False))
                if None in node.keys:
                    break
                for key in node.keys:
                    node_stack.append((key, True))  # type: ignore
                for value in node.values:
                    node_stack.append((value, True))
            else:
                items = zip(
                    [value_stack.pop() for _ in node.keys],
                    [value_stack.pop() for _ in node.values],
                )
                value_stack.append(dict(items))
        elif isinstance(node, BinOp):
            if not_visited:
                node_stack.append((node, False))
                node_stack.append((node.left, True))
                node_stack.append((node.right, True))
            else:
                real = value_stack.pop()
                if not isinstance(real, (int, float)):
                    break
                imag = value_stack.pop()
                if not isinstance(imag, complex):
                    break
                op = node.op
                if isinstance(op, Add):
                    value_stack.append(real + imag)
                elif isinstance(op, Sub):
                    value_stack.append(real - imag)
                else:
                    break
        elif isinstance(node, UnaryOp):
            if not_visited:
                node_stack.append((node, False))
                node_stack.append((node.operand, True))
            else:
                operend = value_stack.pop()
                if not isinstance(operend, (int, float)):
                    break
                op = node.op
                if isinstance(op, UAdd):
                    value_stack.append(operend)
                elif isinstance(op, USub):
                    value_stack.append(-operend)
                else:
                    break
        else:
            break
    else:
        assert len(value_stack) == 1, value_stack
        return value_stack.pop()

    raise ValueError(f"invalid node {dump(node)}")


def ext_eval(source: str) -> Any:
    """An extended version of `ast.literal_eval` that supports using variables as strings."""
    try:
        expression = compile(source, "<string>", "eval", PyCF_ONLY_AST)
    except SyntaxError as exc:
        exc.with_traceback(None)
        raise
    assert isinstance(expression, Expression), f"invalid node {dump(expression)}"
    return convert(expression.body)


@set_name("int")
def int_(x: str) -> int:
    return int(x, 0)


@set_name("str")
def str_(x: str) -> str:
    try:
        expression = compile(x, "<string>", "eval", PyCF_ONLY_AST)
    except SyntaxError:
        pass
    else:
        assert isinstance(expression, Expression), f"invalid node {dump(expression)}"
        node = expression.body
        if isinstance(node, Constant):
            value = node.value
            if isinstance(value, str):
                return value
    return x


@set_name("bytes")
def bytes_(x: str) -> bytes:
    try:
        expression = compile(x, "<string>", "eval", PyCF_ONLY_AST)
    except SyntaxError:
        pass
    else:
        assert isinstance(expression, Expression), expression
        node = expression.body
        if isinstance(node, Constant):
            value = node.value
            if isinstance(value, bytes):
                return value
    return x.encode()


TRUE_VALS = ("true", "t")
FALSE_VALS = ("false", "f")


@set_name("bool")
def bool_(x: str) -> bool:
    y = x.lower()
    if y in TRUE_VALS:
        return True
    if y in FALSE_VALS:
        return False
    raise ValueError


NONE_VALS = ("none",)


def none(x: str) -> None:
    y = x.lower()
    if y in TRUE_VALS:
        return None
    raise ValueError


@set_name("any")
def any_(x: str) -> Any:
    try:
        expression = compile(x, "<string>", "eval", PyCF_ONLY_AST)
    except SyntaxError:
        return x
    assert isinstance(expression, Expression), f"invalid node {dump(expression)}"
    return convert(expression.body)


def timeit_eval() -> None:
    from timeit import timeit

    from sugar._utils import Shield

    shield = Shield()

    while True:
        try:
            source = input(">>> ")
        except EOFError:
            break

        with shield:
            print(f"{literal_eval(source) = !r}")
            print(f"{ext_eval(source) = !r}")

            n = 10_000

            t = timeit(
                "literal_eval(source)",
                number=n,
                globals={"literal_eval": literal_eval, "source": source},
            )

            print(f"literal_eval: {n} loops, {t:.6g} secs, {t/n:.6g} secs per loop")

            t = timeit(
                "ext_eval(source)",
                number=n,
                globals={"ext_eval": ext_eval, "source": source},
            )
            print(f"ext_eval: {n} loops, {t:.6g} secs, {t/n:.6g} secs per loop")


if __name__ == "__main__":
    timeit_eval()
