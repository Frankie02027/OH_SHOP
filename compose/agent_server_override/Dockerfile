FROM ghcr.io/openhands/agent-server:61470a1-python

RUN python - <<'PY'
from pathlib import Path

p = Path("/app/openhands/llm/fn_call_converter.py")
text = p.read_text(encoding="utf-8")

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

fix_start = text.find("def _fix_stopword(content: str) -> str:\n")
normalize_start = text.find("def _normalize_parameter_tags(fn_body: str) -> str:\n")
convert_start = text.find("def convert_non_fncall_messages_to_fncall_messages(\n")

new_fix = """def _normalize_model_tool_markup(content: str) -> str:
    \"\"\"Normalize malformed mock function-calling markup from local models.\"\"\"
    content = content.replace('<|im_start|>', '').replace('<|im_end|>', '')
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

    end_candidates = []
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

new_normalize = """def _normalize_parameter_tags(fn_body: str) -> str:
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
    return fn_body
"""

if fix_start != -1 and normalize_start != -1 and fix_start < normalize_start:
    text = text[:fix_start] + new_fix + "\n\n" + text[normalize_start:]

normalize_start = text.find("def _normalize_parameter_tags(fn_body: str) -> str:\n")
convert_start = text.find("def convert_non_fncall_messages_to_fncall_messages(\n")
if normalize_start != -1 and convert_start != -1 and normalize_start < convert_start:
    text = text[:normalize_start] + new_normalize + "\n\n" + text[convert_start:]

if "_normalize_model_tool_markup" not in text:
    raise SystemExit("failed to patch fn_call_converter")

p.write_text(text, encoding="utf-8")
PY
