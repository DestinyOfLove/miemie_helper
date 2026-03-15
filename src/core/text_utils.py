"""文本预处理工具：用于索引前的文本规范化。"""

import re

# CJK 统一汉字范围
_CJK = r"\u4e00-\u9fff"
# CJK 扩展 A/B 及兼容汉字（覆盖生僻字）
_CJK_EXT = r"\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f"
_CJK_ALL = _CJK + _CJK_EXT

# 句末标点：遇到这些结尾时保留换行
_SENTENCE_END_PUNCT = r"。！？；：）」』】\)>"

# 结构性行首标记：遇到这些开头时说明是新的逻辑段落
_STRUCT_LINE_START = re.compile(
    r"^(?:"
    r"第[一二三四五六七八九十百千\d]+[条章节款项]"
    r"|[一二三四五六七八九十]+[、．.]"
    r"|[（(][一二三四五六七八九十\d]+[）)]"
    r"|\d+[、．.\s]"
    r")"
)
_LINE_ENDS_WITH_CJK = re.compile(rf"[{_CJK_ALL}]\s*$")
_LINE_STARTS_WITH_CJK = re.compile(rf"^\s*[{_CJK_ALL}]")
_LINE_ENDS_WITH_SENT_PUNCT = re.compile(rf"[{_SENTENCE_END_PUNCT}]\s*$")


def normalize_text_for_indexing(text: str) -> str:
    """清理 PDF/OCR 文本中的无意义断行，仅用于索引。"""
    if not text:
        return text

    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    merged: list[str] = []
    index = 0

    while index < len(lines):
        current_line = lines[index]

        if not current_line.strip():
            merged.append("")
            index += 1
            continue

        accumulated = current_line.rstrip()
        is_struct_line = bool(_STRUCT_LINE_START.match(accumulated.strip()))

        while index + 1 < len(lines):
            next_line = lines[index + 1]

            if not next_line.strip():
                break

            if _LINE_ENDS_WITH_SENT_PUNCT.search(accumulated):
                break

            if is_struct_line:
                break

            next_stripped = next_line.strip()
            if _STRUCT_LINE_START.match(next_stripped):
                break

            if (
                _LINE_ENDS_WITH_CJK.search(accumulated)
                and _LINE_STARTS_WITH_CJK.match(next_line)
            ):
                accumulated += next_stripped
                index += 1
                continue

            break

        merged.append(accumulated)
        index += 1

    return "\n".join(merged)
