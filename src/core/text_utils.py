"""文本预处理工具：用于索引前的文本规范化。"""

import re

# CJK 统一汉字范围
_CJK = r"\u4e00-\u9fff"
# CJK 扩展 A/B 及兼容汉字（覆盖生僻字）
_CJK_EXT = r"\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f"
# 合并所有 CJK 字符范围
_CJK_ALL = _CJK + _CJK_EXT

# 句末标点：遇到这些结尾时保留换行（表示真正的段落/句子边界）
_SENTENCE_END_PUNCT = r"。！？；：）」』】\)>"

# 结构性行首标记：这些开头说明是新的逻辑段落，不应与上一行合并
# 匹配模式：
#   - "第X条/章/节/款/项" 格式
#   - "一、" "二、" 等中文数字序号
#   - "（一）" "（二）" 等带括号的序号
#   - "1." "2." 等阿拉伯数字序号
#   - "1、" "2、" 等阿拉伯数字顿号序号
_STRUCT_LINE_START = re.compile(
    r"^(?:"
    r"第[一二三四五六七八九十百千\d]+[条章节款项]"  # 第X条/章/节
    r"|[一二三四五六七八九十]+[、．.]"  # 中文序号
    r"|[（(][一二三四五六七八九十\d]+[）)]"  # 括号序号
    r"|\d+[、．.\s]"  # 阿拉伯数字序号
    r")"
)

# 用于检测行尾是否为 CJK 字符（不含句末标点）
_LINE_ENDS_WITH_CJK = re.compile(rf"[{_CJK_ALL}]\s*$")

# 用于检测行首是否为 CJK 字符
_LINE_STARTS_WITH_CJK = re.compile(rf"^\s*[{_CJK_ALL}]")

# 用于检测行尾是否为句末标点
_LINE_ENDS_WITH_SENT_PUNCT = re.compile(rf"[{_SENTENCE_END_PUNCT}]\s*$")


def normalize_text_for_indexing(text: str) -> str:
    """清理 PDF/OCR 提取文本中的无意义换行，用于索引（FTS5 + 向量搜索）。

    仅合并那些明显由 PDF 排版产生的断行（上行以 CJK 字符结尾、下行以 CJK 字符
    开头），保留真正的段落边界（空行、句末标点、结构性行首标记）。

    此函数不改变原始文本的存储，仅在索引管道中使用。
    """
    if not text:
        return text

    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    merged: list[str] = []
    i = 0

    while i < len(lines):
        current_line = lines[i]

        # 空行 → 保留为段落分隔
        if not current_line.strip():
            merged.append("")
            i += 1
            continue

        # 尝试与后续行合并
        accumulated = current_line.rstrip()
        # 记录当前行是否以结构性标记开头（如 "一、总体要求"）
        is_struct_line = bool(_STRUCT_LINE_START.match(accumulated.strip()))

        while i + 1 < len(lines):
            next_line = lines[i + 1]

            # 下一行为空 → 段落边界，停止合并
            if not next_line.strip():
                break

            # 当前累积行以句末标点结尾 → 停止合并
            if _LINE_ENDS_WITH_SENT_PUNCT.search(accumulated):
                break

            # 当前行以结构性标记开头（如标题/序号行）→ 视为独立段落，不合并后续
            if is_struct_line:
                break

            # 下一行以结构性标记开头 → 停止合并
            next_stripped = next_line.strip()
            if _STRUCT_LINE_START.match(next_stripped):
                break

            # 核心判断：上行以 CJK 结尾 + 下行以 CJK 开头 → 合并（无意义断行）
            if (_LINE_ENDS_WITH_CJK.search(accumulated)
                    and _LINE_STARTS_WITH_CJK.match(next_line)):
                # 直接拼接，不加空格（中文不需要词间空格）
                accumulated += next_stripped
                i += 1
            else:
                # 非 CJK-CJK 断行（如英文、数字等），保留换行
                break

        merged.append(accumulated)
        i += 1

    return "\n".join(merged)
