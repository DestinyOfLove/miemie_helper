"""文本预处理工具：用于索引前的文本规范化。"""


def normalize_text_for_indexing(text: str) -> str:
    """将提取文本的所有换行去除，拼接为单行长文本，用于索引和展示。

    去掉所有换行可以彻底解决 PDF/OCR 排版断行导致的分词问题（如一个词被
    拆到上下两行）。前端展示时依靠单元格宽度自动折行。
    """
    if not text:
        return text

    # 按换行切分，去掉每段首尾空白，过滤空行，直接拼接为一行
    parts = [line.strip() for line in text.split("\n") if line.strip()]
    return "".join(parts)
