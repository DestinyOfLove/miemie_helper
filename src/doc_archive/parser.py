"""从提取的文本中解析公文结构化字段。"""

import re
from pathlib import Path

# 公文种类关键词（按优先级排序）
DOC_TYPES = [
    "通知", "决定", "意见", "报告", "请示", "批复",
    "函", "通报", "公告", "命令", "议案", "纪要",
    "办法", "规定", "条例", "方案", "计划", "总结",
]


def parse_document_fields(text: str, file_path: str, year_hint: str = "") -> dict:
    """从文本中解析公文字段。"""
    # 预处理：合并换行，便于跨行匹配
    text_joined = re.sub(r"\n+", "\n", text)

    doc_number = extract_doc_number(text)
    year = year_hint or extract_year_from_doc_number(doc_number) or extract_year_from_filename(file_path)

    fields = {
        "发文字号": doc_number,
        "发文标题": extract_title(text_joined),
        "发文日期": extract_date(text),
        "发文机关": extract_issuing_authority(text, doc_number),
        "主送单位": extract_recipients(text),
        "公文种类": extract_doc_type_from_title(text_joined),
        "密级": extract_classification(text),
        "来源年份": year,
    }
    return fields


def extract_doc_number(text: str) -> str:
    """提取发文字号，如：国发〔2021〕29号、苏政办发（2017）8号。"""
    patterns = [
        r"[\u4e00-\u9fa5]{1,10}[发字办]\s*[〔\[【（(]\s*\d{4}\s*[〕\]】）)]\s*\d+\s*号",
        r"[\u4e00-\u9fa5]{1,10}[〔\[【（(]\s*\d{4}\s*[〕\]】）)]\s*(?:第?\s*)?\d+\s*号",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().strip()
    return ""


def extract_year_from_doc_number(doc_number: str) -> str:
    """从发文字号中提取年份。"""
    match = re.search(r"[〔\[【（(]\s*(\d{4})\s*[〕\]】）)]", doc_number)
    return match.group(1) if match else ""


def extract_year_from_filename(file_path: str) -> str:
    """从文件名中提取年份。"""
    name = Path(file_path).stem
    match = re.search(r"((?:19|20)\d{2})", name)
    return match.group(1) if match else ""


def extract_title(text_joined: str) -> str:
    """提取发文标题。支持跨行匹配。

    策略：找到"关于"开头，一直匹配到"的+公文种类"结束。
    允许中间有换行（已预处理为 \\n）。
    """
    # 构建种类匹配部分
    types_pattern = "|".join(DOC_TYPES)

    # 跨行匹配：允许中间有换行和空格
    pattern = rf"关于[\s\S]{{2,200}}?的\s*(?:{types_pattern})"
    match = re.search(pattern, text_joined)
    if match:
        title = match.group().strip()
        # 清理换行和多余空格
        title = re.sub(r"\s+", "", title)
        return title

    # 降级：匹配"关于...的..."句式
    pattern2 = rf"关于[\s\S]{{2,200}}?(?:{types_pattern})"
    match = re.search(pattern2, text_joined)
    if match:
        title = match.group().strip()
        title = re.sub(r"\s+", "", title)
        return title

    return ""


def extract_date(text: str) -> str:
    """提取发文日期。"""
    patterns = [
        # 中文数字日期：二〇二四年三月十五日
        r"[二一〇○零三四五六七八九十]{2,4}年[一二三四五六七八九十]{1,3}月[一二三四五六七八九十]{1,4}日",
        # 阿拉伯数字日期：2024年1月10日
        r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return re.sub(r"\s+", "", match.group())
    return ""


def extract_issuing_authority(text: str, doc_number: str) -> str:
    """提取发文机关。

    策略优先级：
    1. 从文档头部的"XX文件"行提取
    2. 从落款处提取（日期前一行）
    3. 从发文字号推断
    """
    # 策略1：头部"XX人民政府/委员会/办公厅 文件"
    header_pattern = r"([\u4e00-\u9fa5]{2,30}(?:人民政府|委员会|办公厅|办公室|局|部|厅|处|院))\s*(?:文件|$)"
    match = re.search(header_pattern, text)
    if match:
        return match.group(1).strip()

    # 策略2：落款 —— 日期前的行通常是发文机关
    lines = text.strip().split("\n")
    date_line_idx = None
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        # 匹配日期行
        if re.search(r"\d{4}\s*年\s*\d{1,2}\s*月|[二一〇○零三四五六七八九十]{2,4}年", line):
            date_line_idx = i
    if date_line_idx is not None:
        # 往上找非空行作为落款机关
        for j in range(date_line_idx - 1, max(date_line_idx - 5, -1), -1):
            candidate = lines[j].strip()
            if candidate and len(candidate) <= 30 and not re.search(r"[。，；：]", candidate):
                # 排除正文内容（含标点的行）
                return candidate

    # 策略3：从发文字号推断
    if doc_number:
        match = re.search(r"([\u4e00-\u9fa5]{2,20})[发字办]\s*[〔\[【（(]", doc_number)
        if match:
            return match.group(1).strip()

    return ""


def extract_recipients(text: str) -> str:
    """提取主送单位。

    策略：
    1. 显式的"主送："标记
    2. 标题后紧跟的称谓行（如"各市、县..."或"各省、自治区..."）
    """
    # 策略1：显式标记
    match = re.search(r"(?:主送|抄送)\s*[:：]\s*(.+?)(?:\n|$)", text)
    if match:
        return match.group(1).strip()

    # 策略2：标题后的称谓行
    types_pattern = "|".join(DOC_TYPES)
    # 找到标题结束位置
    title_end = re.search(rf"(?:{types_pattern})\s*\n", text)
    if title_end:
        after_title = text[title_end.end():]
        # 第一个非空行
        for line in after_title.split("\n"):
            line = line.strip()
            if not line:
                continue
            # 称谓特征：以"各"开头或包含"人民政府"
            if re.match(r"各[市省区县委]|.*人民政府", line):
                # 截到冒号
                recipient = re.split(r"[：:]", line)[0]
                return recipient
            break

    return ""


def extract_doc_type_from_title(text_joined: str) -> str:
    """从标题中提取公文种类（而非正文，避免误匹配）。"""
    # 先提取标题
    types_pattern = "|".join(DOC_TYPES)
    title_match = re.search(rf"关于[\s\S]{{2,200}}?的\s*({types_pattern})", text_joined)
    if title_match:
        return title_match.group(1)

    # 降级：在前 500 字中找种类关键词
    head = text_joined[:500]
    for dt in DOC_TYPES:
        if dt in head:
            return dt

    return ""


def extract_classification(text: str) -> str:
    """提取密级。仅匹配文档开头区域（前 200 字），避免正文误匹配。"""
    # 只在文档头部查找密级标记
    head = text[:200]
    classifications = ["绝密", "机密", "秘密", "内部"]
    for cls in classifications:
        if cls in head:
            return cls
    return ""
