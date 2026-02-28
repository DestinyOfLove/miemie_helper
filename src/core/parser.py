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
    """提取发文标题。支持跨行匹配。"""
    types_pattern = "|".join(DOC_TYPES)

    pattern = rf"关于[\s\S]{{2,200}}?的\s*(?:{types_pattern})"
    match = re.search(pattern, text_joined)
    if match:
        title = match.group().strip()
        title = re.sub(r"\s+", "", title)
        return title

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
        r"[二一〇○零三四五六七八九十]{2,4}年[一二三四五六七八九十]{1,3}月[一二三四五六七八九十]{1,4}日",
        r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return re.sub(r"\s+", "", match.group())
    return ""


def extract_issuing_authority(text: str, doc_number: str) -> str:
    """提取发文机关。"""
    header_pattern = r"([\u4e00-\u9fa5]{2,30}(?:人民政府|委员会|办公厅|办公室|局|部|厅|处|院))\s*(?:文件|$)"
    match = re.search(header_pattern, text)
    if match:
        return match.group(1).strip()

    lines = text.strip().split("\n")
    date_line_idx = None
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if re.search(r"\d{4}\s*年\s*\d{1,2}\s*月|[二一〇○零三四五六七八九十]{2,4}年", line):
            date_line_idx = i
    if date_line_idx is not None:
        for j in range(date_line_idx - 1, max(date_line_idx - 5, -1), -1):
            candidate = lines[j].strip()
            if candidate and len(candidate) <= 30 and not re.search(r"[。，；：]", candidate):
                return candidate

    if doc_number:
        match = re.search(r"([\u4e00-\u9fa5]{2,20})[发字办]\s*[〔\[【（(]", doc_number)
        if match:
            return match.group(1).strip()

    return ""


def extract_recipients(text: str) -> str:
    """提取主送单位。"""
    match = re.search(r"(?:主送|抄送)\s*[:：]\s*(.+?)(?:\n|$)", text)
    if match:
        return match.group(1).strip()

    types_pattern = "|".join(DOC_TYPES)
    title_end = re.search(rf"(?:{types_pattern})\s*\n", text)
    if title_end:
        after_title = text[title_end.end():]
        for line in after_title.split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(r"各[市省区县委]|.*人民政府", line):
                recipient = re.split(r"[：:]", line)[0]
                return recipient
            break

    return ""


def extract_doc_type_from_title(text_joined: str) -> str:
    """从标题中提取公文种类。"""
    types_pattern = "|".join(DOC_TYPES)
    title_match = re.search(rf"关于[\s\S]{{2,200}}?的\s*({types_pattern})", text_joined)
    if title_match:
        return title_match.group(1)

    head = text_joined[:500]
    for dt in DOC_TYPES:
        if dt in head:
            return dt

    return ""


def extract_classification(text: str) -> str:
    """提取密级。仅匹配文档开头区域（前 200 字）。"""
    head = text[:200]
    classifications = ["绝密", "机密", "秘密", "内部"]
    for cls in classifications:
        if cls in head:
            return cls
    return ""
