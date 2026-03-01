"""从文件名分析 fake_data 目录下的公文分类，不读取文件内容。"""

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "fake_data"


def extract_info(filename: str) -> dict | None:
    """从文件名提取发文字号、关键词等信息。"""
    if filename.startswith("."):
        return None

    # 提取发文字号：深龙编办〔2025〕XX号
    match = re.match(r"(.+?〔\d+〕\d+号)\s+(.+)", filename)
    if not match:
        return {"raw": filename, "doc_id": None, "title": filename, "suffix": None}

    doc_id = match.group(1)
    title = match.group(2)

    # 提取文种后缀（通知/批复/函/决定/意见 等）
    suffix_match = re.search(r"的(通知|批复|函|决定|意见|报告|请示|公告|命令|办法|规定|方案|纪要)", title)
    suffix = suffix_match.group(1) if suffix_match else "未识别"

    return {"raw": filename, "doc_id": doc_id, "title": title, "suffix": suffix}


def classify_by_keyword(title: str) -> str:
    """根据标题关键词进行主题分类。"""
    patterns = [
        (r"人才工作力量", "人才工作力量"),
        (r"编外聘用人员员额.*(核增|核减|划转|明确)", "编外员额调整"),
        (r"(核增|核减|收回).*编外聘用人员员额", "编外员额调整"),
        (r"内设机构.*领导职数|领导职数.*内设机构|增设.*内设机构", "内设机构/职数调整"),
        (r"(调整|增设|增加).*领导职数", "内设机构/职数调整"),
        (r"(调整|增设).*内设机构设置", "内设机构/职数调整"),
        (r"党组织领导职数", "党组织职数调整"),
        (r"(收回|核减).*事业编制", "事业编制收回/核减"),
        (r"(调整|核定|核增).*编制", "编制调整"),
        (r"加挂.*牌子", "机构挂牌"),
        (r"更名", "机构更名"),
        (r"人员分流", "人员分流"),
        (r"机构编制事项", "机构编制综合事项"),
        (r"(职责|监管|分工)", "职责分工"),
        (r"公办.*学校.*领导职数|学校.*领导职数", "学校职数调整"),
        (r"增设.*领导职数", "内设机构/职数调整"),
        (r"转发", "转发文件"),
        (r"产业用地", "职责分工"),
        (r"预付式经营", "职责分工"),
    ]
    for pattern, category in patterns:
        if re.search(pattern, title):
            return category
    return "其他"


def main():
    files = sorted(os.listdir(DATA_DIR))
    docs = []
    for f in files:
        info = extract_info(f)
        if info:
            docs.append(info)

    print(f"{'=' * 60}")
    print(f"目录: {DATA_DIR}")
    print(f"文件总数: {len(docs)}")
    print(f"{'=' * 60}")

    # 1. 按文种后缀统计
    suffix_counter = Counter(d["suffix"] for d in docs)
    print(f"\n【一、文种分布】")
    for suffix, count in suffix_counter.most_common():
        print(f"  {suffix}: {count} 件")

    # 2. 按主题关键词分类
    theme_groups = defaultdict(list)
    for d in docs:
        theme = classify_by_keyword(d["title"])
        d["theme"] = theme
        theme_groups[theme].append(d)

    print(f"\n【二、主题分类】")
    for theme, items in sorted(theme_groups.items(), key=lambda x: -len(x[1])):
        print(f"\n  ▸ {theme}（{len(items)} 件）:")
        for item in items:
            doc_id = item["doc_id"] or "无字号"
            print(f"    - [{doc_id}] {item['title']}")

    # 3. 检查是否有疑似非正式公文（从文件名判断）
    non_formal_patterns = [
        (r"(申请|选机|登记|汇总|台账|清单|统计|报表|明细)", "表格类"),
        (r"(草稿|征求意见|初稿|修改稿|讨论稿)", "草稿类"),
        (r"(会议纪要|简报|信息|动态)", "信息类"),
        (r"(工作方案|实施方案|计划|规划|总结)", "方案/计划类"),
        (r"(请示|报告)", "请示报告类"),
    ]

    print(f"\n{'=' * 60}")
    print(f"【三、非正式公文筛查】")
    print(f"（基于文件名关键词判断，以下可能不是正式发文）")
    found_non_formal = False
    for d in docs:
        for pattern, label in non_formal_patterns:
            if re.search(pattern, d["title"]):
                print(f"  ⚠ [{label}] {d['raw']}")
                found_non_formal = True
                break
    if not found_non_formal:
        print(f"  ✓ 所有文件名均符合正式公文格式（发文字号+标题）")

    # 4. 检查重复/相似标题
    print(f"\n{'=' * 60}")
    print(f"【四、疑似重复文件】")
    title_groups = defaultdict(list)
    for d in docs:
        # 用标题的核心部分做分组
        title_groups[d["title"]].append(d)

    # 也检查字号相同但标题略有不同的
    id_groups = defaultdict(list)
    for d in docs:
        if d["doc_id"]:
            id_groups[d["doc_id"]].append(d)

    found_dup = False
    for doc_id, items in id_groups.items():
        if len(items) > 1:
            found_dup = True
            print(f"\n  ⚠ 同一字号 [{doc_id}] 出现 {len(items)} 次:")
            for item in items:
                print(f"    - {item['raw']}")

    if not found_dup:
        print(f"  ✓ 未发现重复字号")

    # 5. 总结
    print(f"\n{'=' * 60}")
    print(f"【五、总结】")
    print(f"  文件总数:     {len(docs)}")
    print(f"  文种类型:     {len(suffix_counter)} 种 ({', '.join(suffix_counter.keys())})")
    print(f"  主题分类:     {len(theme_groups)} 类")
    formal_count = sum(1 for d in docs if d["doc_id"])
    print(f"  有发文字号:   {formal_count} 件")
    print(f"  无发文字号:   {len(docs) - formal_count} 件")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
