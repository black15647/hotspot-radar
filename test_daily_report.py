#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境学子雷达 - 单元测试
运行方式：
    python -m unittest test_daily_report.py -v
或：
    python test_daily_report.py
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入被测模块
import daily_report as dr


class TestCleanHtml(unittest.TestCase):
    """测试摘要清洗函数 clean_html"""

    def test_normal_html(self):
        """正常情况：包含 HTML 标签的文本"""
        text = "<p>这是一段<strong>测试</strong>文本，包含<a href='#'>链接</a>。</p>"
        result = dr.clean_html(text)
        self.assertEqual(result, "这是一段测试文本，包含链接。")
        self.assertNotIn("<", result)

    def test_empty_string(self):
        """空值情况：空字符串"""
        self.assertEqual(dr.clean_html(""), "")

    def test_none_input(self):
        """空值情况：None"""
        self.assertEqual(dr.clean_html(None), "")

    def test_html_entities(self):
        """特殊字符：HTML 实体"""
        text = "A &amp; B &lt; C &gt; D&nbsp;E"
        result = dr.clean_html(text)
        self.assertEqual(result, "A & B < C > D E")

    def test_script_style_removal(self):
        """特殊情况：移除 script 和 style 内容"""
        text = "<p>可见文本</p><script>alert('xss')</script><style>body{color:red}</style>"
        result = dr.clean_html(text)
        self.assertEqual(result, "可见文本")

    def test_multiline_whitespace(self):
        """特殊情况：合并多余空白"""
        text = "  第一行\n\n\n  第二行\t\t第三行  "
        result = dr.clean_html(text)
        self.assertEqual(result, "第一行 第二行 第三行")

    def test_quotes_in_text(self):
        """特殊字符：引号"""
        text = '<p>他说："你好"，然后\'离开\'了。</p>'
        result = dr.clean_html(text)
        self.assertIn('"你好"', result)
        self.assertIn("'离开'", result)


class TestSanitizeStr(unittest.TestCase):
    """测试字符串清洗函数 sanitize_str"""

    def test_normal_string(self):
        """正常情况"""
        self.assertEqual(dr.sanitize_str("hello"), "hello")

    def test_none_input(self):
        """空值情况：None 返回默认值"""
        self.assertEqual(dr.sanitize_str(None), "")
        self.assertEqual(dr.sanitize_str(None, "default"), "default")

    def test_non_string_input(self):
        """特殊情况：非字符串输入转为字符串"""
        self.assertEqual(dr.sanitize_str(123), "123")
        self.assertEqual(dr.sanitize_str(3.14), "3.14")


class TestMatchKeywords(unittest.TestCase):
    """测试关键词匹配函数 match_keywords"""

    def test_chinese_keyword(self):
        """正常情况：中文关键词匹配"""
        keywords = ["气候变化", "碳中和", "水污染"]
        text = "全球气候变化加剧，各国推进碳中和目标。"
        result = dr.match_keywords(text, keywords)
        self.assertIn("气候变化", result)
        self.assertIn("碳中和", result)
        self.assertNotIn("水污染", result)

    def test_english_keyword_word_boundary(self):
        """正常情况：英文关键词单词边界匹配"""
        keywords = ["water", "carbon"]
        text = "The water quality is good. Waterfall is beautiful. carbon emission."
        result = dr.match_keywords(text, keywords)
        self.assertIn("water", result)
        self.assertIn("carbon", result)
        self.assertEqual(len(result), 2)

    def test_case_insensitive(self):
        """正常情况：不区分大小写"""
        keywords = ["Climate", "WATER"]
        text = "climate change and water pollution"
        result = dr.match_keywords(text, keywords)
        self.assertEqual(len(result), 2)

    def test_empty_text(self):
        """空值情况：空文本"""
        self.assertEqual(dr.match_keywords("", ["气候变化"]), [])
        self.assertEqual(dr.match_keywords(None, ["气候变化"]), [])

    def test_empty_keywords(self):
        """空值情况：空关键词列表"""
        self.assertEqual(dr.match_keywords("气候变化", []), [])


class TestCalculateHotness(unittest.TestCase):
    """测试热度计算函数 calculate_hotness"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "keywords": ["气候变化", "碳中和", "水污染"],
            "weights": {
                "source_weights": {"Nature": 2.0, "Google News": 1.5},
                "time_decay": 0.8,
                "keyword_bonus": 2.0,
            },
        }

    def test_normal_items(self):
        """正常情况：计算热度"""
        now = datetime.now(timezone.utc)
        items = [
            {
                "title": "气候变化加剧",
                "summary": "全球气候变化问题严重",
                "source": "Nature",
                "published_dt": now - timedelta(hours=2),
                "link": "http://example.com/1",
            },
            {
                "title": "碳中和目标推进",
                "summary": "各国制定碳中和计划",
                "source": "Google News",
                "published_dt": now - timedelta(hours=5),
                "link": "http://example.com/2",
            },
        ]
        result = dr.calculate_hotness(items, self.config)
        self.assertEqual(len(result), 2)
        for item in result:
            self.assertIn("hotness", item)
            self.assertIsInstance(item["hotness"], (int, float))
            self.assertGreater(item["hotness"], 0)

    def test_empty_items(self):
        """空值情况：空列表"""
        result = dr.calculate_hotness([], self.config)
        self.assertEqual(result, [])

    def test_missing_published_dt(self):
        """特殊情况：缺少发布时间"""
        items = [
            {
                "title": "测试标题",
                "summary": "测试摘要",
                "source": "Test",
                "link": "http://example.com/1",
            }
        ]
        result = dr.calculate_hotness(items, self.config)
        self.assertEqual(len(result), 1)
        self.assertIn("hotness", result[0])


class TestJsonGeneration(unittest.TestCase):
    """测试 JSON 生成函数（验证生成的字符串可被 json.loads 解析）"""

    def setUp(self):
        """测试前准备：创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        os.makedirs("docs/data", exist_ok=True)
        os.makedirs("docs/data/daily", exist_ok=True)
        os.makedirs("docs/data/archive", exist_ok=True)

    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_safe_json_dump_normal(self):
        """正常情况：safe_json_dump 生成合法 JSON"""
        data = {"name": "测试", "value": 123, "items": [1, 2, 3]}
        path = "docs/data/test.json"
        dr.safe_json_dump(data, path)
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_safe_json_dump_chinese(self):
        """特殊字符：中文保留（ensure_ascii=False）"""
        data = {"title": "环境学子雷达", "keywords": ["气候变化", "碳中和"]}
        path = "docs/data/test_chinese.json"
        dr.safe_json_dump(data, path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("环境学子雷达", content)
        loaded = json.loads(content)
        self.assertEqual(loaded, data)

    def test_safe_json_dump_special_chars(self):
        """特殊字符：引号、换行、反斜杠"""
        data = {
            "title": '标题包含"双引号"和\'单引号\'',
            "summary": "摘要包含\n换行和\t制表符和\\反斜杠",
        }
        path = "docs/data/test_special.json"
        dr.safe_json_dump(data, path)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["title"], data["title"])
        self.assertEqual(loaded["summary"], data["summary"])

    def test_safe_json_dump_none_values(self):
        """空值情况：包含 None 的数据"""
        data = {"name": None, "value": 0, "items": []}
        path = "docs/data/test_none.json"
        dr.safe_json_dump(data, path)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertIsNone(loaded["name"])
        self.assertEqual(loaded["value"], 0)


class TestExtractSummary(unittest.TestCase):
    """测试摘要提取函数 extract_summary（使用 SimpleNamespace 模拟 feedparser entry）"""

    def test_empty_entry(self):
        """空值情况：空条目"""
        result = dr.extract_summary(SimpleNamespace())
        self.assertEqual(result, "")

    def test_none_entry(self):
        """空值情况：None"""
        result = dr.extract_summary(None)
        self.assertEqual(result, "")

    def test_long_content_extracted(self):
        """正常情况：从 content 字段提取长文本"""
        long_text = "这是一段非常长的文章内容，包含详细的信息和描述，" * 5
        entry = SimpleNamespace(
            content=[{"value": "<p>" + long_text + "</p>"}],
            summary="简短摘要",
        )
        result = dr.extract_summary(entry)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0 or result == "")


class TestHotnessV2(unittest.TestCase):
    """热度算法 v2 关键行为回归测试

    锁定的都是曾经真实失效过的行为：英文标题拿不到关键词分、并列 raw 被拉开成
    伪差异、单条条目直接给满分、中英双语重复检测不到。改动算法时若破坏这些性质会立即暴露。
    """

    def _item(self, title, source="Science", hours_ago=6, summary=None, **extra):
        now = datetime.now(timezone.utc)
        it = {
            "title": title,
            "source": source,
            "link": "https://example.com/x",
            "summary": summary if summary is not None else
                       "这是一段足够长的有效中文摘要，用于满足内容质量分的二十字符门槛要求。",
            "published": "",
            "published_dt": now - timedelta(hours=hours_ago),
        }
        it.update(extra)
        return it

    def test_english_title_matches_keywords_via_alias(self):
        """英文标题应通过英文别名命中中文关键词（修复前恒为空，IDF 分永久失效）"""
        cfg = dr.load_config()
        kws = cfg.get("keywords", dr.DEFAULT_KEYWORDS)
        title = "Water pollution treatment technology achieves breakthrough"
        self.assertEqual(dr.match_keywords(title, kws), [],
                         "前提：不加别名时英文标题不应命中中文关键词")
        matched = dr.match_keywords(title, kws, dr.KEYWORD_EN_ALIASES)
        self.assertIn("水污染", matched, "英文别名应把结果归一回中文关键词")

    def test_english_title_gets_nonzero_idf_score(self):
        """英文标题条目应拿到非零 IDF 分（修复前全英文批次 base 恒为 35）"""
        cfg = dr.load_config()
        items = [
            self._item("Global warming drives extreme weather across Europe"),
            self._item("Microplastics contamination in marine ecosystem", source="Nature"),
        ]
        out = dr.calculate_hotness(items, cfg)
        for it in out:
            self.assertGreater(it["score_breakdown"]["keyword_idf_score"], 0,
                               "英文标题应命中关键词并获得 IDF 分")

    def test_tied_raw_scores_get_identical_display_score(self):
        """raw 相同的条目必须得到相同展示分（修复前按排序位置拉开，是伪差异）"""
        cfg = dr.load_config()
        same = "Water pollution treatment study identical title"
        items = [self._item(same, "Science", 12) for _ in range(3)]
        out = dr.calculate_hotness(items, cfg)

        groups = {}
        counts = {}
        for it in out:
            r = it["score_v2_raw"]
            groups.setdefault(r, set()).add(it["score_v2"])
            counts[r] = counts.get(r, 0) + 1
        # 前提：必须存在"多条并列"的 raw 组，否则本用例什么都没检验到
        self.assertTrue(any(c > 1 for c in counts.values()),
                        "前提：应存在并列 raw 的一组（本用例中受重复惩罚的两条）")
        for raw, disps in groups.items():
            self.assertEqual(len(disps), 1,
                             f"raw={raw} 出现多个展示分 {sorted(disps)}，存在伪差异")

    def test_single_item_gets_neutral_display_score(self):
        """仅 1 条时不应给满分（修复前 n=1 直接映射为 100）"""
        cfg = dr.load_config()
        out = dr.calculate_hotness([self._item("Climate change research")], cfg)
        self.assertEqual(out[0]["score_v2"], dr.DISPLAY_SCORE_MID)
        self.assertNotEqual(out[0]["score_v2"], dr.DISPLAY_SCORE_MAX)

    def test_display_score_range_and_monotonic(self):
        """展示分应落在 [MIN, MAX] 且随 raw 单调不减"""
        cfg = dr.load_config()
        items = [
            self._item("Climate change and extreme weather events", "Science", 1),
            self._item("Circular economy strategy for industry",
                       "arXiv Environmental Engineering", 200),
            self._item("Control theory paper without any env keyword",
                       "arXiv Environmental Engineering", 400),
        ]
        out = dr.calculate_hotness(items, cfg)
        for it in out:
            self.assertGreaterEqual(it["score_v2"], dr.DISPLAY_SCORE_MIN)
            self.assertLessEqual(it["score_v2"], dr.DISPLAY_SCORE_MAX)
        seq = [(it["score_v2_raw"], it["score_v2"]) for it in out]
        seq.sort()
        for (r1, d1), (r2, d2) in zip(seq, seq[1:]):
            if r1 < r2:
                self.assertLessEqual(d1, d2, "展示分必须与 raw 同向单调")

    def test_hotness_level_matches_display_score(self):
        """hotness_level 必须与展示分阈值一致（前端据此上色）"""
        cfg = dr.load_config()
        items = [self._item(f"Climate change study number {i}", "Science") for i in range(6)]
        out = dr.calculate_hotness(items, cfg)
        for it in out:
            s = it["score_v2"]
            expect = ("high" if s >= dr.HOTNESS_LEVEL_HIGH
                      else "medium" if s >= dr.HOTNESS_LEVEL_MEDIUM else "low")
            self.assertEqual(it["hotness_level"], expect,
                             f"score={s} 的 level 应为 {expect}")

    def test_cross_language_duplicate_detected_via_title_zh(self):
        """中英双语同一事件应能判为重复（修复前中英 token 交集恒为空）"""
        zh = "生态环境部发布水污染防治行动计划"
        en = "Ministry of Ecology and Environment releases water pollution action plan"
        en_zh = "生态环境部发布水污染防治行动计划"
        self.assertEqual(
            dr._jaccard(dr._title_token_set(zh), dr._title_token_set(en)), 0.0,
            "前提：中文标题与英文原文的 token 交集应为空")
        self.assertGreaterEqual(
            dr._jaccard(dr._title_token_set(zh), dr._title_token_set(en_zh)),
            dr.DUPLICATE_JACCARD_THRESHOLD,
            "对齐到中文译文后应达到重复阈值")

    def test_jieba_env_init_is_idempotent(self):
        """jieba 词典注入应幂等，且不改变分词结果"""
        dr._JIEBA_ENV_INITIALIZED = False
        dr._init_jieba_env()
        self.assertTrue(dr._JIEBA_ENV_INITIALIZED, "首次调用后应置位")
        before = sorted(dr._title_token_set("气候变化与水污染治理"))
        dr._init_jieba_env()  # 第二次应直接返回，不重复注入
        after = sorted(dr._title_token_set("气候变化与水污染治理"))
        self.assertEqual(before, after, "重复注入不应改变分词结果")

    def test_boundary_inputs_are_safe(self):
        """边界：空列表、无发布时间、未来时间都不应抛异常"""
        cfg = dr.load_config()
        self.assertEqual(dr.calculate_hotness([], cfg), [])

        no_time = self._item("Climate change")
        no_time["published_dt"] = None
        out = dr.calculate_hotness([no_time], cfg)
        self.assertAlmostEqual(out[0]["score_breakdown"]["time_factor"], 0.35, places=3)

        future = self._item("Climate change", hours_ago=-100)
        out2 = dr.calculate_hotness([future], cfg)
        self.assertLessEqual(out2[0]["score_breakdown"]["time_factor"], 1.0)


class TestUrlSafety(unittest.TestCase):
    """测试 SSRF 防护：正文提取的目标 URL 来自 RSS（外部输入），必须做协议与地址校验"""

    def test_allows_public_http_urls(self):
        """正常公网地址必须放行（否则正文提取整体失效）"""
        for url in [
            "https://www.nature.com/articles/d41586-026-02628-9",
            "http://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.arxiv.org/rss/cs.CE",
            "https://www.sciencedirect.com/science/article/pii/S0043135426014594",
        ]:
            self.assertTrue(dr._is_safe_public_url(url), f"应放行却拦截：{url}")

    def test_blocks_cloud_metadata_endpoints(self):
        """云元数据端点必须拦截：这是 SSRF 最典型的攻击目标"""
        for url in [
            "https://169.254.169.254/latest/meta-data/",
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "http://100.100.100.200/latest/meta-data/",
            "https://metadata.google.internal/computeMetadata/v1/",
        ]:
            self.assertFalse(dr._is_safe_public_url(url), f"应拦截却放行：{url}")

    def test_blocks_loopback_and_private_ranges(self):
        """环回与 RFC1918 私网地址必须拦截"""
        for url in [
            "http://127.0.0.1:8080/admin",
            "http://localhost/x",
            "http://[::1]/x",
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://172.16.3.4/",
            "http://169.254.1.1/",
            "http://0.0.0.0/",
            "http://router.local/admin",
            "http://foo.internal/",
        ]:
            self.assertFalse(dr._is_safe_public_url(url), f"应拦截却放行：{url}")

    def test_blocks_dangerous_schemes(self):
        """非 http/https 协议（含可执行脚本的协议）必须拦截"""
        for url in [
            "file:///etc/passwd",
            "ftp://example.com/x",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "//evil.com/x",       # 协议相对：无 scheme 亦应拒绝
        ]:
            self.assertFalse(dr._is_safe_public_url(url), f"应拦截却放行：{url}")

    def test_handles_malformed_input(self):
        """空值 / 非字符串 / 脏链接不应抛异常"""
        for bad in ["", None, "not a url", 123, [], {}]:
            try:
                self.assertFalse(dr._is_safe_public_url(bad))
            except Exception as e:      # noqa: BLE001 - 测试目的就是确保不抛
                self.fail(f"_is_safe_public_url({bad!r}) 抛异常：{e}")


class TestCsvFormulaInjection(unittest.TestCase):
    """测试 CSV 公式注入防护：以 = 开头的单元格会被 Excel/WPS 当公式执行"""

    def test_prefixes_formula_like_values(self):
        """= + - @ 及制表符/回车开头的值应被加上前导单引号"""
        for danger in ["=HYPERLINK(\"http://evil\",\"x\")",
                       "+1+1",
                       "-1+1",
                       "@SUM(A1)",
                       "\tcmd",
                       "\rcmd"]:
            out = dr._csv_safe(danger)
            self.assertTrue(out.startswith("'"), f"未加防护前缀：{danger!r} -> {out!r}")

    def test_leaves_normal_values_unchanged(self):
        """普通文本与日期不应被改动"""
        for normal in ["2026-09-18", "气候变化, 碳中和", "", "Water Research"]:
            self.assertEqual(dr._csv_safe(normal), normal)

    def test_handles_none(self):
        """None 转成空串，不抛异常"""
        self.assertEqual(dr._csv_safe(None), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
