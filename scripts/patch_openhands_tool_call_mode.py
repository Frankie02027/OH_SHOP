#!/usr/bin/env python3
"""Patch OpenHands tool-calling compatibility for openhands-lm on LM Studio."""

import re
from pathlib import Path
import sys

LLM_TARGET = Path(
    "/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py"
)
FN_CONVERTER_TARGET = Path("/app/openhands/llm/fn_call_converter.py")
SDK_FN_CONVERTER_TARGET = Path(
    "/app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/"
    "fn_call_converter.py")

PATCH_SNIPPET = """        if model and 'openhands-lm' in model:
            llm_kwargs['native_tool_calling'] = False
"""

OLD_LLM_KWARGS_BLOCK = """        llm_kwargs = {
            'model': model,
            'base_url': base_url,
            'api_key': user.llm_api_key,
            'usage_id': 'agent',
        }

        return LLM(**llm_kwargs)
"""

OLD_DIRECT_RETURN_BLOCK = """        return LLM(
            model=model,
            base_url=base_url,
            api_key=user.llm_api_key,
            usage_id='agent',
        )
"""

NEW_BLOCK = """        llm_kwargs = {
            'model': model,
            'base_url': base_url,
            'api_key': user.llm_api_key,
            'usage_id': 'agent',
        }
        if model and 'openhands-lm' in model:
            llm_kwargs['native_tool_calling'] = False

        return LLM(**llm_kwargs)
"""

NEW_FIX_STOPWORD_BLOCK = """def _normalize_model_tool_markup(content: str) -> str:
    \"\"\"Normalize malformed mock function-calling markup from local models.\"\"\"
    content = content.replace('<|im_start|>', '').replace('<|im_end|>', '')
    content = re.sub(
        r'<function=([^>\\n]+)>',
        lambda match: '<function=' + match.group(1).strip().split()[0] + '>',
        content,
    )
    content = re.sub(
        r'<function=([^\\s>]+)[^>\\n]*(?:\\n)?(?=<parameter=)',
        r'<function=\\1>\\n',
        content,
    )
    content = re.sub(r'<function=([^\\s>]+)[^>]*>', r'<function=\\1>', content)
    content = re.sub(
        r'<parameter>\\s*([a-zA-Z0-9_]+)>(.*?)</parameter>',
        r'<parameter=\\1>\\2</parameter>',
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r'<parameter=(security_risk|summary)>.*?</parameter>\\s*',
        '',
        content,
        flags=re.DOTALL,
    )
    return content


def _fix_stopword(content: str) -> str:
    \"\"\"Fix missing stopwords and trim malformed extra tool-call markup.\"\"\"
    content = _normalize_model_tool_markup(content)
    first_function_idx = content.find('<function=')
    if first_function_idx == -1:
        return content

    first_close_idx = content.find('</function>', first_function_idx)
    if first_close_idx != -1:
        head = content[: first_close_idx + len('</function>')]
        tail = content[first_close_idx + len('</function>') :]
        if '<function=' not in tail:
            return head + tail
        return head

    end_candidates: list[int] = []
    for marker in ('<|im_start|>', '<|im_end|>'):
        marker_idx = content.find(marker, first_function_idx + len('<function='))
        if marker_idx != -1:
            end_candidates.append(marker_idx)

    next_function_idx = content.find('<function=', first_function_idx + len('<function='))
    if next_function_idx != -1:
        end_candidates.append(next_function_idx)

    if end_candidates:
        content = content[: min(end_candidates)].rstrip()

    if content.endswith('</'):
        return content.rstrip() + 'function>'
    return content.rstrip() + '\\n</function>'
"""

NEW_NORMALIZE_PARAM_BLOCK = """def _normalize_parameter_tags(fn_body: str) -> str:
    \"\"\"Normalize malformed parameter tags to the canonical format.\"\"\"
    fn_body = re.sub(
        r'<parameter=([a-zA-Z0-9_]+)=([^<]*)</parameter>',
        r'<parameter=\\1>\\2</parameter>',
        fn_body,
    )
    fn_body = re.sub(
        r'<parameter>\\s*([a-zA-Z0-9_]+)>(.*?)</parameter>',
        r'<parameter=\\1>\\2</parameter>',
        fn_body,
        flags=re.DOTALL,
    )
    fn_body = re.sub(
        r'<parameter=(security_risk|summary)>.*?</parameter>\\s*',
        '',
        fn_body,
        flags=re.DOTALL,
    )
    return fn_body
"""

FN_NAME_SNIPPET = """                fn_name = fn_match.group(1)
                fn_body = _normalize_parameter_tags(fn_match.group(2))
"""

FN_NAME_REPLACEMENT = """                raw_fn_name = fn_match.group(1)
                fn_name = raw_fn_name.strip().split()[0].splitlines()[0]
                if '<parameter=' in fn_name:
                    fn_name = fn_name.split('<parameter=', 1)[0].strip()
                fn_body = _normalize_parameter_tags(fn_match.group(2))
"""

UNKNOWN_PARAM_SNIPPET = """        # Validate parameter is allowed
        if allowed_params and param_name not in allowed_params:
            raise FunctionCallValidationError(
                f\"Parameter '{param_name}' is not allowed for function '{fn_name}'. \"
                f\"Allowed parameters: {allowed_params}\"
            )
"""

UNKNOWN_PARAM_REPLACEMENT = """        # Validate parameter is allowed
        if allowed_params and param_name not in allowed_params:
            if param_name in {'security_risk', 'summary'}:
                continue
            raise FunctionCallValidationError(
                f\"Parameter '{param_name}' is not allowed for function '{fn_name}'. \"
                f\"Allowed parameters: {allowed_params}\"
            )
"""

OPTIONAL_ARRAY_SNIPPET = """            elif param_name_to_type[param_name] == \"array\":
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    raise FunctionCallValidationError(
                        f\"Parameter '{param_name}' is expected to be an array.\"
                    )
"""

OPTIONAL_ARRAY_REPLACEMENT = """            elif param_name_to_type[param_name] == \"array\":
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    if param_name not in required_params:
                        continue
                    raise FunctionCallValidationError(
                        f\"Parameter '{param_name}' is expected to be an array.\"
                    )
"""

UNKNOWN_PARAM_SNIPPET_OLD = """        # Validate parameter is allowed
        if allowed_params and param_name not in allowed_params:
            raise FunctionCallValidationError(
                f\"Parameter '{param_name}' is not allowed for function '{fn_name}'. \"
                f'Allowed parameters: {allowed_params}'
            )
"""

OPTIONAL_ARRAY_SNIPPET_OLD = """            elif param_name_to_type[param_name] == 'array':
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    raise FunctionCallValidationError(
                        f\"Parameter '{param_name}' is expected to be an array.\"
                    )
"""

OPTIONAL_ARRAY_REPLACEMENT_OLD = """            elif param_name_to_type[param_name] == 'array':
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    if param_name not in required_params:
                        continue
                    raise FunctionCallValidationError(
                        f\"Parameter '{param_name}' is expected to be an array.\"
                    )
"""

MISSING_PARAMS_SNIPPET_OLD = """    # Check all required parameters are present
    missing_params = required_params - found_params
"""

MISSING_PARAMS_REPLACEMENT_OLD = """    # Check all required parameters are present
    missing_params = required_params - found_params - {'security_risk'}
"""


def _patch_llm_startup() -> int:
    if not LLM_TARGET.exists():
        print(f"target file not found: {LLM_TARGET}", file=sys.stderr)
        return 1

    text = LLM_TARGET.read_text(encoding="utf-8")
    if PATCH_SNIPPET not in text:
        replacement_source = None
        if OLD_DIRECT_RETURN_BLOCK in text:
            replacement_source = OLD_DIRECT_RETURN_BLOCK
        elif OLD_LLM_KWARGS_BLOCK in text:
            replacement_source = OLD_LLM_KWARGS_BLOCK

        if replacement_source is None:
            print(
                "expected OpenHands LLM configuration block not found; refusing blind patch",
                file=sys.stderr,
            )
            return 1

        backup = LLM_TARGET.with_suffix(LLM_TARGET.suffix + ".bak_oh_shop")
        if not backup.exists():
            backup.write_text(text, encoding="utf-8")

        text = text.replace(replacement_source, NEW_BLOCK, 1)
        LLM_TARGET.write_text(text, encoding="utf-8")
        print(
            "Applied OpenHands tool-calling compatibility patch for openhands-lm."
        )
    else:
        print("OpenHands tool-calling compatibility patch already present.")

    return 0


def _patch_single_fn_converter(target: Path) -> int:
    if not target.exists():
        print(f"target file not found: {target}", file=sys.stderr)
        return 1

    text = target.read_text(encoding="utf-8")
    original_text = text

    text = text.replace(
        "FN_REGEX_PATTERN = r'<function=([^>]+)>\\n(.*?)</function>'",
        "FN_REGEX_PATTERN = r'<function=([^\\s>]+)>\\s*(.*?)</function>'",
        1,
    )
    text = text.replace(
        "FN_REGEX_PATTERN = r'<function=([^\\\\s>]+)>\\\\s*(.*?)</function>'",
        "FN_REGEX_PATTERN = r'<function=([^\\s>]+)>\\s*(.*?)</function>'",
        1,
    )
    text = text.replace(
        'FN_REGEX_PATTERN = r"<function=([^>]+)>\\n?(.*?)</function>"',
        'FN_REGEX_PATTERN = r"<function=([^\\s>]+)>\\s*(.*?)</function>"',
        1,
    )
    text = text.replace(
        'FN_REGEX_PATTERN = r"<function=([^\\\\s>]+)>\\\\s*(.*?)</function>"',
        'FN_REGEX_PATTERN = r"<function=([^\\s>]+)>\\s*(.*?)</function>"',
        1,
    )
    fix_start = text.find("def _fix_stopword(content: str) -> str:\n")
    normalize_start = text.find(
        "def _normalize_parameter_tags(fn_body: str) -> str:\n")
    convert_start = text.find(
        "def convert_non_fncall_messages_to_fncall_messages(\n")

    if fix_start != -1 and normalize_start != -1 and fix_start < normalize_start:
        text = (text[:fix_start] + NEW_FIX_STOPWORD_BLOCK + "\n\n" +
                text[normalize_start:])

    normalize_start = text.find(
        "def _normalize_parameter_tags(fn_body: str) -> str:\n")
    convert_start = text.find(
        "def convert_non_fncall_messages_to_fncall_messages(\n")
    if (normalize_start != -1 and convert_start != -1
            and normalize_start < convert_start):
        text = (text[:normalize_start] + NEW_NORMALIZE_PARAM_BLOCK + "\n\n" +
                text[convert_start:])

    text = text.replace(FN_NAME_SNIPPET, FN_NAME_REPLACEMENT, 1)
    text = text.replace(
        UNKNOWN_PARAM_SNIPPET,
        UNKNOWN_PARAM_REPLACEMENT,
        1,
    )
    text = text.replace(
        UNKNOWN_PARAM_SNIPPET_OLD,
        UNKNOWN_PARAM_REPLACEMENT,
        1,
    )
    text = text.replace(
        OPTIONAL_ARRAY_SNIPPET,
        OPTIONAL_ARRAY_REPLACEMENT,
        1,
    )
    text = text.replace(
        OPTIONAL_ARRAY_SNIPPET_OLD,
        OPTIONAL_ARRAY_REPLACEMENT_OLD,
        1,
    )
    text = text.replace(
        MISSING_PARAMS_SNIPPET_OLD,
        MISSING_PARAMS_REPLACEMENT_OLD,
        1,
    )

    expected_regex_markers = (
        "FN_REGEX_PATTERN = r'<function=([^\\s>]+)>\\s*(.*?)</function>'",
        'FN_REGEX_PATTERN = r"<function=([^\\s>]+)>\\s*(.*?)</function>"',
    )
    if ("_normalize_model_tool_markup" not in text
            or "raw_fn_name = fn_match.group(1)" not in text
            or not any(marker in text for marker in expected_regex_markers)):
        print(
            "expected fn_call_converter compatibility markers not found; refusing blind patch",
            file=sys.stderr,
        )
        return 1

    if text != original_text:
        backup = target.with_suffix(target.suffix + ".bak_oh_shop")
        if not backup.exists():
            backup.write_text(original_text, encoding="utf-8")
        target.write_text(text, encoding="utf-8")
        print(
            f"Applied OpenHands fn_call_converter compatibility patch: {target}"
        )
    else:
        print(
            "OpenHands fn_call_converter compatibility patch already present: "
            f"{target}")

    return 0


def _patch_fn_converter() -> int:
    statuses = []
    for target in (FN_CONVERTER_TARGET, SDK_FN_CONVERTER_TARGET):
        if target.exists():
            statuses.append(_patch_single_fn_converter(target))
    return 0 if statuses and all(status == 0 for status in statuses) else 1


def main() -> int:
    llm_status = _patch_llm_startup()
    fn_status = _patch_fn_converter()
    return 0 if llm_status == 0 and fn_status == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
