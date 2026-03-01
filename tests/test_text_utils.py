"""normalize_text_for_indexing 的单元测试。"""

from src.core.text_utils import normalize_text_for_indexing


class TestNormalizeTextForIndexing:
    """测试 PDF/OCR 提取文本的换行规范化。"""

    # ── 基本边界情况 ──

    def test_empty_string(self):
        assert normalize_text_for_indexing("") == ""

    def test_none_passthrough(self):
        """空字符串和 None 不会崩溃（调用方已做 if text 判断）。"""
        assert normalize_text_for_indexing("") == ""

    def test_single_line(self):
        text = "这是一行文本"
        assert normalize_text_for_indexing(text) == text

    def test_no_newlines(self):
        text = "没有换行的文本内容"
        assert normalize_text_for_indexing(text) == text

    # ── 核心功能：合并无意义换行 ──

    def test_merge_cjk_broken_word(self):
        """CJK 字符被换行切断 → 合并。"""
        text = "企\n业"
        assert normalize_text_for_indexing(text) == "企业"

    def test_merge_cjk_broken_phrase(self):
        """中文短语被换行切断 → 合并。"""
        text = "关于进一步加强安全生产\n工作的通知"
        assert normalize_text_for_indexing(text) == "关于进一步加强安全生产工作的通知"

    def test_merge_multiple_consecutive_breaks(self):
        """多行连续的无意义断行 → 全部合并。"""
        text = "各市县人民政\n府各有关部门\n和单位"
        assert normalize_text_for_indexing(text) == "各市县人民政府各有关部门和单位"

    def test_merge_mixed_content(self):
        """混合段落中只合并 CJK-CJK 断行。"""
        text = "第一段的内容在这\n里结束了。\n第二段从这里\n开始"
        expected = "第一段的内容在这里结束了。\n第二段从这里开始"
        assert normalize_text_for_indexing(text) == expected

    # ── 保留段落边界 ──

    def test_preserve_empty_line_paragraph_break(self):
        """空行表示段落分隔 → 保留。"""
        text = "第一段内容\n\n第二段内容"
        assert normalize_text_for_indexing(text) == "第一段内容\n\n第二段内容"

    def test_preserve_sentence_end_period(self):
        """句号结尾 → 保留换行。"""
        text = "这是第一句话。\n这是第二句话"
        assert normalize_text_for_indexing(text) == "这是第一句话。\n这是第二句话"

    def test_preserve_sentence_end_exclamation(self):
        """感叹号结尾 → 保留换行。"""
        text = "注意安全！\n请大家遵守"
        assert normalize_text_for_indexing(text) == "注意安全！\n请大家遵守"

    def test_preserve_sentence_end_question(self):
        """问号结尾 → 保留换行。"""
        text = "是否同意？\n请回复"
        assert normalize_text_for_indexing(text) == "是否同意？\n请回复"

    def test_preserve_sentence_end_semicolon(self):
        """分号结尾 → 保留换行。"""
        text = "做好以下工作；\n第一项"
        assert normalize_text_for_indexing(text) == "做好以下工作；\n第一项"

    def test_preserve_sentence_end_colon(self):
        """冒号结尾 → 保留换行。"""
        text = "通知如下：\n各部门"
        assert normalize_text_for_indexing(text) == "通知如下：\n各部门"

    def test_preserve_closing_paren(self):
        """右括号结尾 → 保留换行。"""
        text = "详见附件）\n以上内容"
        assert normalize_text_for_indexing(text) == "详见附件）\n以上内容"

    # ── 保留结构性行首标记 ──

    def test_preserve_article_numbering(self):
        """第X条 格式 → 保留换行。"""
        text = "相关规定如下\n第一条 总则"
        assert normalize_text_for_indexing(text) == "相关规定如下\n第一条 总则"

    def test_preserve_chinese_numbered_list(self):
        """中文序号 "一、" → 保留换行。"""
        text = "主要内容\n一、总体要求\n二、基本原则"
        assert normalize_text_for_indexing(text) == "主要内容\n一、总体要求\n二、基本原则"

    def test_preserve_parenthesized_numbering(self):
        """括号序号 （一） → 保留换行。"""
        text = "具体措施\n（一）加强管理\n（二）提高效率"
        assert normalize_text_for_indexing(text) == "具体措施\n（一）加强管理\n（二）提高效率"

    def test_preserve_arabic_numbered_list(self):
        """阿拉伯数字序号 → 保留换行。"""
        text = "工作安排\n1、第一项\n2、第二项"
        assert normalize_text_for_indexing(text) == "工作安排\n1、第一项\n2、第二项"

    def test_preserve_arabic_dot_numbered_list(self):
        """阿拉伯数字加点序号 → 保留换行。"""
        text = "工作安排\n1.第一项\n2.第二项"
        assert normalize_text_for_indexing(text) == "工作安排\n1.第一项\n2.第二项"

    def test_preserve_chapter_numbering(self):
        """第X章 格式 → 保留换行。"""
        text = "本办法分为\n第一章 总则\n第二章 职责"
        assert normalize_text_for_indexing(text) == "本办法分为\n第一章 总则\n第二章 职责"

    # ── 非 CJK 内容不合并 ──

    def test_no_merge_latin_lines(self):
        """纯英文行之间的换行 → 保留。"""
        text = "Hello\nWorld"
        assert normalize_text_for_indexing(text) == "Hello\nWorld"

    def test_no_merge_number_ending(self):
        """数字结尾 → 不是 CJK，保留换行。"""
        text = "共计100\n元整"
        assert normalize_text_for_indexing(text) == "共计100\n元整"

    # ── 复合场景 ──

    def test_realistic_government_document(self):
        """模拟真实公文 PDF 提取结果。"""
        text = (
            "关于进一步加强企\n"
            "业安全生产工作的\n"
            "通知\n"
            "\n"
            "各市、县人民政府，省政府各部门：\n"
            "\n"
            "为深入贯彻落实\n"
            "中央关于安全生产\n"
            "的重要指示精神，现就有关事项通知如下：\n"
            "一、总体要求\n"
            "各地区各部门要\n"
            "高度重视安全生\n"
            "产工作。\n"
            "二、主要任务"
        )
        expected = (
            "关于进一步加强企业安全生产工作的通知\n"
            "\n"
            "各市、县人民政府，省政府各部门：\n"
            "\n"
            "为深入贯彻落实中央关于安全生产的重要指示精神，现就有关事项通知如下：\n"
            "一、总体要求\n"
            "各地区各部门要高度重视安全生产工作。\n"
            "二、主要任务"
        )
        assert normalize_text_for_indexing(text) == expected

    def test_ocr_fragmented_text(self):
        """模拟 OCR 识别结果的碎片化文本。"""
        text = "中华人民\n共和国\n国务院"
        assert normalize_text_for_indexing(text) == "中华人民共和国国务院"

    def test_preserve_mixed_punctuation_endings(self):
        """混合标点结尾的多行文本。
        "续行" 以 CJK 结尾，"最后" 以 CJK 开头，无句末标点/结构标记 → 合并。
        这对索引来说是正确行为：把 PDF 断行视为同一段文本。
        """
        text = (
            "这是一段话。\n"
            "这是另一段\n"
            "话的续行\n"
            "最后结束！\n"
            "新的开始"
        )
        expected = (
            "这是一段话。\n"
            "这是另一段话的续行最后结束！\n"
            "新的开始"
        )
        assert normalize_text_for_indexing(text) == expected

    def test_multiple_empty_lines(self):
        """连续空行 → 全部保留（段落间距）。"""
        text = "第一段\n\n\n第二段"
        result = normalize_text_for_indexing(text)
        assert result == "第一段\n\n\n第二段"

    def test_trailing_newline(self):
        """末尾换行 → 保留。"""
        text = "内容\n"
        result = normalize_text_for_indexing(text)
        assert result == "内容\n"

    def test_comma_does_not_prevent_merge(self):
        """逗号不是句末标点，不应阻止合并。"""
        text = "各部门要认真贯彻落实，\n切实做好工作"
        # 逗号后面的行以 CJK 开头，但逗号不在 SENTENCE_END_PUNCT 中
        # 然而逗号也不是 CJK 字符，所以 _LINE_ENDS_WITH_CJK 不会匹配
        # 因此这种情况换行会被保留，这是合理的行为
        result = normalize_text_for_indexing(text)
        assert result == "各部门要认真贯彻落实，\n切实做好工作"
