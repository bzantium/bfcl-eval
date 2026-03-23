import ast
import builtins
import json
import re
from typing import Union

from bfcl_eval.constants.enums import ReturnFormat
from bfcl_eval.parser.java_parser import parse_java_function_call
from bfcl_eval.parser.js_parser import parse_javascript_function_call
from bfcl_eval.parser.json_parser import parse_json_function_call
from bfcl_eval.parser.xml_parser import (
    parse_concise_xml_function_call,
    parse_verbose_xml_function_call,
)


def convert_to_function_call(function_call_list):
    from bfcl_eval.decode import _parse_json_arguments

    if type(function_call_list) == dict:
        function_call_list = [function_call_list]
    # function_call_list is of type list[dict[str, str]] or list[dict[str, dict]]
    execution_list = []
    for function_call in function_call_list:
        for key, value in function_call.items():
            if isinstance(value, str):
                value = _parse_json_arguments(value)
            elif value is None:
                value = {}
            execution_list.append(
                f"{key}({','.join([f'{k}={repr(v)}' for k,v in value.items()])})"
            )

    return execution_list


def convert_value(value, type_str):
    """Convert a string value into its appropriate Python data type based on the provided type string."""

    if type_str in ("list", "dict"):
        try:
            return ast.literal_eval(value)
        except:
            return value

    type_class = getattr(builtins, type_str)
    try:
        return type_class(value)
    except ValueError:
        return value


def ast_parse(
    input_str: str,
    language: ReturnFormat = ReturnFormat.PYTHON,
    has_tool_call_tag: bool = False,
) -> list[dict]:
    if has_tool_call_tag:
        match = re.search(r"<TOOLCALL>(.*?)</TOOLCALL>", input_str, re.DOTALL)
        if match:
            input_str = match.group(1).strip()
        else:
            raise ValueError(f"No tool call tag found in input string: {input_str}")

    if language == ReturnFormat.PYTHON:
        # We only want to remove wrapping quotes that could have been added by the model.
        cleaned_input = input_str.strip().strip("'")
        parsed = ast.parse(cleaned_input, mode="eval")
        extracted = []
        if isinstance(parsed.body, ast.Call):
            extracted.append(resolve_ast_call(parsed.body))
        else:
            for elem in parsed.body.elts:
                assert isinstance(elem, ast.Call)
                extracted.append(resolve_ast_call(elem))
        return extracted

    elif language == ReturnFormat.JAVA:
        # Remove the [ and ] from the string
        return parse_java_function_call(input_str[1:-1])

    elif language == ReturnFormat.JAVASCRIPT:
        return parse_javascript_function_call(input_str[1:-1])

    elif language == ReturnFormat.VERBOSE_XML:
        match = re.search(r"<functions>(.*?)</functions>", input_str, re.DOTALL)
        if not match:
            raise ValueError(
                f"No XML function call found in input string: {input_str}. Missing <functions> tag."
            )
        return parse_verbose_xml_function_call(match.group(0))

    elif language == ReturnFormat.CONCISE_XML:
        match = re.search(r"<functions>(.*?)</functions>", input_str, re.DOTALL)
        if not match:
            raise ValueError(
                f"No XML function call found in input string: {input_str}. Missing <functions> tag."
            )
        return parse_concise_xml_function_call(match.group(0))

    elif language == ReturnFormat.JSON:
        json_match = re.search(r"\[.*\]", input_str, re.DOTALL)
        if json_match:
            input_str = json_match.group(0)
        return parse_json_function_call(input_str)

    else:
        raise NotImplementedError(f"Unsupported language: {language}")


def resolve_ast_call(elem):
    # Handle nested attributes for deeply nested module paths
    func_parts = []
    func_part = elem.func
    while isinstance(func_part, ast.Attribute):
        func_parts.append(func_part.attr)
        func_part = func_part.value
    if isinstance(func_part, ast.Name):
        func_parts.append(func_part.id)
    func_name = ".".join(reversed(func_parts))
    args_dict = {}
    for arg in elem.keywords:
        output = resolve_ast_by_type(arg.value)
        args_dict[arg.arg] = output
    return {func_name: args_dict}


def resolve_ast_by_type(value):
    if isinstance(value, ast.Constant):
        if value.value is Ellipsis:
            output = "..."
        else:
            output = value.value
    elif isinstance(value, ast.UnaryOp):
        output = -value.operand.value
    elif isinstance(value, ast.List):
        output = [resolve_ast_by_type(v) for v in value.elts]
    elif isinstance(value, ast.Dict):
        output = {
            resolve_ast_by_type(k): resolve_ast_by_type(v)
            for k, v in zip(value.keys, value.values)
        }
    elif isinstance(
        value, ast.NameConstant
    ):  # Added this condition to handle boolean values
        output = value.value
    elif isinstance(
        value, ast.BinOp
    ):  # Added this condition to handle function calls as arguments
        output = eval(ast.unparse(value))
    elif isinstance(value, ast.Name):
        output = value.id
    elif isinstance(value, ast.Call):
        if len(value.keywords) == 0:
            output = ast.unparse(value)
        else:
            output = resolve_ast_call(value)
    elif isinstance(value, ast.Tuple):
        output = tuple(resolve_ast_by_type(v) for v in value.elts)
    elif isinstance(value, ast.Lambda):
        output = eval(ast.unparse(value.body[0].value))
    elif isinstance(value, ast.Ellipsis):
        output = "..."
    elif isinstance(value, ast.Subscript):
        try:
            output = ast.unparse(value.body[0].value)
        except:
            output = ast.unparse(value.value) + "[" + ast.unparse(value.slice) + "]"
    else:
        raise Exception(f"Unsupported AST type: {type(value)}")
    return output


def default_decode_ast_prompting(
    result: str,
    language: ReturnFormat = ReturnFormat.PYTHON,
    has_tool_call_tag: bool = False,
) -> list[dict]:
    result = result.strip("`\n ")
    if not result.startswith("["):
        result = "[" + result
    if not result.endswith("]"):
        result = result + "]"
    decoded_output = ast_parse(result, language, has_tool_call_tag)
    return decoded_output


def default_decode_execute_prompting(
    result: str, has_tool_call_tag: bool = False
) -> list[str]:
    # Note: For execute, there are only Python entries, so we don't need to check the language.
    result = result.strip("`\n ")
    if not result.startswith("["):
        result = "[" + result
    if not result.endswith("]"):
        result = result + "]"
    decoded_output = ast_parse(
        result, language=ReturnFormat.PYTHON, has_tool_call_tag=has_tool_call_tag
    )
    return decoded_output_to_execution_list(decoded_output)


def parse_nested_value(value):
    """Parse a potentially nested value from the AST output."""
    if isinstance(value, dict):
        if all(isinstance(v, dict) for v in value.values()):
            func_name = list(value.keys())[0]
            args = value[func_name]
            args_str = ", ".join(f"{k}={parse_nested_value(v)}" for k, v in args.items())
            return f"{func_name}({args_str})"
        else:
            return (
                "{"
                + ", ".join(f"'{k}': {parse_nested_value(v)}" for k, v in value.items())
                + "}"
            )
    return repr(value)


def decoded_output_to_execution_list(decoded_output: list[dict]) -> list[str]:
    """Convert decoded output to a list of executable function calls."""
    execution_list = []
    for function_call in decoded_output:
        for key, value in function_call.items():
            args_str = ", ".join(f"{k}={parse_nested_value(v)}" for k, v in value.items())
            execution_list.append(f"{key}({args_str})")
    return execution_list


def parse_prompt_variation_params(input_str: str) -> tuple[str, bool, str, str, str]:
    """Parse format sensitivity config string."""
    _PATTERN = re.compile(
        r"^"
        r"ret_fmt=(?P<return_format>python|json|verbose_xml|concise_xml)"
        r"&tool_call_tag=(?P<has_tool_call_tag>True|False)"
        r"&func_doc_fmt=(?P<function_doc_format>python|xml|json)"
        r"&prompt_fmt=(?P<prompt_format>plaintext|markdown)"
        r"&style=(?P<prompt_style>classic|experimental)"
        r"$"
    )

    match = _PATTERN.match(input_str)
    if not match:
        raise ValueError(f"Invalid query format: {input_str!r}")

    return_format = match.group("return_format")
    has_tool_call_tag = match.group("has_tool_call_tag") == "True"
    function_doc_format = match.group("function_doc_format")
    prompt_format = match.group("prompt_format")
    prompt_style = match.group("prompt_style")

    return (
        return_format,
        has_tool_call_tag,
        function_doc_format,
        prompt_format,
        prompt_style,
    )
