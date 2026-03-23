import ast
import json
import re

from bfcl_eval.constants.enums import ReturnFormat
from bfcl_eval.parse_utils import (
    convert_to_function_call,
    default_decode_ast_prompting,
    default_decode_execute_prompting,
)


def _parse_json_arguments(args_string: str) -> dict:
    """Parse JSON arguments string with fallback for common malformations.

    Handles patterns commonly produced by vLLM/SGLang models:
    - trailing commas: {"city": "Seoul",}
    - single quotes: {'city': 'Seoul'}
    - Python literals: True/False/None instead of true/false/null
    """
    try:
        return json.loads(args_string)
    except json.JSONDecodeError:
        pass

    # Fallback 1: remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", args_string)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback 2: Python literal (single quotes, True/False/None)
    try:
        result = ast.literal_eval(args_string)
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    raise json.JSONDecodeError(
        f"Cannot parse arguments as JSON: {args_string!r}", args_string, 0
    )


def decode_ast(
    result,
    language: ReturnFormat = ReturnFormat.PYTHON,
    has_tool_call_tag: bool = False,
    is_fc: bool = True,
) -> list[dict]:
    """Unified AST decoder for server-side FC and prompting results.

    Args:
        result: For FC (is_fc=True), a list of single-key dicts
                [{func_name: json_string_or_dict}, ...].
                For prompting (is_fc=False), a raw text string.
        language: The return format (Python, Java, JavaScript, JSON, XML).
        has_tool_call_tag: Whether output is wrapped in <TOOLCALL> tags.
        is_fc: True for function-calling API results, False for prompting.
    """
    if is_fc:
        if not isinstance(result, list):
            raise ValueError(f"FC result must be a list, got {type(result).__name__}")
        decoded_output = []
        for invoked_function in result:
            if not isinstance(invoked_function, dict) or len(invoked_function) != 1:
                raise ValueError(
                    f"Each FC result item must be a single-key dict, got {invoked_function!r}"
                )
            name = next(iter(invoked_function))
            params = invoked_function[name]
            if params is None:
                params = {}
            elif isinstance(params, str):
                params = _parse_json_arguments(params)
            elif not isinstance(params, dict):
                raise ValueError(
                    f"Arguments for {name!r} must be str or dict, got {type(params).__name__}"
                )
            decoded_output.append({name: params})
        return decoded_output
    else:
        return default_decode_ast_prompting(result, language, has_tool_call_tag)


def decode_execute(
    result,
    has_tool_call_tag: bool = False,
    is_fc: bool = True,
) -> list[str]:
    """Unified execute decoder."""
    if is_fc:
        if not isinstance(result, list):
            raise ValueError(f"FC result must be a list, got {type(result).__name__}")
        return convert_to_function_call(result)
    else:
        return default_decode_execute_prompting(result, has_tool_call_tag)
