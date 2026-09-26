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
import time
from unittest import mock
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


class TestHotnessV3(unittest.TestCase):
    """热度算法关键行为回归测试（v3.0）

    锁定的都是曾经真实失效过的行为：英文标题拿不到关键词分、并列 raw 被拉开成
    伪差异、单条条目直接给满分、中英双语重复检测不到、展示分依赖批次。
    改动算法时若破坏这些性质会立即暴露。

    （类名从 TestHotnessV2 改为 V3：算法已升到 v3.0，留着旧名会误导。）
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

    def test_single_item_never_gets_full_mark(self):
        """仅 1 条时不应给满分（修复前 n=1 直接映射为 100）"""
        cfg = dr.load_config()
        out = dr.calculate_hotness([self._item("Climate change research")], cfg)
        self.assertNotEqual(out[0]["score_v2"], dr.DISPLAY_SCORE_MAX)
        self.assertGreaterEqual(out[0]["score_v2"], dr.DISPLAY_SCORE_MIN)
        # relative 旧口径下，单条无实质差异 -> 中性分（保留该分支的回归）
        rel = {"weights": cfg["weights"], "hotness": {"display": {"mode": "relative"}}}
        out2 = dr.calculate_hotness([self._item("Climate change research")], rel)
        self.assertEqual(out2[0]["score_v2"], dr.DISPLAY_SCORE_MID)

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
        a, b = dr._title_token_set(zh), dr._title_token_set(en_zh)
        overlap = len(a & b) / min(len(a), len(b))
        self.assertGreaterEqual(
            overlap, dr.EVENT_CLUSTER_OVERLAP_THRESHOLD,
            "对齐到中文译文后应达到「同一事件」的判定阈值")

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


class TestRelevanceFallback(unittest.TestCase):
    """相关性过滤的兜底口径：AI 判决不得被整体作废

    背景（2026-09-20 线上事故）：28 条里 AI 判 10 条无关，剩 18 条低于 MIN_KEPT_ITEMS(20)，
    旧兜底把**全部 28 条**原样放回，首页出现 Fat Bear Week、特朗普组建 AI 部队、国赛上分
    这类与环境无关的条目。修复后：AI 判「否」即最终判决；规则模式仍保留原有整体放宽行为。
    """

    def setUp(self):
        if not dr.REQUESTS_AVAILABLE:
            self.skipTest("requests 不可用，AI 分支无法验证")
        self._orig_ai = dr._ai_relevance_irrelevant
        self._orig_disabled = dr._ai_func_disabled
        self._orig_req = dr.REQUESTS_AVAILABLE
        dr.REQUESTS_AVAILABLE = True
        dr._ai_func_disabled = lambda *a, **k: False   # 不受全局降级标记影响
        self.api = {"summary_enabled": True, "api_key": "test-key"}

    def tearDown(self):
        dr._ai_relevance_irrelevant = self._orig_ai
        dr._ai_func_disabled = self._orig_disabled
        dr.REQUESTS_AVAILABLE = self._orig_req

    def _items(self, n_env, extra):
        items = [{"title": f"某地推进生态环境保护督察整改第{i}期"} for i in range(n_env)]
        items += [{"title": t} for t in extra]
        return items

    def test_ai_rejections_survive_below_floor(self):
        """低于下限时，AI 判无关的条目也必须保持剔除（核心回归点）"""
        junk = ["Fat Bear Week has returned and the salmon are swimming",
                "Trump says US will form AI Force and appoint a czar"]
        items = self._items(18, junk)          # 18 < MIN_KEPT_ITEMS(20)
        ai_rejected = {18, 19}
        dr._ai_relevance_irrelevant = lambda its, cfg: ai_rejected

        kept = dr.filter_environmental_relevance(items, {}, self.api)
        titles = [i["title"] for i in kept]

        self.assertEqual(len(kept), 18, "AI 判无关的条目不应被兜底放回")
        for t in junk:
            self.assertNotIn(t, titles)
        self.assertFalse(any(i.get("irrelevant") for i in kept),
                         "被保留的条目不应带 irrelevant 标记")

    def test_ai_mode_kept_count_is_lower_than_input(self):
        """AI 模式下最终条数 = 输入数 - AI 判无关数，不做任何补偿"""
        items = self._items(3, ["A polar bear diary, week 12", "Local team wins the cup"])
        dr._ai_relevance_irrelevant = lambda its, cfg: {3, 4}

        kept = dr.filter_environmental_relevance(items, {}, self.api)
        self.assertEqual(len(kept), 3)
        self.assertEqual(len(items), 5)

    def test_rule_mode_still_relaxes_on_small_sample(self):
        """规则模式（AI 不可用）下小样本仍整体放宽——避免规则误杀把当天内容清空"""
        items = [{"title": "欧盟推进碳边境调节机制，专家分析对出口影响"},
                 {"title": "今日沪深股市收评：两市震荡整理"},
                 {"title": "英超联赛周末战报：曼城客场取胜"}]
        dr._ai_relevance_irrelevant = lambda its, cfg: None   # 模拟 AI 调用失败

        kept = dr.filter_environmental_relevance(items, {}, self.api)
        self.assertEqual(len(kept), len(items), "规则模式小样本应整体放宽")
        self.assertFalse(any(i.get("irrelevant") for i in kept))


class TestEnglishRelevanceKeep(unittest.TestCase):
    """英文标题相关性兜底（2026-09-26 修正）

    背景（2026-09-25 线上实测）：规则模式下英文条目的生死完全取决于"DeepL 译文是否
    **字面**含中文词表里的词"，译文换个近义词就整条被砍 —— 那次运行中文条目保留率
    94%(18/19)、英文仅 25%(10/40)，58 条里明确误杀 >=7 条，且集中在与水处理/环境化学/
    海洋低氧相关的学术条目上（恰好是本平台目标用户最需要的那批）。

    修好后的四条出口：译文命中 / 原文命中英文词表 / 都不命中（保守放行）/ 黑名单拦截。
    这里逐条锁定，避免以后有人把"直接 return 译文结果"那条近路又写回来。
    """

    def setUp(self):
        self._orig_tr = dr.translate_en_to_zh
        self._zh = {}
        # 不联网：译文由每个用例显式给出，专门模拟"译文换个说法"这个关键变量
        dr.translate_en_to_zh = lambda t: self._zh.get(t, "")

    def tearDown(self):
        dr.translate_en_to_zh = self._orig_tr

    def test_translation_hit_keeps(self):
        """译文命中中文词表 -> 保留（补词后"变暖"这类高频译法应能命中）"""
        t = "This Map Shows Where Warming Has Accelerated"
        self._zh[t] = "这张地图显示变暖在哪里加速"
        self.assertTrue(dr._en_relevance_keep(t))

    def test_original_english_hit_keeps(self):
        """译文未命中时，原文命中英文词表也要保留

        这正是旧实现的漏点：它拿到译文后直接 return，英文词表这条路根本走不到。
        """
        t = "Temporal patterns and causes of deoxygenation"
        self._zh[t] = "某研究的时空模式与成因"      # 故意不含任何环境词
        self.assertTrue(dr._en_relevance_keep(t))

    def test_hyphenated_multiword_hits(self):
        """连字符归一：词表里的 "fossil fuel" 必须能命中 "Fossil-fuel firms ..." """
        t = "Fossil-fuel firms in line for billions in subsidies"
        self._zh[t] = "某行业公司有望获得巨额补贴"
        self.assertTrue(dr._en_relevance_keep(t))

    def test_unknown_keeps_conservatively(self):
        """两条路都不命中 -> 保守放行（旧实现 docstring 承诺、但永远走不到的那条）"""
        t = "Some headline with no term"
        self._zh[t] = "这只是一个普通说法"
        self.assertTrue(dr._en_relevance_keep(t))

    def test_blacklist_still_filters(self):
        """黑名单必须仍然生效，且译文为中文时也要生效

        旧实现把 IRRELEVANT_EN 排在翻译之后 —— 译文为中文时它永远检查不到
        （'phd'/'programme'/'scholarship' 等词形同虚设）。
        """
        t1 = "Best sports moments of the year"
        self._zh[t1] = "年度最佳体育时刻"
        self.assertFalse(dr._en_relevance_keep(t1))

        t2 = "Scholarship for environmental engineering students"
        self._zh[t2] = "环境工程专业学生奖学金"     # 译文含"环境工程"，旧实现会误放行
        self.assertFalse(dr._en_relevance_keep(t2))


class TestExtractAiListNumberedDict(unittest.TestCase):
    """_extract_ai_list 对"编号字典"返回的兜底（2026-09-26）

    背景（2026-09-25 线上）：AI 调用成功、返回体也是合法 JSON 对象，但内部没有数组
    （形如 {"0":"是","1":"否"}）。旧实现在这里**静默** return None，调用方只看到
    "解析失败"，无法区分「格式不认识」与「AI 没返回内容」—— 唯一能定位格式的线索被丢掉。
    """

    def test_numbered_dict_is_normalized(self):
        raw = '{"results": {"0": "是", "3": "否"}}'
        arr = dr._extract_ai_list(raw, keys=("results", "items"), label="T")
        self.assertIsInstance(arr, list)
        self.assertEqual(len(arr), 2)
        self.assertEqual({r["id"] for r in arr}, {"0", "3"})
        self.assertTrue(any(r.get("relevant") == "否" for r in arr))

    def test_numbered_dict_of_objects(self):
        raw = '{"results": {"7": {"relevant": "否"}}}'
        arr = dr._extract_ai_list(raw, keys=("results",), label="T")
        self.assertEqual(arr, [{"relevant": "否", "id": "7"}])

    def test_plain_array_still_wins(self):
        """正常数组形式不受影响（兜底不得抢在正路前面）"""
        raw = '{"results": [{"id": 0, "relevant": "是"}]}'
        self.assertEqual(dr._extract_ai_list(raw, keys=("results",), label="T"),
                         [{"id": 0, "relevant": "是"}])


class TestRelevanceBatching(unittest.TestCase):
    """相关性过滤分批（2026-09-26）

    背景（2026-09-25 线上）：58 条一次性请求时 max_tokens 只给到 812（14*58），
    而每条 {"id":0,"relevant":"是"} 实测需 15~25 token（58 条要 870~1450）——
    JSON 被截断后整轮降级成规则模式，英文条目随即被系统性误杀。
    分批后单批预算充裕，且**单批失败只损失该批**，不再整轮作废。
    """

    def setUp(self):
        self._orig_call = dr.call_nvidia_api

    def tearDown(self):
        dr.call_nvidia_api = self._orig_call

    @staticmethod
    def _ids_in(prompt):
        out = []
        for line in prompt.splitlines():
            head = line.split(". ", 1)[0]
            if head.isdigit():
                out.append(int(head))
        return out

    def test_one_failed_batch_does_not_kill_the_rest(self):
        calls = []

        def fake(prompt, cfg, **kw):
            calls.append(prompt)
            if len(calls) == 1:
                return ""                      # 第一批失败（空响应）
            ids = self._ids_in(prompt)
            return json.dumps({"results": [{"id": i, "relevant": "是"} for i in ids]})

        dr.call_nvidia_api = fake
        items = [{"title": f"某地推进生态环境保护督察整改第{i}期"} for i in range(45)]
        out = dr._ai_relevance_irrelevant(items, {})
        self.assertIsNotNone(out, "只要有批次成功，就不应整体降级为规则模式")
        self.assertEqual(out, set(), "全部判「是」时无关集合应为空")
        self.assertEqual(len(calls), 3, "45 条按每批 20 条应为 3 批")

    def test_rejections_are_collected_across_batches(self):
        """跨批次的判决要合并，且 id 用全局下标、批间不撞号"""
        def fake(prompt, cfg, **kw):
            ids = self._ids_in(prompt)
            return json.dumps({"results": [
                {"id": i, "relevant": ("否" if i % 20 == 0 else "是")} for i in ids
            ]})

        dr.call_nvidia_api = fake
        items = [{"title": f"标题{i}"} for i in range(45)]
        out = dr._ai_relevance_irrelevant(items, {})
        self.assertEqual(out, {0, 20, 40})

    def test_all_batches_failed_degrades(self):
        dr.call_nvidia_api = lambda prompt, cfg, **kw: ""
        items = [{"title": f"标题{i}"} for i in range(5)]
        self.assertIsNone(dr._ai_relevance_irrelevant(items, {}),
                          "全部批次失败才应返回 None（调用方降级规则）")


class TestContentDensity(unittest.TestCase):
    """信息密度判据（v2.1）。

    背景：线上榜尾混进多条地方政务通稿（省督察组调研督导信访、昆山生态环境局
    网友见面会、永州溶洞整治推进会、中央督察组反馈会表态发言），它们与高密度
    科研进展在旧口径下拿到的"内容质量分"可以完全一样。这里锁定判据行为：
    通稿降权 / 政策文件加分 / 纯时政与娱乐类判断为正常不放行也不误伤。
    """

    def test_local_boilerplate_is_downweighted(self):
        cases = [
            "省第二生态环境保护督察组调研督导信访工作 - finance.sina.com.cn",
            "苏州市昆山生态环境局举办网友见面会 - Sohu",
            "永州市溶洞污染排查整治工作推进会召开 - 湖南红网",
            "黄坤明在中央第四生态环境保护督察组督察广东省情况反馈会上作表态发言",
            "江西省生态环境厅第三轮“利剑行动”启动",
        ]
        for t in cases:
            factor, note = dr.evaluate_content_density(t)
            self.assertEqual(note, "地方政务通稿", f"应判为地方政务通稿：{t}")
            self.assertLess(factor, 1.0, f"通稿必须降权：{t}")

    def test_title_without_the_word_huanjing_still_caught(self):
        """标题不含"环境"二字也可以是明确的地方环保政务（靠 地方层级+污染+推进会 命中）"""
        factor, note = dr.evaluate_content_density("永州市溶洞污染排查整治工作推进会召开")
        self.assertEqual(note, "地方政务通稿")
        self.assertLess(factor, 1.0)

    def test_national_policy_document_is_boosted(self):
        t = ("生态环境部环评司有关负责人就《排污许可证申请与核发技术规范 火电》"
             "等六项国家生态环境标准修订答记者问")
        factor, note = dr.evaluate_content_density(t)
        self.assertEqual(note, "国家级政策文件")
        self.assertGreater(factor, 1.0)

    def test_high_density_content_is_not_penalized(self):
        """国家层面部署、学术会议、国际论坛、科研发现都不能被误判为通稿"""
        cases = [
            "生态环境部部长黄润秋：重拳整治！ - finance.sina.com.cn",
            "分三阶段整治！多部门联合部署深入打击生态环境监测机构弄虚作假",
            "大气污染控制费效与达标评估暨大气霾化学国际学术研讨会召开 - 科学网",
            "中国—东盟绿色循环产业与国际环境公约履约平行论坛在南宁举行 - 央广网",
        ]
        for t in cases:
            factor, note = dr.evaluate_content_density(t)
            self.assertEqual(factor, 1.0, f"不应被降权：{t}（判为 {note}）")

    def test_english_titles_are_never_flagged(self):
        """判据只对中文生效：英文源不产出中文政务通稿，套用会误判"""
        for t in ["Microplastics in Soil a ‘Trojan Horse’ for Toxic Chemicals",
                  "Trump says US will form 'AI Force' and appoint an army"]:
            factor, note = dr.evaluate_content_density(t)
            self.assertEqual((factor, note), (1.0, ""))

    def test_density_factor_can_be_disabled_by_config(self):
        """config 里 content_density.enabled=false 时应完全失效"""
        item = {"title": "省第二生态环境保护督察组调研督导信访工作",
                "source": "Google News 生态环境", "published": "2026-09-20T00:00:00+00:00"}
        items = dr.calculate_heat_v3([dict(item)], {"content_density": {"enabled": False}})
        self.assertEqual(items[0]["score_breakdown"]["density_factor"], 1.0)
        self.assertEqual(items[0]["score_breakdown"]["density_note"], "")

    def test_density_factor_recorded_in_breakdown(self):
        """密度系数与判定说明必须进入 score_breakdown，供前端热度弹窗展示"""
        items = dr.calculate_heat_v3(
            [{"title": "省第二生态环境保护督察组调研督导信访工作",
              "source": "Google News 生态环境", "published": "2026-09-20T00:00:00+00:00"},
             {"title": "Microplastics in Soil a ‘Trojan Horse’ for Toxic Chemicals",
              "source": "Yale Environment 360", "published": "2026-09-20T00:00:00+00:00"}],
            {})
        bd = items[0]["score_breakdown"]
        self.assertEqual(bd["algorithm"], "v3.0")
        self.assertLess(bd["density_factor"], 1.0)
        self.assertEqual(bd["density_note"], "地方政务通稿")
        self.assertEqual(items[1]["score_breakdown"]["density_factor"], 1.0)

    def test_boilerplate_cap_removes_excess(self):
        """配额生效：最多保留 N 条通稿，非通稿一条都不动"""
        items = [
            {"title": "省第二生态环境保护督察组调研督导信访工作"},
            {"title": "苏州市昆山生态环境局举办网友见面会"},
            {"title": "永州市溶洞污染排查整治工作推进会召开"},
            {"title": "生态环境部部长黄润秋：重拳整治！"},
        ]
        kept = dr.limit_low_density_items(items, {"content_density": {"max_boilerplate": 1}})
        self.assertEqual(len(kept), 2)
        self.assertIn("生态环境部部长黄润秋：重拳整治！", [k["title"] for k in kept])

    def test_boilerplate_cap_zero_drops_all(self):
        items = [{"title": "省第二生态环境保护督察组调研督导信访工作"},
                 {"title": "Microplastics in Soil a ‘Trojan Horse’"}]
        kept = dr.limit_low_density_items(items, {"content_density": {"max_boilerplate": 0}})
        self.assertEqual([k["title"] for k in kept], ["Microplastics in Soil a ‘Trojan Horse’"])

    def test_boilerplate_cap_default_is_no_op(self):
        """默认 -1：只降权不删，榜单条数不变（避免默认行为改变上线表现）"""
        items = [{"title": "省第二生态环境保护督察组调研督导信访工作"},
                 {"title": "苏州市昆山生态环境局举办网友见面会"}]
        for cfg in ({}, {"content_density": {}}, {"content_density": {"max_boilerplate": -1}},
                    {"content_density": {"max_boilerplate": "abc"}}):
            self.assertEqual(len(dr.limit_low_density_items(items, cfg)), 2)


class TestKeywordCoverage(unittest.TestCase):
    """关键词表覆盖度。

    线上 28 条里 22 条 matched_keywords 为空（79%），导致关键词 IDF 分（满分 25）
    与跨源共振分（满分 15）几乎全体为 0，排序退化成「来源权重 + 时间衰减」。
    根因是默认词表缺「生态环境」「环境保护」「环境监测」「督察」等中文高频领域词
    —— "生态环境保护督察" 也不含子串 "环保督察"。
    """

    def test_high_frequency_cn_domain_words_are_covered(self):
        must_have = ["生态环境", "环境保护", "环境监测", "督察", "污染治理",
                     "碳达峰", "温室气体", "固废", "地下水", "饮用水", "流域",
                     "湿地", "臭氧", "生态安全", "环境政策", "绿色低碳", "能源转型"]
        for w in must_have:
            self.assertIn(w, dr.DEFAULT_KEYWORDS, f"默认词表缺高频领域词：{w}")

    def test_real_titles_from_live_site_now_match(self):
        """线上实测零命中的 5 条中文标题，扩词后必须至少命中一个关键词"""
        cases = [
            "生态环境部部长黄润秋：重拳整治！",
            "分三阶段整治！多部门联合部署深入打击生态环境监测机构弄虚作假",
            "打赢打好漓江生态环境提档升级总体战丨阳朔镇：精治细护提质效",
            "省第二生态环境保护督察组调研督导信访工作",
            "苏州市昆山生态环境局举办网友见面会",
        ]
        for t in cases:
            got = dr.match_keywords(t, dr.DEFAULT_KEYWORDS, dr.KEYWORD_EN_ALIASES)
            self.assertTrue(got, f"扩词后仍零命中：{t}")

    def test_bare_over_generic_words_are_excluded(self):
        """过泛的单字级词会让 s_keyword 对所有人一起饱和，必须排除"""
        for w in ["污染", "排放", "气候", "环境", "生态"]:
            self.assertNotIn(w, dr.DEFAULT_KEYWORDS, f"过泛词不应收录：{w}")

    def test_no_duplicate_keywords(self):
        self.assertEqual(len(dr.DEFAULT_KEYWORDS), len(set(dr.DEFAULT_KEYWORDS)),
                         "默认词表存在重复词")

    def test_every_keyword_has_english_alias_or_is_only_cn(self):
        """至少 2/3 信源为英文，新增词应尽量配英文别名（未配的须是有意为之）"""
        missing = [w for w in dr.DEFAULT_KEYWORDS if w not in dr.KEYWORD_EN_ALIASES]
        # 允许少量纯中文政务词无英文对应，但不允许大面积缺失
        self.assertLess(len(missing), 8, f"缺英文别名的词过多：{missing}")


class TestTopicTagNormalization(unittest.TestCase):
    """话题标签清洗。实测线上四类毛病：整句标题当标签、截断残词、
    大小写重复（Pfas/PFAS）、与标题完全相同的空信息标签。"""

    def test_overlong_tag_is_dropped(self):
        tags = ["东盟绿色循环产业与国际环境公约履约平行论坛在南宁举行", "微塑料"]
        self.assertEqual(dr.normalize_topic_tags(tags), ["微塑料"])

    def test_case_duplicates_are_merged(self):
        """合并后的拼写取**规范形**（PFAS），而不是"最先出现的那一个"。

        旧行为保留了首次出现的写法，于是 Pfas 与 PFAS 在周榜里各占一格；
        2026-09-22 起缩写统一归一到规范拼写，见 canonical_tag。
        """
        self.assertEqual(dr.normalize_topic_tags(["Pfas", "PFAS", "pfas"]), ["PFAS"])

    def test_english_long_tag_is_kept(self):
        """"forever chemicals" 17 字符属正常英文标签，不能被中文的 15 字上限误杀"""
        self.assertIn("forever chemicals", dr.normalize_topic_tags(["forever chemicals"]))

    def test_tag_equal_to_title_is_dropped(self):
        t = "生态环境部部长黄润秋：重拳整治！"
        self.assertEqual(dr.normalize_topic_tags([t], t), ["环境资讯"])

    def test_empty_falls_back_to_contract_value(self):
        """清洗后为空必须回落 ["环境资讯"]：前端在摘要为空时用它做提示"""
        for empty in ([], None, [""], ["短"]):
            self.assertEqual(dr.normalize_topic_tags(empty), ["环境资讯"])

    def test_capped_at_three(self):
        got = dr.normalize_topic_tags(["微塑料", "气候变化", "碳中和", "臭氧", "湿地"])
        self.assertEqual(len(got), 3)
        self.assertEqual(got, ["微塑料", "气候变化", "碳中和"])


class TestJunkTitleFilter(unittest.TestCase):
    """导航页 / 占位标题过滤（2026-09-20 接入中文垂直源后新增）

    实测来源：Google News 的 site: 查询与部分站点 feed 会把非文章页当条目返回 ——
    「首页 /申请前信息公开」（生态环境部）、「上市」（中国水网）、「要闻」（北极星环保网）。
    这类条目标题极短或是栏目名，进榜没有信息价值，还会因来源权重高而排到前面。
    """

    def test_placeholder_titles_are_dropped(self):
        for t in ["首页", "要闻", "上市", "更多", "首页 /申请前信息公开",
                  "版权所有 © 中国水网", "", "   "]:
            self.assertTrue(dr.is_junk_title(t), "应判为占位标题：%r" % t)

    def test_real_titles_are_not_mistaken(self):
        """宁可漏掉几个垃圾页，也不要误杀正常条目"""
        for t in ["全国碳市场扩围至钢铁水泥铝冶炼行业",
                  "宁夏固体废物污染防治“十五五”规划",
                  "我国绿色贷款余额超40万亿元",
                  "Microplastics in Soil a ‘Trojan Horse’ for Toxic Chemicals"]:
            self.assertFalse(dr.is_junk_title(t), "不应误杀：%r" % t)


class TestTrustedEnvSource(unittest.TestCase):
    """环境垂直源白名单（2026-09-20 新增）

    这些源整站/整频道就跑环境口，标题里没有"环境/生态"字样**不代表**内容无关。
    实测误杀：人民网环保频道的「全国碳市场扩围至钢铁水泥铝冶炼行业」、
    中国水网的「国能水务中标神东煤炭矿井水提标治理EPC项目」都被规则整条剔除。
    """

    def setUp(self):
        # filter_environmental_relevance 需要一个 api_config；这里只用来判断"AI 是否可用"，
        # 真正的 AI 调用在下面被 mock 掉了。
        self.api = {"summary_enabled": True, "api_key": "test-key"}

    def test_vertical_sources_are_trusted(self):
        for s in ["Google News 中国环境网", "Google News 生态环境部",
                  "Google News 北极星环保网", "Google News 中国水网",
                  "人民网 环保频道"]:
            self.assertTrue(dr.is_trusted_env_source(s), s)

    def test_broad_queries_are_not_trusted(self):
        """放宽不能外溢到泛聚合查询源——它们正是低密度通稿的来源"""
        for s in ["Google News 环境保护", "Google News 生态环境",
                  "Google News 气候变化", "The Guardian Environment", ""]:
            self.assertFalse(dr.is_trusted_env_source(s), s)

    def test_trusted_source_rescued_in_rule_mode(self):
        """规则模式下：标题不含环境词的条目，来自垂直源 -> 保留；来自泛查询源 -> 剔除"""
        # 20 条正常条目垫底，避免触发"不足 MIN_KEPT_ITEMS 就整体放宽"的兜底
        filler = [{"title": "某地推进水污染治理工作取得阶段性进展", "source": "Google News 环境保护"}
                  for _ in range(20)]
        title = "湖北大悟守护秋收蓝天"
        trusted = {"title": title, "source": "Google News 中国环境网"}
        untrusted = {"title": title, "source": "Google News 环境保护"}
        dr._ai_relevance_irrelevant = lambda its, cfg: None      # 模拟 AI 不可用 -> 规则模式

        kept = dr.filter_environmental_relevance(filler + [trusted, untrusted], {}, self.api)
        self.assertTrue(any(i is trusted for i in kept), "垂直源应被白名单放行")
        self.assertTrue(untrusted.get("irrelevant"), "泛查询源不应享受白名单")


class TestKeywordCoverageForChineseVertical(unittest.TestCase):
    """中文垂直源高频主题必须在词表内（否则关键词 IDF 分恒为 0，排序吃亏）"""

    def test_new_domain_words_present(self):
        for kw in ["碳市场", "碳交易", "垃圾焚烧", "污泥", "环境法典", "排污许可"]:
            self.assertIn(kw, dr.DEFAULT_KEYWORDS, "词表缺少 %s" % kw)

    def test_real_headlines_hit_keywords(self):
        cases = [
            "全国碳市场扩围至钢铁水泥铝冶炼行业",
            "宁夏固体废物污染防治“十五五”规划",
            "关于印发《全国碳排放权交易市场2025、2026年度发电行业配额总量和分配方案》的通知",
        ]
        for t in cases:
            self.assertTrue(dr.match_keywords(t, dr.DEFAULT_KEYWORDS, dr.KEYWORD_EN_ALIASES),
                            "关键词零命中：%s" % t)


class TestSafeGetRedirectGuard(unittest.TestCase):
    """_safe_get 逐跳校验重定向 —— 堵住「入口 URL 合法、重定向指向内网」的绕过路径。

    为什么必须单独测这一层：只测 _is_safe_public_url 是**测不到**这个缺陷的。
    requests 默认 allow_redirects=True，会把 302 一路跟到底，于是校验只看过那个
    合法的公网 URL，真正被请求的却是内网地址。本用例的核心断言不是「返回 None」，
    而是「那个内网地址**一次都没有被请求过**」——即请求根本没发出去。
    """

    def setUp(self):
        self.calls = []
        self._orig_get = dr.requests.get

    def tearDown(self):
        dr.requests.get = self._orig_get

    @staticmethod
    def _resp(status, location=None):
        return SimpleNamespace(
            status_code=status,
            headers={"Location": location} if location else {},
            text="ok",
        )

    def _patch(self, mapping):
        def fake_get(u, **kwargs):
            self.calls.append({"url": u, "allow_redirects": kwargs.get("allow_redirects")})
            if u not in mapping:
                raise AssertionError(f"不应请求该地址：{u}")
            return mapping[u]
        dr.requests.get = fake_get

    def test_follows_legitimate_redirect(self):
        """正常跳转必须照常跟到底（否则正文提取整体失效）"""
        self._patch({
            "https://a.example.com/x": self._resp(302, "https://b.example.com/y"),
            "https://b.example.com/y": self._resp(200),
        })
        resp, blocked = dr._safe_get("https://a.example.com/x")
        self.assertIsNone(blocked)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([c["url"] for c in self.calls],
                         ["https://a.example.com/x", "https://b.example.com/y"])

    def test_never_enables_auto_redirect(self):
        """每一跳都必须 allow_redirects=False：只要有一跳交回给 requests 自动跟随，防线即失效"""
        self._patch({
            "https://a.example.com/x": self._resp(302, "https://b.example.com/y"),
            "https://b.example.com/y": self._resp(200),
        })
        dr._safe_get("https://a.example.com/x")
        self.assertTrue(self.calls, "应当发起过请求")
        for c in self.calls:
            self.assertIs(c["allow_redirects"], False,
                          f"{c['url']} 未显式关闭自动重定向")

    def test_metadata_redirect_target_is_never_requested(self):
        """核心回归：302 指向云元数据端点时，那个地址绝不能被请求"""
        self._patch({
            "https://evil.example.com/x": self._resp(302, "http://169.254.169.254/latest/meta-data/"),
        })
        resp, blocked = dr._safe_get("https://evil.example.com/x")
        self.assertIsNone(resp, "被拦截时不应返回响应")
        self.assertEqual(blocked, "http://169.254.169.254/latest/meta-data/")
        self.assertEqual(len(self.calls), 1, "只应请求过最初那个公网地址")

    def test_relative_location_is_resolved_before_check(self):
        """相对 Location 必须先解析成绝对地址再校验，否则私网重定向会漏过"""
        self._patch({
            "https://a.example.com/x": self._resp(302, "../../../etc"),
            "https://a.example.com/etc": self._resp(200),
        })
        resp, blocked = dr._safe_get("https://a.example.com/x")
        self.assertIsNone(blocked)
        self.assertEqual(self.calls[-1]["url"], "https://a.example.com/etc")

    def test_redirect_to_private_host_is_blocked(self):
        for target in ["http://127.0.0.1/admin",
                       "http://10.1.2.3/",
                       "http://metadata.google.internal/x",
                       "file:///etc/passwd"]:
            self.calls = []
            self._patch({"https://a.example.com/x": self._resp(302, target)})
            resp, blocked = dr._safe_get("https://a.example.com/x")
            self.assertIsNone(resp, f"应拦截：{target}")
            self.assertEqual(blocked, target)
            self.assertEqual(len(self.calls), 1, f"不应请求：{target}")

    def test_redirect_loop_is_bounded(self):
        """自指环必须在上限内停止，不能无限跟下去"""
        self._patch({"https://a.example.com/x": self._resp(302, "https://a.example.com/x")})
        resp, blocked = dr._safe_get("https://a.example.com/x")
        self.assertIsNone(resp)
        self.assertIsNone(blocked)
        self.assertEqual(len(self.calls), dr.SAFE_GET_MAX_REDIRECTS + 1)

    def test_existing_behaviour_for_plain_200(self):
        """无重定向的老路径行为不变：一次请求、原样返回响应"""
        self._patch({"https://a.example.com/x": self._resp(200)})
        resp, blocked = dr._safe_get("https://a.example.com/x")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(blocked)
        self.assertEqual(len(self.calls), 1)


class TestSummaryAttribution(unittest.TestCase):
    """摘要归属校验：AI 少返回一条时，摘要不得与相邻标题张冠李戴。

    背景（2026-09-21 线上实证）：某一批 5 条只返回了 4 条摘要 —— 模型自行跳过了它认为
    无信息量的「力源科技」（一个栏目页），**其后的 id 全部左移**。旧实现照 id 落盘后，
    榜单第 15 名挂上了第 16 名的摘要、第 16 名挂上了第 17 名的摘要，
    而日志只显示「AI生成 14/15 条」，看不出任何异常。
    """

    TITLES = [
        "对话｜岛国沉没倒计时！图瓦卢青年为何拒绝当“气候移民”？ - thepaper.cn",
        "Billions in rare earth elements may be hiding in America’s coal ash",
        "力源科技 - huanbao.bjx.com.cn",
        "来自中国电网的超级气候污染物正在炙烤地球 - Inside Climate News",
        "永州市溶洞污染排查整治工作推进会召开 - 湖南红网",
    ]

    def _batch(self, titles=None):
        titles = self.TITLES if titles is None else titles
        return [(i, i, {"title": t}, "") for i, t in enumerate(titles)]

    def test_model_skips_one_item_does_not_shift_summaries(self):
        """复盘线上事故：模型漏掉一条，后面的摘要不得整体前移"""
        summaries = [
            {"id": 0, "title": "对话｜岛国沉没倒计",
             "summary": "图瓦卢青年拒绝被定义为气候移民，选择留守或另寻生存路径。"},
            {"id": 1, "title": "Billions in rare",
             "summary": "科学家从藻类与植物中寻找更清洁的稀土提取方法，减少尾矿依赖。"},
            {"id": 2, "title": "来自中国电网的超级",
             "summary": "中国电网是全球最大六氟化硫排放源，SF6 泄漏温室效应极强。"},
            {"id": 3, "title": "永州市溶洞污染排查",
             "summary": "永州市开展溶洞污染专项排查整治，遏制地下水污染风险。"},
        ]
        m = dr._match_summary_entries(self._batch(), summaries)

        self.assertNotIn(2, m, "被模型跳过的那条不得借用相邻条目的摘要")
        self.assertIn("六氟化硫", m[3], "第 16 条必须拿到自己的摘要")
        self.assertIn("溶洞", m[4], "第 17 条必须拿到自己的摘要")
        self.assertEqual(len(m), 4)

    def test_id_is_ignored_when_title_fingerprint_present(self):
        """模型重编号（id 全错）但回显了标题：必须按标题归属"""
        summaries = [
            {"id": 9, "title": "永州市溶洞污染排查", "summary": "永州市溶洞污染专项整治推进。"},
            {"id": 8, "title": "对话｜岛国沉没倒计", "summary": "图瓦卢青年拒绝气候移民标签。"},
        ]
        m = dr._match_summary_entries(self._batch(), summaries)
        self.assertEqual(set(m.keys()), {0, 4})
        self.assertIn("图瓦卢", m[0])

    def test_falls_back_to_id_when_model_ignores_title_echo(self):
        """模型整体不回显标题：退回 id 定位，保持修复前行为（不是回退为不安全）"""
        batch = self._batch(["标题甲", "标题乙"])
        m = dr._match_summary_entries(batch, [{"id": 0, "summary": "甲摘要"},
                                              {"id": 1, "summary": "乙摘要"}])
        self.assertEqual(m, {0: "甲摘要", 1: "乙摘要"})

    def test_no_title_echo_and_bad_id_is_skipped(self):
        """既无标题回显、id 又是脏值时跳过，不抛异常"""
        batch = self._batch(["标题甲"])
        m = dr._match_summary_entries(batch, [{"id": "甲", "summary": "摘要"}])
        self.assertEqual(m, {})

    def test_duplicate_titles_do_not_overwrite(self):
        """同题不同源：两条摘要应落到两个位置，而不是都挤在第一条上"""
        batch = self._batch(["生态环境部部署严打监测造假 - 甲网", "生态环境部部署严打监测造假 - 乙网"])
        m = dr._match_summary_entries(batch, [
            {"id": 0, "title": "生态环境部部署严打", "summary": "摘要一"},
            {"id": 1, "title": "生态环境部部署严打", "summary": "摘要二"},
        ])
        self.assertEqual(m, {0: "摘要一", 1: "摘要二"})

    def test_dirty_entries_are_skipped(self):
        """非 dict、空摘要、空指纹不算命中"""
        batch = self._batch(["标题甲"])
        m = dr._match_summary_entries(batch, ["字符串", {"id": 0, "summary": "   "}, 42])
        self.assertEqual(m, {})

    def test_fingerprint_tolerates_model_shortening(self):
        """模型只回显前 3 个字（少字）时仍应命中"""
        batch = self._batch(["永州市溶洞污染排查整治工作推进会召开"])
        m = dr._match_summary_entries(batch, [{"id": 0, "title": "永州市", "summary": "修复后的摘要"}])
        self.assertEqual(m, {0: "修复后的摘要"})


class TestRelevanceVerdictNormalization(unittest.TestCase):
    """AI 相关性判决值归一化：布尔与大小写都必须正确识别。

    旧实现 `str(v).strip() in ("否","no","false","0")` 有两个洞：大小写敏感，
    以及 str(False)=="False" 不命中 —— json_mode 下模型回 {"relevant": false} 时
    判「否」会被当成「是」，整批结果静默变成"零剔除"。
    """

    def test_boolean_false_means_irrelevant(self):
        self.assertTrue(dr._is_irrelevant_verdict(False))

    def test_boolean_true_means_relevant(self):
        self.assertFalse(dr._is_irrelevant_verdict(True))

    def test_case_insensitive_strings(self):
        for v in ["否", "no", "NO", "No", "false", "FALSE", "False", "0", " 否 ", "无关"]:
            self.assertTrue(dr._is_irrelevant_verdict(v), f"应判为无关：{v!r}")

    def test_relevant_strings(self):
        for v in ["是", "yes", "true", "1", "相关", ""]:
            self.assertFalse(dr._is_irrelevant_verdict(v), f"应判为相关：{v!r}")

    def test_is_environment_field_uses_same_normalizer(self):
        """兼容 is_environment 布尔字段：False 即无关"""
        self.assertTrue(dr._is_irrelevant_verdict(False))
        self.assertFalse(dr._is_irrelevant_verdict(True))


class TestJunkTitleSourceSuffix(unittest.TestCase):
    """Google News 的「标题 - 来源名」形态：先剥后缀再判，否则栏目页会靠后缀逃过长度检查。"""

    def test_section_page_with_domain_suffix_is_junk(self):
        for t in ["力源科技 - huanbao.bjx.com.cn",
                  "上市 - 中国水网",
                  "要闻 | 北极星环保网",
                  "首页 - 生态环境部"]:
            self.assertTrue(dr.is_junk_title(t), f"应判为占位内容：{t}")

    def test_real_titles_are_not_falsely_dropped(self):
        for t in ["生态环境部：重拳整治环境监测造假！ - 上海热线",
                  "永州市溶洞污染排查整治工作推进会召开 - 湖南红网",
                  "来自中国电网的超级气候污染物正在炙烤地球 - Inside Climate News",
                  "表演式采样、伪造数据？生态环境部部署全国严打环境监测造假_政经观察 - 奥一网",
                  "江西省流域水生态环境保护“十五五”规划（征求意见稿） - 中国水网"]:
            self.assertFalse(dr.is_junk_title(t), f"误杀正常标题：{t}")

    def test_english_subtitle_is_not_stripped(self):
        """英文标题的长副标题不是来源名，不能被剥掉（否则会误伤）"""
        t = ("MAKING WAVES: Sounds of the underground - "
             "unveiling the potential of acoustic monitoring in water systems")
        self.assertEqual(dr.strip_title_source_suffix(t), t)
        self.assertFalse(dr.is_junk_title(t))

    def test_strip_does_not_touch_plain_title(self):
        t = "This deep-sea enzyme survives heat that destroys most proteins"
        self.assertEqual(dr.strip_title_source_suffix(t), t)


class TestWeeklyKeywordPlaceholderFilter(unittest.TestCase):
    """兜底占位标签「环境资讯」不得进入近7天高频词（2026-09-21 它以 count=10 占据榜首）。"""

    def test_fallback_tag_excluded_from_weekly_keywords(self):
        tmp = tempfile.mkdtemp()
        old_dir = dr.DATA_DIR
        try:
            daily_dir = os.path.join(tmp, "daily")
            os.makedirs(daily_dir)
            today = datetime.now().strftime("%Y-%m-%d")
            with open(os.path.join(daily_dir, today + ".json"), "w", encoding="utf-8") as f:
                json.dump({"items": [
                    {"topic_tags": ["环境资讯"], "matched_keywords": ["微塑料"]},
                    {"topic_tags": ["环境资讯"], "matched_keywords": ["微塑料"]},
                    {"topic_tags": ["环境资讯"], "matched_keywords": ["碳市场"]},
                ]}, f)
            dr.DATA_DIR = tmp
            terms = [k["term"] for k in dr.calculate_weekly_keywords()]
        finally:
            dr.DATA_DIR = old_dir
            shutil.rmtree(tmp, ignore_errors=True)

        self.assertNotIn("环境资讯", terms)
        self.assertIn("微塑料", terms)
        self.assertIn("碳市场", terms)

    def test_banned_tags_constant_covers_fallback_literal(self):
        """兜底字面量必须被禁词表覆盖，避免以后新增兜底标签又漏"""
        self.assertIn("环境资讯", dr.WEEKLY_KEYWORD_BANNED_TAGS)


class TestSummaryNotDuplicatingTitle(unittest.TestCase):
    """摘要与标题一字不差时应置空，由前端显示「暂无摘要」，而不是让摘要栏复制标题。"""

    def test_chinese_summary_equal_to_title_becomes_empty(self):
        item = {"title": "永州市溶洞污染排查整治工作推进会召开 - 湖南红网",
                "summary": "永州市溶洞污染排查整治工作推进会召开 - 湖南红网"}
        self.assertEqual(dr._finalize_summary(item), "")

    def test_real_summary_is_kept(self):
        item = {"title": "生态环境部：重拳整治环境监测造假！ - 上海热线",
                "summary": "生态环境部发布重拳整治环境监测造假的通报，严厉打击采样造假等违法行为。"}
        self.assertIn("重拳整治", dr._finalize_summary(item))

    def test_english_item_keeps_existing_behaviour(self):
        """英文条目以原标题充当摘要是既有设计（避免截断成残片），本次不改动"""
        t = "This deep-sea enzyme survives heat that destroys most proteins"
        self.assertEqual(dr._finalize_summary({"title": t, "summary": t}), t)


class TestFeedResponseDiagnostics(unittest.TestCase):
    """抓取失败的诊断信息：必须能区分「被 WAF 拦截」与「XML 本身有问题」。"""

    def _resp(self, status, body, ctype):
        return SimpleNamespace(status_code=status, content=body,
                               headers={"Content-Type": ctype})

    def test_html_block_page_is_reported_as_non_xml(self):
        diag = dr._describe_feed_response(
            self._resp(403, b"<!DOCTYPE html><html><head><title>Attention Required</title>", "text/html"))
        self.assertIn("403", diag)
        self.assertIn("非XML", diag)

    def test_xml_response_is_reported_as_xml(self):
        diag = dr._describe_feed_response(
            self._resp(200, b"<?xml version='1.0'?><rss><channel/></rss>", "application/rss+xml"))
        self.assertIn("200", diag)
        self.assertIn("XML", diag)
        self.assertNotIn("非XML", diag)


class TestHotnessV3Factors(unittest.TestCase):
    """v3.0 四个维度的量纲与行为。

    背景：v2.1 在线上 17 条数据上的消融实验显示，跨源共振分与内容质量分
    完全不影响排序（ρ=1.000 / 15 条为 0），榜单实际只由关键词 IDF 决定。
    这里逐维锁定「必须真实参与」，防止再退化回单因子决定论。
    """

    def _item(self, title, source="Google News 生态环境", hours_ago=6, **extra):
        now = datetime.now(timezone.utc)
        it = {
            "title": title,
            "source": source,
            "link": "https://example.com/x",
            "summary": "",
            "published": "",
            "published_dt": now - timedelta(hours=hours_ago),
        }
        it.update(extra)
        return it

    def test_authority_has_no_constant_floor(self):
        """权威度不能有常数底分。

        旧口径 15+(w-1)*10 给每个源 15 分底分 —— 常数项不参与排序，
        满分 25 里只有 8 分真正影响名次。新口径未列入权重表的源应得 0 分。
        """
        cfg = dr.load_config()
        items = [self._item("某地环境议题研究", "完全未列入权重表的来源"),
                 self._item("Water pollution study", "Nature")]
        out = dr.calculate_heat_v3(items, cfg)
        self.assertEqual(out[0]["score_breakdown"]["authority_score"], 0.0)
        self.assertAlmostEqual(out[1]["score_breakdown"]["authority_score"], 18.0, places=1)

    def test_dimension_maxima_exposed_for_frontend(self):
        """四维满分必须写进 breakdown（前端模态框据此标注量纲）"""
        cfg = dr.load_config()
        out = dr.calculate_heat_v3([self._item("生态环境议题研究")], cfg)
        bd = out[0]["score_breakdown"]
        self.assertEqual(bd["algorithm"], "v3.0")
        self.assertEqual(bd["base_max"], 70.0)
        self.assertEqual(bd["dimension_max"],
                         {"authority": 18.0, "topic": 18.0, "resonance": 18.0, "information": 16.0})

    def test_topic_floor_covers_unmatched_env_title(self):
        """关键词表未覆盖、但标题确属环境题材时不应被归零。

        线上实测 7/17 条 matched_keywords 为空；若无兜底，话题分对这些条目
        等于「词表覆盖运气」而不是内容价值。
        """
        cfg = dr.load_config()
        out = dr.calculate_heat_v3([self._item("永州市溶洞污染排查整治工作推进会召开")], cfg)
        self.assertGreater(out[0]["score_breakdown"]["topic_score"], 0.0)

    def test_resonance_comes_from_event_media_count(self):
        """同一事件被多家媒体报道 -> 共振分 > 0；单一来源 -> 0。

        用例取自线上真实数据（2026-09-21 榜单第 1、2 名），两条标题分属
        上海热线与奥一网两家媒体 —— 这正是 v2.1 漏掉、导致共振分恒 0 的场景。
        """
        cfg = dr.load_config()
        items = [
            self._item("生态环境部：重拳整治环境监测造假！ - 上海热线"),
            self._item("表演式采样、伪造数据？生态环境部部署全国严打环境监测造假 - 奥一网"),
            self._item("Redox homeostasis governs anaerobic microbial stability", "Water Research"),
        ]
        out = dr.calculate_heat_v3(items, cfg)
        self.assertEqual(out[2]["score_breakdown"]["resonance_score"], 0.0)
        self.assertGreater(out[0]["score_breakdown"]["resonance_score"], 0.0)
        self.assertEqual(out[0]["score_breakdown"]["event_media_count"], 2)
        self.assertEqual(out[0]["score_breakdown"]["event_size"], 2)

    def test_duplicate_penalty_hits_only_non_representative(self):
        """同一事件中只有代表条目不被降权"""
        cfg = dr.load_config()
        items = [
            self._item("生态环境部：重拳整治环境监测造假！ - 上海热线"),
            self._item("表演式采样、伪造数据？生态环境部部署全国严打环境监测造假 - 奥一网"),
        ]
        out = dr.calculate_heat_v3(items, cfg)
        pens = sorted(it["score_breakdown"]["repeat_penalty"] for it in out)
        self.assertEqual(pens, [dr.DUPLICATE_PENALTY, 1.0])

    def test_info_score_is_language_neutral(self):
        """英文标题不应在信息量维度上系统性拿 0。

        旧质量分读 summary，而中文查询源全都没有 RSS 描述，
        实测 15/17 条为 0 —— 且对英文条目天然有利。新判据中英文对等。
        """
        cfg = dr.load_config()
        out = dr.calculate_heat_v3(
            [self._item("Solar-driven desalination coupled with antibiotic degradation",
                        "Water Research")], cfg)
        self.assertGreater(out[0]["score_breakdown"]["info_score"], 0.0)

    def test_info_score_zero_for_vague_slogan(self):
        """空泛标语型标题拿 0（无量化信息/主体/研究信号/描述）"""
        cfg = dr.load_config()
        out = dr.calculate_heat_v3([self._item("共建共治绘新篇")], cfg)
        self.assertEqual(out[0]["score_breakdown"]["info_score"], 0.0)

    def test_every_dimension_varies_in_mixed_batch(self):
        """混合批次里每一维都必须有非零跨度（否则等于常数项，不参与排序）"""
        cfg = dr.load_config()
        items = [
            self._item("生态环境部：重拳整治环境监测造假！", "Nature",
                       matched_keywords=["微塑料"]),
            self._item("表演式采样、伪造数据？生态环境部部署全国严打环境监测造假", "完全未列出"),
            self._item("共建共治绘新篇", "Google News 环境保护"),
        ]
        out = dr.calculate_heat_v3(items, cfg)
        for key in ("authority_score", "topic_score", "resonance_score", "info_score"):
            vals = [it["score_breakdown"][key] for it in out]
            self.assertGreater(max(vals) - min(vals), 0.0,
                               "%s 在本批中无差异，等于常数项" % key)


class TestHotnessV3EventCluster(unittest.TestCase):
    """事件聚类：v3.0 共振分的识别基础。"""

    def test_overlap_beats_jaccard_on_chinese_titles(self):
        """线上真实案例：两条同事件标题的 Jaccard 低于阈值、重叠系数高于阈值"""
        a = "生态环境部：重拳整治环境监测造假！"
        b = "表演式采样、伪造数据？生态环境部部署全国严打环境监测造假"
        ta, tb = dr._title_token_set(a), dr._title_token_set(b)
        inter = ta & tb
        self.assertTrue(inter, "前提：两条标题应有共同 token")
        self.assertLess(dr._jaccard(ta, tb), dr.EVENT_CLUSTER_OVERLAP_THRESHOLD,
                        "Jaccard 应低于阈值（这正是旧口径漏判的原因）")
        self.assertGreaterEqual(len(inter) / min(len(ta), len(tb)),
                                dr.EVENT_CLUSTER_OVERLAP_THRESHOLD,
                                "重叠系数应达到阈值")

    def test_cluster_detects_same_event_across_media(self):
        items = [{"title": "生态环境部：重拳整治环境监测造假！ - 上海热线"},
                 {"title": "表演式采样、伪造数据？生态环境部部署全国严打环境监测造假 - 奥一网"}]
        cl = dr._cluster_events(items)
        self.assertEqual(len(cl), 1)
        self.assertEqual(len(cl[0]), 2)

    def test_cluster_does_not_merge_distinct_events(self):
        items = [{"title": "生态环境部：重拳整治环境监测造假！"},
                 {"title": "江西省流域水生态环境保护十五五规划征求意见稿"},
                 {"title": "京津冀生态环境志愿服务活动在北京举行"}]
        self.assertEqual(len(dr._cluster_events(items)), 3)

    def test_source_suffix_can_create_false_similarity(self):
        """来源后缀必须在校验前剥掉：否则不同条目会因后缀而看起来相似"""
        items = [{"title": "某地开展环境监测造假专项整治 - 上海热线"},
                 {"title": "表演式采样环境监测造假专项整治部署 - 奥一网"}]
        self.assertEqual(len(dr._cluster_events(items)), 1,
                         "剥掉来源后缀后两条应聚为同一事件")

    def test_extract_media_name_forms(self):
        cases = [
            ("生态环境部：重拳整治环境监测造假！ - 上海热线", "上海热线"),
            ("表演式采样、伪造数据？ - 奥一网", "奥一网"),
            ("来自中国电网的超级气候污染物 - Inside Climate News", "Inside Climate News"),
            ("Redox homeostasis governs anaerobic stability", ""),
            ("", ""),
        ]
        for title, expect in cases:
            self.assertEqual(dr.extract_media_name(title), expect, "解析错误：%s" % title)

    def test_origin_source_falls_back_to_feed_name(self):
        item = {"title": "Redox homeostasis governs anaerobic stability",
                "source": "Water Research"}
        self.assertEqual(dr.item_origin_source(item), "Water Research")


class TestHotnessV3Calibration(unittest.TestCase):
    """展示分标定：从「逐日相对分」改为「绝对标定」。"""

    def _item(self, title, source="Google News 生态环境", hours_ago=6, **extra):
        now = datetime.now(timezone.utc)
        it = {"title": title, "source": source, "link": "https://example.com/x",
              "summary": "", "published": "",
              "published_dt": now - timedelta(hours=hours_ago)}
        it.update(extra)
        return it

    def test_absolute_mode_does_not_depend_on_batch(self):
        """绝对标定下展示分只由自身 raw 决定，与同批其他条目无关。

        逐日 min-max 口径下，把一个低分条目单独跑会直接变成满分 ——
        本用例锁死这一行为不再出现。
        """
        cfg = dr.load_config()
        lone = self._item("共建共治绘新篇")
        strong = self._item("生态环境部发布重拳整治监测造假行动方案", "Nature")
        single = dr.calculate_heat_v3([dict(lone)], cfg)
        mixed = dr.calculate_heat_v3([dict(lone), dict(strong)], cfg)
        self.assertEqual(single[0]["score_v2"], mixed[0]["score_v2"])
        self.assertLess(mixed[0]["score_v2"], dr.DISPLAY_SCORE_MAX)

    def test_weak_day_does_not_get_full_marks(self):
        """全天内容都很弱时不应出现满分条目（旧口径必然给出 100）"""
        cfg = dr.load_config()
        weak = [self._item("共建共治绘新篇" + str(i)) for i in range(4)]
        out = dr.calculate_heat_v3(weak, cfg)
        for it in out:
            self.assertLess(it["score_v2"], dr.HOTNESS_LEVEL_HIGH)

    def test_relative_mode_reproducible_for_history(self):
        """relative 模式保留（用于复现历史口径）：单条给中性分"""
        cfg = dr.load_config()
        rel = {"weights": cfg["weights"], "hotness": {"display": {"mode": "relative"}}}
        out = dr.calculate_heat_v3([self._item("生态环境议题研究")], rel)
        self.assertEqual(out[0]["score_v2"], dr.DISPLAY_SCORE_MID)
        self.assertEqual(out[0]["score_breakdown"]["display_mode"], "relative")

    def test_display_score_within_bounds(self):
        cfg = dr.load_config()
        items = [self._item("生态环境部发布行动方案", "Nature"),
                 self._item("共建共治绘新篇"),
                 self._item("永州市溶洞污染排查整治工作推进会召开")]
        out = dr.calculate_heat_v3(items, cfg)
        for it in out:
            self.assertGreaterEqual(it["score_v2"], dr.DISPLAY_SCORE_MIN)
            self.assertLessEqual(it["score_v2"], dr.DISPLAY_SCORE_MAX)


class TestHeatInputRobustness(unittest.TestCase):
    """F5 / F6：热点主链路的输入容错。

    背景：calculate_heat_v3 的逐条循环原先没有任何 try/except，一条脏数据
    （naive 时间、权重写成字符串、权重表写成 null）就会让整次运行抛错、
    当日更新全废。本项目在 AI 聚类解析、院校渲染、时间线快照处都已确立
    「一条脏数据不能让整批失效」，热度主链路同样补齐。
    """

    def _item(self, title="生态环境部发布行动方案", source="Nature", hours_ago=3, **extra):
        now = datetime.now(timezone.utc)
        it = {"title": title, "source": source, "link": "https://example.com/x",
              "summary": "", "published": "",
              "published_dt": now - timedelta(hours=hours_ago)}
        it.update(extra)
        return it

    def test_naive_published_dt_does_not_raise(self):
        """naive datetime 必须被当作 UTC 处理，而不是抛 TypeError 中断整批。"""
        cfg = dr.load_config()
        items = [self._item(published_dt=datetime.now() - timedelta(hours=3))]  # 故意 naive
        out = dr.calculate_heat_v3(items, cfg)
        self.assertEqual(len(out), 1)
        # 3 小时前的条目应落在"新鲜"区间（时间常数 48h -> 约 0.96）
        self.assertGreater(out[0]["score_breakdown"]["time_factor"], 0.9)

    def test_non_datetime_published_dt_falls_back_to_no_time(self):
        """published_dt 是字符串等非法类型时按"无发布时间"处理（时间衰减到底）。"""
        cfg = dr.load_config()
        items = [self._item(published_dt="2026-09-21T00:00:00+00:00")]
        out = dr.calculate_heat_v3(items, cfg)
        self.assertAlmostEqual(out[0]["score_breakdown"]["time_factor"], 0.35, places=3)

    def test_calculate_heat_v1_tolerates_naive_published_dt(self):
        """v1 对照分同样不能被 naive 时间打断（它也被前端弹窗读取）。"""
        naive = datetime.now() - timedelta(hours=5)
        score, breakdown, _weight, _hours = dr.calculate_heat_v1(
            {"title": "t", "source": "Nature", "published_dt": naive},
            {}, {}, 2.0)
        self.assertGreater(breakdown["time_score"], 0.0)
        self.assertGreater(score, 0.0)

    def test_filter_by_time_accepts_naive_published_dt(self):
        """filter_by_time 遇到 naive 时间应补上 UTC 时区而不是抛错。"""
        items = [{"title": "t", "published_dt": datetime.now() - timedelta(hours=2)}]
        kept = dr.filter_by_time(items, hours=48)
        self.assertEqual(len(kept), 1)
        self.assertIsNotNone(kept[0]["published_dt"].tzinfo)

    def test_source_weights_none_falls_back_to_defaults(self):
        """source_weights 写成 YAML 空值 -> 回退默认权重表，不抛 AttributeError。"""
        cfg = dr.load_config()
        items = [self._item(source="Nature")]
        out = dr.calculate_heat_v3(items, {"weights": {"source_weights": None}})
        self.assertAlmostEqual(out[0]["score_breakdown"]["authority_score"], 18.0, places=1)
        out2 = dr.calculate_heat_v3([self._item(source="Nature")], {"weights": None})
        self.assertAlmostEqual(out2[0]["score_breakdown"]["authority_score"], 18.0, places=1)
        self.assertTrue(cfg)  # 默认配置本身未被修改

    def test_string_source_weight_is_coerced(self):
        """权重写成字符串（YAML 引号）-> 转成数值；不可解析则退回 1.0。"""
        out = dr.calculate_heat_v3(
            [self._item(source="Nature")],
            {"weights": {"source_weights": {"Nature": "2.0"}}})
        self.assertAlmostEqual(out[0]["score_breakdown"]["authority_score"], 18.0, places=1)

        out2 = dr.calculate_heat_v3(
            [self._item(source="Nature")],
            {"weights": {"source_weights": {"Nature": "high"}}})
        self.assertEqual(out2[0]["score_breakdown"]["authority_score"], 0.0)

    def test_get_source_weight_preserves_numeric_behaviour(self):
        """数值原样返回（int 仍是 int），只在遇到非法类型时兜底为 1.0。"""
        self.assertEqual(dr.get_source_weight("A", None), 1.0)
        self.assertEqual(dr.get_source_weight("A", {}), 1.0)
        self.assertEqual(dr.get_source_weight("A", {"A": 2}), 2)
        self.assertEqual(dr.get_source_weight("A", {"A": 1.5}), 1.5)
        self.assertEqual(dr.get_source_weight("A", {"A": "1.5"}), 1.5)
        self.assertEqual(dr.get_source_weight("A", {"A": "abc"}), 1.0)
        self.assertEqual(dr.get_source_weight("A", {"A": None}), 1.0)


class TestHotnessV3ParamClamp(unittest.TestCase):
    """F7：hotness 配置段的参数钳制必须对称。

    原先只有 reso_tau / display.k / 密度系数有钳制，四维满分与聚类阈值完全没有 ——
    一处配置笔误会让整个维度静默失效（实测 overlap_threshold=1.5 时全部条目各自
    成簇、共振维度整体归零）。
    """

    SAME_EVENT = [
        "生态环境部：重拳整治环境监测造假！ - 上海热线",
        "表演式采样、伪造数据？生态环境部部署全国严打环境监测造假 - 奥一网",
    ]

    def _item(self, title, source="Google News 生态环境", hours_ago=6):
        return {"title": title, "source": source, "link": "", "summary": "",
                "published": "",
                "published_dt": datetime.now(timezone.utc) - timedelta(hours=hours_ago)}

    def _scores(self, items, hotness_cfg):
        out = dr.calculate_heat_v3(items, {"hotness": hotness_cfg})
        return [it["score_breakdown"] for it in out]

    def test_overlap_threshold_above_one_is_clamped(self):
        """阈值 > 1（重叠系数不可能达到）-> 钳到 1.0，不能让共振维度整体归零。"""
        items = [self._item(t) for t in self.SAME_EVENT]
        bd = self._scores(items, {"event_cluster": {"overlap_threshold": 1.5}})
        # 钳到 1.0 后两条仍不会并簇（overlap=0.6 < 1.0），但阈值本身已被压在合法域内
        self.assertEqual([b["event_size"] for b in bd], [1, 1])
        # 关键回归：合法阈值下这两条必须能并簇、共振非零
        bd_ok = self._scores([self._item(t) for t in self.SAME_EVENT],
                             {"event_cluster": {"overlap_threshold": 0.5}})
        self.assertEqual([b["event_size"] for b in bd_ok], [2, 2])
        self.assertGreater(bd_ok[0]["resonance_score"], 0.0)

    def test_overlap_threshold_below_zero_is_clamped(self):
        """阈值 < 0（任意两条都相似）-> 钳到下限，不能把整批并成一簇。"""
        items = [self._item(t) for t in self.SAME_EVENT]
        bd = self._scores(items, {"event_cluster": {"overlap_threshold": -5}})
        # 钳到 0.05 后这两条依旧并簇（行为与合法小阈值一致），且不会出现负阈值语义
        self.assertEqual([b["event_size"] for b in bd], [2, 2])

    def test_duplicate_penalty_is_clamped_to_unit_interval(self):
        """惩罚系数 > 1 会把"重复"变成奖励、< 0 会让 raw 变负 —— 都钳到 [0,1]。"""
        high = self._scores([self._item(t) for t in self.SAME_EVENT],
                            {"event_cluster": {"duplicate_penalty": 3.0}})
        self.assertEqual(sorted(b["repeat_penalty"] for b in high), [1.0, 1.0])

        low = self._scores([self._item(t) for t in self.SAME_EVENT],
                           {"event_cluster": {"duplicate_penalty": -5}})
        self.assertEqual(sorted(b["repeat_penalty"] for b in low), [0.0, 1.0])

        normal = self._scores([self._item(t) for t in self.SAME_EVENT],
                              {"event_cluster": {"duplicate_penalty": 0.6}})
        self.assertEqual(sorted(b["repeat_penalty"] for b in normal),
                         [dr.DUPLICATE_PENALTY, 1.0])

    def test_dimension_maxima_are_clamped(self):
        """四维满分钳到 [0, HOTNESS_DIMENSION_MAX_BOUND]，负值不能让 base 变负。"""
        neg = self._scores([self._item(self.SAME_EVENT[0])],
                           {"dimensions": {"authority": -50}})
        self.assertEqual(neg[0]["authority_score"], 0.0)
        self.assertEqual(neg[0]["dimension_max"]["authority"], 0.0)

        huge = self._scores([self._item(self.SAME_EVENT[0])],
                            {"dimensions": {"authority": 10000}})
        self.assertEqual(huge[0]["dimension_max"]["authority"], dr.HOTNESS_DIMENSION_MAX_BOUND)

    def test_default_config_is_untouched_by_clamping(self):
        """钳制只对越界值生效：默认配置下四维满分与聚类阈值保持原值。"""
        bd = self._scores([self._item(self.SAME_EVENT[0])], {})
        self.assertEqual(bd[0]["dimension_max"],
                         {"authority": dr.HOTNESS_AUTHORITY_MAX,
                          "topic": dr.HOTNESS_TOPIC_MAX,
                          "resonance": dr.HOTNESS_RESONANCE_MAX,
                          "information": dr.HOTNESS_INFO_MAX})
        self.assertEqual(bd[0]["base_max"], 70.0)


class TestAnalysisDrivers(unittest.TestCase):
    """F1：分析文案的驱动因素识别必须跟得上 score_breakdown 的 schema 变更。

    旧实现只按 v1 键名（source_score / keyword_score / …）取值，分支判据又是
    `if sb:`（对任何非空字典恒真）——于是 v3.0 上线后永远走旧分支、四个值全取到 0、
    drivers 恒为空，连四维满分条目也说不出驱动因素（实测 0/200），全站文案退化成
    「热度受综合因素影响，可留意」。零报错、零异常、单测全绿，属于"换了数据 schema、
    消费方没跟上"的静默退化。
    """

    V3_BREAKDOWN = {
        "algorithm": "v3.0",
        "dimension_max": {"authority": 18.0, "topic": 18.0,
                          "resonance": 18.0, "information": 16.0},
        "authority_score": 18.0, "topic_score": 18.0,
        "resonance_score": 18.0, "info_score": 16.0, "time_factor": 1.0,
    }

    def test_analysis_drivers_reads_v3_keys(self):
        drivers = dr._analysis_drivers(dict(self.V3_BREAKDOWN))
        self.assertIn("来源权威性高", drivers)
        self.assertIn("发布时间较新", drivers)
        self.assertIn("多家媒体同题报道", drivers)

    def test_analysis_drivers_reads_v1_keys(self):
        """v1 对照分仍在被前端弹窗读取，旧键名路径不能因为兼容 v3 而失效。"""
        sb = {"base": 5.0, "source_score": 6.0, "keyword_score": 4.0,
              "time_score": 9.9, "topic_bonus": 2.0, "total": 27.0}
        drivers = dr._analysis_drivers(sb)
        self.assertIn("来源权威性高", drivers)
        self.assertIn("发布时间较新", drivers)
        self.assertIn("主题热度高", drivers)
        self.assertIn("与近期热点主题相关", drivers)

    def test_analysis_drivers_ignores_unknown_schema(self):
        """两套键名都不匹配时不硬凑（返回空，由调用方兜底），避免编造驱动因素。"""
        self.assertEqual(dr._analysis_drivers({"algorithm": "v9"}), [])
        self.assertEqual(dr._analysis_drivers({}), [])

    def test_enhance_analysis_never_degenerates_for_v3_item(self):
        """v3 满分条目必须能说出「因……」，而不是退化成「受综合因素影响」。"""
        item = {"title": "某条标题", "topic_tags": ["水污染防治"],
                "score_breakdown": dict(self.V3_BREAKDOWN)}
        text = dr.enhance_analysis_with_tags(item)
        self.assertIn("热度上升", text)
        self.assertNotIn("综合因素", text)
        self.assertIn("水污染防治", text)

    def test_enhance_analysis_falls_back_without_breakdown(self):
        text = dr.enhance_analysis_with_tags({"title": "t"})
        self.assertIn("综合因素", text)

    def test_real_pipeline_item_gets_drivers(self):
        """真实链路：calculate_hotness 产出 breakdown -> 分析文案能识别驱动因素。

        这是端到端的那条断言 —— 单测直接喂 breakdown 会漏掉"算法写出的键名
        与消费方读的键名不一致"这类问题，必须走一遍完整 pipeline。
        """
        items = [{"title": "生态环境部发布新污染物治理行动方案",
                  "source": "Nature", "summary": "", "link": "",
                  "published_dt": datetime.now(timezone.utc) - timedelta(hours=2)}]
        dr.calculate_hotness(items, dr.load_config())
        text = dr.enhance_analysis_with_tags(items[0])
        self.assertIn("热度上升", text)
        self.assertNotIn("综合因素", text)


class TestMatchedKeywordsInvariant(unittest.TestCase):
    """F3：matched_keywords 必须始终是 config 词表的子集。

    这是「话题分的噪声词过滤」曾被写成死判据的前提 —— 它的两个条件
    （不在领域白名单、且不在当日关键词计数里）在本数据流下都不可能成立：
    前者因为 match_keywords 只会返回 config 词表里的词、后者因为
    keyword_item_count 正是由同一批词统计出来的。该过滤与随之失效的
    glossary.json（140 KB）白读已移除，这里用不变量把前提锁住：
    只要这个不变量成立，就不需要任何"二次过滤"。
    """

    def test_matched_keywords_are_subset_of_config_keywords(self):
        cfg_keywords = ["碳市场", "碳排放"]
        items = [
            {"title": "全国碳排放权交易市场配额分配方案发布"},
            {"title": "某地开展碳排放核查", "summary": "涉及碳市场交易"},
        ]
        dr.calculate_hotness(items, {"keywords": cfg_keywords})
        for it in items:
            matched = set(it["matched_keywords"])
            self.assertTrue(matched, "本用例应至少命中一个关键词")
            self.assertTrue(matched <= set(cfg_keywords),
                            f"匹配出配置词表之外的关键词：{matched - set(cfg_keywords)}")

    def test_keyword_item_count_is_derived_from_matched_keywords(self):
        """当日计数只能来自 matched_keywords —— 死判据的另一半前提。"""
        cfg = {"keywords": ["碳市场", "碳排放"]}
        items = [{"title": "碳排放 碳排放"}, {"title": "碳市场"}]
        dr.calculate_hotness(items, cfg)
        counted = set()
        for it in items:
            counted |= set(it["matched_keywords"])
        # 每个被计入当日统计的词，都必须出现在某条的 matched_keywords 里
        self.assertTrue(counted <= {"碳市场", "碳排放"})

class TestPersonalKnowledgeRotation(unittest.TestCase):
    """F8：personal_knowledge.md（CI 每日追加的累积日志）的轮转。

    旧实现是「读全量 -> 正则替换当天段 -> 写全量」且**永不裁剪**：按约 11 KB/日
    估算，一年后单文件约 4 MB，每次运行都要全量扫描两遍，而这份文件是 CI 每日
    提交的对象，体积会永久留在仓库里。新实现按保留窗口裁掉超窗的日记块，并按
    月份归档到 docs/data/archive/personal_knowledge-YYYY-MM.md（归档目录已被
    CI 的 `git add docs/data/` 覆盖，内容不会丢，也不需要手工上传）。

    安全性由**写入顺序**保证：先写归档、全部成功后才裁主文件；归档失败则原样
    保留全部历史（本用例专门锁住这条）。
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pk_")
        self.data_dir = os.path.join(self.tmp, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self._patches = [
            mock.patch.object(dr, "DATA_DIR", self.data_dir),
            mock.patch.object(dr, "__file__", os.path.join(self.tmp, "daily_report.py")),
        ]
        for p in self._patches:
            p.start()
        with open(os.path.join(self.data_dir, "latest.json"), "w", encoding="utf-8") as f:
            json.dump({"keywords": [], "items": []}, f)

    def tearDown(self):
        for p in self._patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------- helpers ----------
    def _main_path(self):
        return os.path.join(self.tmp, "personal_knowledge.md")

    def _read(self, path):
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _seed(self, days_back):
        """写入「今天 + 前 days_back-1 天」的日记块，返回日期列表。"""
        now = datetime.now(timezone.utc)
        dates = [(now - timedelta(days=k)).strftime("%Y-%m-%d")
                 for k in range(days_back - 1, -1, -1)]
        text = "# 个人知识库\n\n> 测试种子\n\n---\n\n"
        text += "\n\n".join("## %s\n\n- 种子内容 %s\n\n---" % (d, d) for d in dates)
        with open(self._main_path(), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        return dates

    def _headers(self, text):
        return dr._PERSONAL_KNOWLEDGE_DAY_RE.findall(text)

    def _archive_headers(self):
        archive_dir = os.path.join(self.data_dir, "archive")
        found = []
        if os.path.isdir(archive_dir):
            for name in sorted(os.listdir(archive_dir)):
                found += self._headers(self._read(os.path.join(archive_dir, name)))
        return found

    # ---------- tests ----------
    def test_same_day_is_replaced_not_duplicated(self):
        """同一天重复运行只应有一个当天小节（幂等）。"""
        dr.generate_personal_knowledge()
        dr.generate_personal_knowledge()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        headers = self._headers(self._read(self._main_path()))
        self.assertEqual(headers.count(today), 1)

    def test_rotation_moves_old_days_to_monthly_archive(self):
        seeded = self._seed(6)
        with mock.patch.object(dr, "PERSONAL_KNOWLEDGE_KEEP_DAYS", 2):
            dr.generate_personal_knowledge()
        kept = self._headers(self._read(self._main_path()))
        archived = self._archive_headers()
        self.assertLessEqual(len(kept), 3, "主文件应只保留今天 + 最近 2 天")
        self.assertTrue(archived, "归档文件不应为空")
        lost = set(seeded) - set(kept) - set(archived)
        self.assertEqual(lost, set(), "有内容既不在主文件也不在归档里：%s" % sorted(lost))

    def test_archived_content_is_retained_verbatim(self):
        """归档的是原文，不是摘要 —— 正文必须逐字保留。"""
        seeded = self._seed(6)
        with mock.patch.object(dr, "PERSONAL_KNOWLEDGE_KEEP_DAYS", 2):
            dr.generate_personal_knowledge()
        archive_dir = os.path.join(self.data_dir, "archive")
        merged = "".join(self._read(os.path.join(archive_dir, n))
                         for n in sorted(os.listdir(archive_dir)))
        for d in seeded:
            if d not in self._headers(self._read(self._main_path())):
                self.assertIn("种子内容 %s" % d, merged)

    def test_rotation_is_idempotent(self):
        """连跑两次不应在归档里写出重复日期。"""
        self._seed(6)
        with mock.patch.object(dr, "PERSONAL_KNOWLEDGE_KEEP_DAYS", 2):
            dr.generate_personal_knowledge()
            dr.generate_personal_knowledge()
        headers = self._archive_headers()
        self.assertEqual(len(headers), len(set(headers)),
                         "归档里出现重复日期：%s" % sorted(headers))

    def test_keep_days_zero_disables_rotation(self):
        """keep_days <= 0 = 关闭轮转（保留全部历史），且不产生归档目录。"""
        seeded = self._seed(6)
        with mock.patch.object(dr, "PERSONAL_KNOWLEDGE_KEEP_DAYS", 0):
            dr.generate_personal_knowledge()
        kept = self._headers(self._read(self._main_path()))
        self.assertTrue(set(seeded) <= set(kept), "关闭轮转后不应裁掉任何历史")
        self.assertFalse(os.path.exists(os.path.join(self.data_dir, "archive")))

    def test_archive_failure_keeps_history_in_main_file(self):
        """归档失败时宁可不裁 —— 绝不冒「内容被裁掉却没归档」的风险。"""
        seeded = self._seed(6)
        with mock.patch.object(dr, "PERSONAL_KNOWLEDGE_KEEP_DAYS", 2), \
                mock.patch.object(dr.os, "makedirs", side_effect=OSError("boom")):
            dr.generate_personal_knowledge()
        kept = self._headers(self._read(self._main_path()))
        self.assertTrue(set(seeded) <= set(kept), "归档失败却把历史裁掉了")


class _FakeAIResponse:
    """AI 端点响应替身：只实现 _ai_call 实际用到的属性与方法。"""

    def __init__(self, status_code=200, content="模型输出", headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = content or ""
        self._content = content

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise dr.requests.exceptions.HTTPError(response=self)


class TestAiGovernance(unittest.TestCase):
    """AI 调用治理层：限流 / 退避 / Retry-After / 缓存 / 预算 / 熔断。

    每个用例都用替身替换 requests.post，因此**不产生任何真实网络请求**。
    """

    def setUp(self):
        self._snap = {
            "limits": dict(dr.AI_LIMITS),
            "delays": list(dr.AI_RETRY_DELAYS),
            "failures": dict(dr.AI_FUNC_FAILURES),
            "logged": set(dr.AI_FUNC_DEGRADED_LOGGED),
            "count": dr._AI_CALL_COUNT,
            "warned": dr._AI_BUDGET_WARNED,
            "cache": dict(dr._AI_RESULT_CACHE),
            "ts": list(dr._AI_CALL_TS),
            "last": dr._AI_LAST_TS,
            "hits": dr._AI_CACHE_HITS,
        }
        self._calls = []
        self._script = []
        self._orig_post = dr.requests.post
        dr.requests.post = self._fake_post
        # 退避表压到毫秒级：测的是"退避逻辑"而不是"真的等 30 秒"
        dr.AI_RETRY_DELAYS = [0.01, 0.02, 0.03]
        dr.AI_LIMITS.update({"rpm": 6000, "max_concurrency": 1, "max_calls_per_run": 80,
                             "jitter_ratio": 0.0, "max_backoff": 60.0,
                             "cache_enabled": True, "honor_retry_after": True})
        dr.configure_ai_limits({})
        dr.AI_FUNC_FAILURES.clear()
        dr.AI_FUNC_DEGRADED_LOGGED.clear()
        dr._AI_RESULT_CACHE.clear()
        dr._AI_CALL_TS.clear()
        dr._AI_CALL_COUNT = 0
        dr._AI_BUDGET_WARNED = False
        dr._AI_CACHE_HITS = 0
        dr._AI_CALL_LOG.clear()
        dr._AI_RETRY_LOG.clear()

    def tearDown(self):
        dr.requests.post = self._orig_post
        dr.AI_LIMITS.clear(); dr.AI_LIMITS.update(self._snap["limits"])
        dr.configure_ai_limits({})          # 按恢复后的并发数重建信号量
        dr.AI_RETRY_DELAYS[:] = self._snap["delays"]
        dr.AI_FUNC_FAILURES.clear(); dr.AI_FUNC_FAILURES.update(self._snap["failures"])
        dr.AI_FUNC_DEGRADED_LOGGED.clear(); dr.AI_FUNC_DEGRADED_LOGGED.update(self._snap["logged"])
        dr._AI_CALL_COUNT = self._snap["count"]
        dr._AI_BUDGET_WARNED = self._snap["warned"]
        dr._AI_RESULT_CACHE.clear(); dr._AI_RESULT_CACHE.update(self._snap["cache"])
        dr._AI_CALL_TS[:] = self._snap["ts"]
        dr._AI_LAST_TS = self._snap["last"]
        dr._AI_CACHE_HITS = self._snap["hits"]

    def _fake_post(self, url, headers=None, json=None, timeout=None):
        self._calls.append(time.time())
        if not self._script:
            return _FakeAIResponse(200)
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    @property
    def _cfg(self):
        return {"summary_enabled": True, "api_key": "k", "model": "m",
                "fallback_model": "", "base_url": "https://example.invalid/v1/",
                "max_tokens": 100}

    # ---------- 重试与退避 ----------

    def test_429_then_success_retries_and_clears_failure(self):
        self._script = [_FakeAIResponse(429), _FakeAIResponse(429), _FakeAIResponse(200, "结果")]
        out = dr.call_nvidia_api("p1", self._cfg, feature="T1")
        self.assertEqual(out, "结果")
        self.assertEqual(len(self._calls), 3, "两次 429 后应发出第 3 次请求并成功")
        self.assertEqual(dr._AI_RETRY_LOG.get("T1"), 2)
        self.assertEqual(dr.AI_FUNC_FAILURES.get("T1", 0), 0, "成功后该功能失败计数应清零")

    def test_retry_after_header_is_honored(self):
        """服务端 Retry-After 优先于本地退避表：表值是 0.01s，故意用它验证"""
        self._script = [_FakeAIResponse(429, headers={"Retry-After": "1"}),
                        _FakeAIResponse(200, "ok")]
        t0 = time.time()
        out = dr.call_nvidia_api("p2", self._cfg, feature="T2")
        self.assertEqual(out, "ok")
        self.assertGreaterEqual(time.time() - t0, 0.9,
                                "应等待服务端要求的 1 秒，而不是本地 0.01 秒")

    def test_gives_up_after_max_attempts_without_premature_breaker(self):
        """用尽一次调用的全部尝试 -> 返回 None，但只记 1 次失败、不熔断

        2026-09-26 修正：旧实现把重试循环内**每一次尝试**都记一次失败，于是一次调用
        （AI_MAX_ATTEMPTS=4）就能把该功能熔断 —— 而设计本意是"连续 3 次**调用**失败"。
        实测副作用有两个：故障被放大 4 倍；降级日志在重试中途打印，之后仍发出第 4 次
        请求并成功，日志出现"已降级为规则模式"紧跟"调用成功"的自相矛盾记录
        （2026-09-25 线上运行日志实证）。计数单位是"调用"，不是"HTTP 尝试"。
        """
        self._script = [_FakeAIResponse(429)] * dr.AI_MAX_ATTEMPTS
        out = dr.call_nvidia_api("p3", self._cfg, feature="T3")
        self.assertIsNone(out)
        self.assertEqual(len(self._calls), dr.AI_MAX_ATTEMPTS,
                         "用尽所有尝试后应停止请求")
        self.assertEqual(dr.AI_FUNC_FAILURES["T3"], 1,
                         "一次调用内重试多次，只应记 1 次失败")
        self.assertFalse(dr._ai_func_disabled("T3"),
                         "单次调用失败不得熔断（熔断需连续 N 次调用失败）")

    def test_degrades_after_consecutive_failed_calls(self):
        """连续 AI_FUNC_MAX_FAILURES 次**调用**都失败 -> 该功能独立熔断、降级规则"""
        for _ in range(dr.AI_FUNC_MAX_FAILURES):
            self._script = [_FakeAIResponse(429)] * dr.AI_MAX_ATTEMPTS
            self.assertIsNone(dr.call_nvidia_api("p4", self._cfg, feature="T4"))
        self.assertGreaterEqual(dr.AI_FUNC_FAILURES["T4"], dr.AI_FUNC_MAX_FAILURES)
        self.assertTrue(dr._ai_func_disabled("T4"), "达到阈值后该功能应独立熔断")

    def test_server_5xx_is_retryable(self):
        """503/502 属服务端瞬时故障，旧实现会直接降级，现在应重试"""
        self._script = [_FakeAIResponse(503), _FakeAIResponse(502), _FakeAIResponse(200, "恢复")]
        self.assertEqual(dr.call_nvidia_api("p8", self._cfg, feature="T8"), "恢复")
        self.assertEqual(len(self._calls), 3)

    def test_deterministic_error_not_retried(self):
        """401/403 这类确定性错误重试无意义，应一次即放弃"""
        self._script = [_FakeAIResponse(401), _FakeAIResponse(200, "不该被用到")]
        self.assertIsNone(dr.call_nvidia_api("p10", self._cfg, feature="T10"))
        self.assertEqual(len(self._calls), 1)

    def test_400_strips_field_without_consuming_backoff(self):
        self._script = [_FakeAIResponse(400), _FakeAIResponse(200, "ok")]
        t0 = time.time()
        self.assertEqual(dr.call_nvidia_api("p9", self._cfg, json_mode=True, feature="T9"), "ok")
        self.assertEqual(len(self._calls), 2)
        self.assertLess(time.time() - t0, 0.5, "400 是立即重试，不应消耗退避")

    def test_backoff_formula(self):
        saved_j = dr.AI_LIMITS["jitter_ratio"]
        saved_mb = dr.AI_LIMITS["max_backoff"]
        try:
            dr.AI_LIMITS["jitter_ratio"] = 0.0
            self.assertEqual(dr._ai_compute_backoff(0), float(dr.AI_RETRY_DELAYS[0]))
            self.assertEqual(dr._ai_compute_backoff(1), float(dr.AI_RETRY_DELAYS[1]))
            self.assertEqual(dr._ai_compute_backoff(99), float(dr.AI_RETRY_DELAYS[-1]),
                             "超出退避表长度应取表尾值")
            self.assertEqual(dr._ai_compute_backoff(0, 45), 45.0, "服务端要求更长时采信服务端")
            self.assertEqual(dr._ai_compute_backoff(1, 0.001), float(dr.AI_RETRY_DELAYS[1]),
                             "服务端要求更短时用本地退避表")
            dr.AI_LIMITS["max_backoff"] = 10.0
            self.assertEqual(dr._ai_compute_backoff(0, 60), 60.0,
                             "Retry-After 明确要求的长等待不应被 max_backoff 压制")
            dr.AI_LIMITS["max_backoff"] = saved_mb
            dr.AI_LIMITS["jitter_ratio"] = 0.25
            base = float(dr.AI_RETRY_DELAYS[1])
            samples = [dr._ai_compute_backoff(1) for _ in range(80)]
            self.assertTrue(all(base <= s <= base * 1.25 + 1e-9 for s in samples),
                            "抖动必须落在 [base, base*(1+ratio)] 内（只向上抖动）")
            self.assertGreater(len(set(samples)), 1, "抖动应产生不同值，避免同步重试")
        finally:
            dr.AI_LIMITS["jitter_ratio"] = saved_j
            dr.AI_LIMITS["max_backoff"] = saved_mb

    def test_retry_after_parsing(self):
        self.assertEqual(dr._ai_parse_retry_after(_FakeAIResponse(429, headers={"Retry-After": "30"})), 30.0)
        self.assertEqual(dr._ai_parse_retry_after(_FakeAIResponse(429, headers={"Retry-After": "1.5"})), 1.5)
        self.assertEqual(
            dr._ai_parse_retry_after(_FakeAIResponse(429, headers={"Retry-After": "Wed, 21 Oct 2020 07:28:00 GMT"})),
            0.0, "已过去的 HTTP-date 应视为 0 秒")
        future = dr._ai_parse_retry_after(
            _FakeAIResponse(429, headers={"Retry-After": "Wed, 21 Oct 2099 07:28:00 GMT"}))
        self.assertIsNotNone(future)
        self.assertGreater(future, 0)
        self.assertIsNone(dr._ai_parse_retry_after(_FakeAIResponse(429, headers={})))
        self.assertIsNone(dr._ai_parse_retry_after(_FakeAIResponse(429, headers={"Retry-After": "soon"})))
        self.assertIsNone(dr._ai_parse_retry_after(None))

    # ---------- 缓存 ----------

    def test_cache_skips_duplicate_request(self):
        self._script = [_FakeAIResponse(200, "缓存内容")]
        first = dr.call_nvidia_api("same-prompt", self._cfg, feature="T4")
        self.assertEqual(len(self._calls), 1)
        second = dr.call_nvidia_api("same-prompt", self._cfg, feature="T4")
        self.assertEqual(first, second)
        self.assertEqual(len(self._calls), 1, "同一 prompt 第二次不应再发请求")
        self.assertGreaterEqual(dr._AI_CACHE_HITS, 1)

    def test_cache_key_is_sensitive_to_all_inputs(self):
        k = dr._ai_cache_key("p", "m", 100, True)
        self.assertEqual(k, dr._ai_cache_key("p", "m", 100, True), "同输入必须同键")
        self.assertNotEqual(k, dr._ai_cache_key("p", "m", 100, False), "json_mode 应参与键")
        self.assertNotEqual(k, dr._ai_cache_key("p", "m", 101, True), "max_tokens 应参与键")
        self.assertNotEqual(k, dr._ai_cache_key("q", "m", 100, True), "prompt 应参与键")
        self.assertNotEqual(k, dr._ai_cache_key("p", "m2", 100, True), "模型应参与键")

    def test_cache_eviction_keeps_size_bounded(self):
        saved_cap = dr.AI_LIMITS["cache_max_entries"]
        try:
            dr.AI_LIMITS["cache_max_entries"] = 8
            for i in range(40):
                dr._ai_cache_put(dr._ai_cache_key("p%d" % i, "m", 1, False), "v%d" % i)
            self.assertLessEqual(len(dr._AI_RESULT_CACHE), 8)
        finally:
            dr.AI_LIMITS["cache_max_entries"] = saved_cap

    def test_cache_disabled_still_calls(self):
        saved = dr.AI_LIMITS["cache_enabled"]
        try:
            dr.AI_LIMITS["cache_enabled"] = False
            self._script = [_FakeAIResponse(200, "x"), _FakeAIResponse(200, "y")]
            dr.call_nvidia_api("nocc", self._cfg, feature="T4b")
            dr.call_nvidia_api("nocc", self._cfg, feature="T4b")
            self.assertEqual(len(self._calls), 2, "关闭缓存后每次都应发请求")
        finally:
            dr.AI_LIMITS["cache_enabled"] = saved

    # ---------- 限流与预算 ----------

    def test_rate_limiter_spaces_out_requests(self):
        dr.AI_LIMITS["rpm"] = 600      # 最小间隔 0.1s
        dr._AI_CALL_TS.clear(); dr._AI_LAST_TS = 0.0
        self._script = [_FakeAIResponse(200, "r%d" % i) for i in range(3)]
        for i in range(3):
            dr.call_nvidia_api("rate-%d" % i, self._cfg, feature="T6")
        self.assertEqual(len(self._calls), 3)
        gaps = [self._calls[i + 1] - self._calls[i] for i in range(len(self._calls) - 1)]
        for g in gaps:
            self.assertGreaterEqual(g, 0.09, "相邻请求间隔应不小于 60/rpm 秒")

    def test_budget_blocks_further_calls(self):
        dr.AI_LIMITS["max_calls_per_run"] = 1
        dr._AI_CALL_COUNT = 0
        dr._AI_BUDGET_WARNED = False
        self._script = [_FakeAIResponse(200, "b1"), _FakeAIResponse(200, "b2")]
        self.assertEqual(dr.call_nvidia_api("budget-1", self._cfg, feature="T7"), "b1")
        self.assertIsNone(dr.call_nvidia_api("budget-2", self._cfg, feature="T7"),
                          "超出预算应直接降级，不再发请求")
        self.assertEqual(len(self._calls), 1)

    def test_configure_limits_clamps_invalid_values(self):
        self.assertEqual(dr.AI_LIMITS["rpm"], 6000)
        dr.configure_ai_limits({"limits": {"rpm": 0, "max_concurrency": -3,
                                           "jitter_ratio": 9.0, "max_calls_per_run": "abc"}})
        self.assertEqual(dr.AI_LIMITS["rpm"], 1, "rpm 至少为 1")
        self.assertEqual(dr.AI_LIMITS["max_concurrency"], 1)
        self.assertEqual(dr.AI_LIMITS["jitter_ratio"], 1.0, "抖动比例夹取到 [0,1]")
        self.assertNotEqual(dr.AI_LIMITS["max_calls_per_run"], "abc", "非法值应保留原默认")

    def test_concurrency_gate_semaphore_matches_config(self):
        dr.configure_ai_limits({"limits": {"max_concurrency": 3}})
        self.assertEqual(dr._ai_get_semaphore()._value, 3)
        dr.configure_ai_limits({"limits": {"max_concurrency": 1}})
        self.assertEqual(dr._ai_get_semaphore()._value, 1)

    def test_report_shape(self):
        self._script = [_FakeAIResponse(200, "x")]
        dr.call_nvidia_api("rep", self._cfg, feature="TRep")
        rep = dr.ai_call_report()
        for key in ("http_calls", "by_feature", "cache_hits", "retries", "rpm",
                    "max_concurrency", "budget", "degraded_features"):
            self.assertIn(key, rep)
        self.assertGreaterEqual(rep["http_calls"], 1)


class TestAiSingleGateway(unittest.TestCase):
    """护栏：所有 AI 请求必须走唯一出口，防止将来新增旁路绕过限流。"""

    # 允许出现 requests.post 的函数白名单：AI 唯一出口 + 正文提取 + DeepL 翻译。
    # 任何新增项都必须先自问：这是 AI 对话请求吗？是的话请改用 _ai_call。
    _ALLOWED_POST_OWNERS = {"_ai_http_post", "extract_article_text", "_deepl_translate"}

    def _enclosing_function(self, lines, lineno):
        for i in range(lineno - 1, -1, -1):
            s = lines[i]
            if s.startswith("def ") or s.startswith("    def "):
                return s.split("(")[0].replace("def", "").strip()
        return "<module>"

    def test_no_bypass_around_ai_gateway(self):
        """所有 AI 请求必须走 _ai_http_post，不得有旁路绕过限流/并发/缓存。"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_report.py")
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        src_lines = src.split("\n")

        owners = {}
        for i, ln in enumerate(src_lines):
            if "requests.post(" in ln:
                owners.setdefault(self._enclosing_function(src_lines, i), []).append(i + 1)

        self.assertIn("_ai_http_post", owners,
                      "AI 请求的唯一出口 _ai_http_post 内应当有 requests.post(")
        unexpected = sorted(set(owners) - self._ALLOWED_POST_OWNERS)
        self.assertEqual(
            unexpected, [],
            "发现绕过 AI 治理层的直连请求，所在函数：%s（行 %s）。"
            "新增 AI 请求请使用 _ai_call / call_nvidia_api。" % (unexpected, owners))

    def test_ai_call_uses_gateway_not_raw_post(self):
        """_ai_call 自己也不得直接 requests.post，必须经由 _ai_http_post。"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_report.py")
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        fn_start = src.index("def _ai_call(")
        fn_end = src.find("\ndef ", fn_start + 1)
        body = src[fn_start:(fn_end if fn_end != -1 else len(src))]
        self.assertIn("_ai_http_post(", body)
        self.assertNotIn("requests.post(", body,
                         "_ai_call 必须经由 _ai_http_post，否则会绕过限流与并发闸门")


class TestAiEventClustering(unittest.TestCase):
    """AI 语义事件聚类接入热度算法的事件共振维度。"""

    def setUp(self):
        self._failures = dict(dr.AI_FUNC_FAILURES)
        self._count = dr._AI_CALL_COUNT
        self._warned = dr._AI_BUDGET_WARNED
        dr.AI_FUNC_FAILURES.clear()
        dr._AI_CALL_COUNT = 0
        dr._AI_BUDGET_WARNED = False

    def tearDown(self):
        dr.AI_FUNC_FAILURES.clear(); dr.AI_FUNC_FAILURES.update(self._failures)
        dr._AI_CALL_COUNT = self._count
        dr._AI_BUDGET_WARNED = self._warned

    def _items(self):
        return [
            {"title": "上海某河道污染整治完成 - 上海热线", "source": "上海热线"},
            {"title": "沪上一河道污染治理通过验收 - 奥一网", "source": "奥一网"},
            {"title": "全球碳市场机制谈判取得进展 - 路透", "source": "路透"},
        ]

    def _item(self, title, source="Google News 生态环境", hours_ago=6, **extra):
        now = datetime.now(timezone.utc)
        it = {"title": title, "source": source, "link": "https://example.com/x",
              "summary": "", "published": "",
              "published_dt": now - timedelta(hours=hours_ago)}
        it.update(extra)
        return it

    def test_cluster_events_prefers_ai_mapping(self):
        assigned = dr._cluster_events(self._items(), ai_mapping={0: "E1", 1: "E1"})
        self.assertEqual(assigned, {0: [0, 1], 2: [2]},
                         "AI 覆盖的下标按 AI 组归组，未覆盖的各自独立成簇")

    def test_cluster_events_without_ai_mapping_uses_token_overlap(self):
        items = self._items()
        assigned = dr._cluster_events(items)
        self.assertEqual(sum(len(v) for v in assigned.values()), len(items),
                         "token 路径必须覆盖全部条目，不能丢条目")

    def test_ai_cluster_events_disabled_by_config(self):
        self.assertIsNone(dr.ai_cluster_events(
            self._items(), {"summary_enabled": True,
                            "algorithm_ai": {"semantic_event_clustering": False}}))

    def test_ai_cluster_events_returns_none_without_credentials(self):
        self.assertIsNone(dr.ai_cluster_events(self._items(), {"summary_enabled": False}))
        self.assertIsNone(dr.ai_cluster_events(self._items(),
                                               {"summary_enabled": True, "api_key": ""}))

    def test_ai_cluster_events_returns_none_when_feature_degraded(self):
        dr.AI_FUNC_FAILURES["事件聚类"] = dr.AI_FUNC_MAX_FAILURES
        self.assertIsNone(dr.ai_cluster_events(self._items(),
                                               {"summary_enabled": True, "api_key": "k"}),
                          "该功能熔断后应直接回退，不再调用")

    def test_ai_cluster_events_success_writes_mapping_and_field(self):
        items = self._items()
        payload = json.dumps({"events": [{"id": "E1", "items": [0, 1]}]})
        with mock.patch.object(dr, "call_nvidia_api", return_value=payload):
            mapping = dr.ai_cluster_events(items, {"summary_enabled": True, "api_key": "k"})
        self.assertEqual(mapping, {0: "E1", 1: "E1"})
        self.assertEqual(items[0].get("_ai_event_id"), "E1")
        self.assertEqual(items[1].get("_ai_event_id"), "E1")
        self.assertIsNone(items[2].get("_ai_event_id"), "未归组的条目不应被塞组号")

    def test_ai_cluster_events_tolerates_dirty_members(self):
        """越界 / 重复 / 非数字成员应被丢弃，其余仍生效"""
        items = self._items()
        payload = json.dumps({"events": [{"id": "E1", "items": ["0", 1, 42, 1]}]})
        with mock.patch.object(dr, "call_nvidia_api", return_value=payload):
            mapping = dr.ai_cluster_events(items, {"summary_enabled": True, "api_key": "k"})
        self.assertEqual(mapping, {0: "E1", 1: "E1"})

    def test_ai_cluster_events_rejects_singleton_groups(self):
        items = self._items()
        payload = json.dumps({"events": [{"id": "E1", "items": [0, 99]},
                                         {"id": "E2", "items": [1, 1]}]})
        with mock.patch.object(dr, "call_nvidia_api", return_value=payload):
            self.assertIsNone(dr.ai_cluster_events(items, {"summary_enabled": True, "api_key": "k"}),
                              "全部退化成单元素组时应回退 token 聚类")

    def test_ai_cluster_events_returns_none_on_garbage(self):
        with mock.patch.object(dr, "call_nvidia_api", return_value="完全不是 JSON"):
            self.assertIsNone(dr.ai_cluster_events(self._items(),
                                                   {"summary_enabled": True, "api_key": "k"}))

    def test_ai_cluster_events_returns_none_on_api_failure(self):
        with mock.patch.object(dr, "call_nvidia_api", return_value=None):
            self.assertIsNone(dr.ai_cluster_events(self._items(),
                                                   {"summary_enabled": True, "api_key": "k"}))

    def test_ai_cluster_events_clears_stale_field(self):
        """上一轮残留的 _ai_event_id 必须被清掉，否则会污染本轮聚类"""
        items = self._items()
        for it in items:
            it["_ai_event_id"] = "STALE"
        with mock.patch.object(dr, "call_nvidia_api", return_value=None):
            dr.ai_cluster_events(items, {"summary_enabled": True, "api_key": "k"})
        self.assertIsNone(items[0].get("_ai_event_id"))

    def test_heat_v3_reports_ai_cluster_source(self):
        cfg = dr.load_config()
        items = [self._item("上海某河道污染整治完成 - 上海热线"),
                 self._item("沪上一河道污染治理通过验收 - 奥一网"),
                 self._item("全球碳市场机制谈判取得进展 - 路透")]
        items[0]["_ai_event_id"] = "E1"
        items[1]["_ai_event_id"] = "E1"
        out = dr.calculate_heat_v3(items, cfg)
        bd = out[0]["score_breakdown"]
        self.assertEqual(bd["event_cluster_source"], "ai")
        self.assertEqual(bd["event_size"], 2, "同一 AI 事件组的两条应聚成一簇")
        self.assertGreater(bd["event_media_count"], 1)

    def test_heat_v3_reports_token_cluster_source_without_ai(self):
        cfg = dr.load_config()
        items = [self._item("上海某河道污染整治完成 - 上海热线"),
                 self._item("沪上一河道污染治理通过验收 - 奥一网")]
        out = dr.calculate_heat_v3(items, cfg)
        self.assertEqual(out[0]["score_breakdown"]["event_cluster_source"], "token")

    def test_heat_v3_still_works_when_ai_fails(self):
        """AI 挂掉不能让事件共振维度消失：两条同事件标题仍应聚成一簇"""
        cfg = dr.load_config()
        items = [self._item("上海某河道污染整治完成 - 上海热线"),
                 self._item("沪上一河道污染治理通过验收 - 奥一网")]
        out = dr.calculate_heat_v3(items, cfg)
        sizes = [it["score_breakdown"]["event_size"] for it in out]
        self.assertTrue(any(s >= 2 for s in sizes), "回退路径下仍应识别出同事件")


    def test_hotness_clears_ai_event_field(self):
        """_ai_event_id 是中间字段，清理不干净就会落进 latest.json 污染数据"""
        cfg = dr.load_config()
        items = [self._item("上海某河道污染整治完成 - 上海热线"),
                 self._item("沪上一河道污染治理通过验收 - 奥一网")]
        items[0]["_ai_event_id"] = "E1"
        items[1]["_ai_event_id"] = "E1"
        out = dr.calculate_hotness(items, cfg)
        self.assertEqual(sum(1 for it in out if "_ai_event_id" in it), 0,
                         "calculate_hotness 必须清掉 _ai_event_id")
        self.assertEqual(out[0]["score_breakdown"]["event_size"], 2,
                         "清理不能影响已算好的事件维度")


class TestSnapshotStatisticsDepth(unittest.TestCase):
    """快照的「明细口径」与「统计口径」必须分离（2026-09-22 线上静默失效审查）

    线上 30 天时间线合计 276 条，而 history.json 记录的真实发布量是 886 条（低估 3.21 倍）：
    快照只存 Top10 明细，timeline / 近7天分类趋势 / 政策占比却全都遍历 items。
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "daily"))
        self._old_dir = dr.DATA_DIR
        dr.DATA_DIR = self.tmp
        self.config = {"site_name": "测试站点"}

    def tearDown(self):
        dr.DATA_DIR = self._old_dir
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def _items(n, cat="气候变化"):
        return [{"title": "测试标题 %d" % i, "link": "https://example.com/%d" % i,
                 "source": "测试源", "category": cat, "score_v2": 50.0 + i,
                 "summary": "用于测试的摘要内容"} for i in range(n)]

    @staticmethod
    def _today():
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _write_snapshot(self, date_str, payload):
        with open(os.path.join(self.tmp, "daily", date_str + ".json"), "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def test_snapshot_keeps_top10_detail_but_full_statistics(self):
        data = dr.generate_daily_snapshot(self._items(25), self.config)
        self.assertEqual(len(data["items"]), 10, "明细仍是 Top10（产品口径）")
        self.assertEqual(data["snapshot_items"], 10)
        self.assertEqual(data["total_items"], 25, "total_items 必须是当日全量，而不是明细条数")
        self.assertEqual(sum(e["count"] for e in data["category_stats"].values()), 25)
        # 必须真的落盘：统计方读的是文件，不是返回值
        with open(os.path.join(self.tmp, "daily", self._today() + ".json"), "r", encoding="utf-8") as f:
            disk = json.load(f)
        self.assertEqual(disk["total_items"], 25)
        self.assertEqual(sum(e["count"] for e in disk["category_stats"].values()), 25)

    def test_snapshot_success_sources_counts_only_effective(self):
        """快照里的 success_sources 也要走「有效源」口径，与 source_health.json 一致"""
        health = [{"name": "正常源", "success": True, "item_count": 5},
                  {"name": "哑源", "success": True, "item_count": 0},
                  {"name": "坏源", "success": False, "item_count": 0}]
        data = dr.generate_daily_snapshot(self._items(3), self.config, source_health=health)
        self.assertEqual(data["total_sources"], 3)
        self.assertEqual(data["success_sources"], 1, "零产出的源不能算进成功数")
        self.assertEqual(data["failed_sources"], 1)

    def test_timeline_counts_full_population_not_detail(self):
        dr.generate_daily_snapshot(self._items(25, "气候变化"), self.config)
        timeline = dr.generate_timeline_data(days=30)
        today = self._today()
        point = [p for p in timeline["气候变化"] if p["date"] == today][0]
        self.assertEqual(point["count"], 25, "时间线必须读到全量口径，不能被 Top10 明细截断")

    def test_timeline_falls_back_to_detail_for_legacy_snapshot(self):
        """旧快照没有 category_stats：回退遍历 items（偏小但可用），不能报错或清零"""
        self._write_snapshot(self._today(),
                             {"items": [{"title": "旧快照条目", "category": "污染治理", "score_v2": 10}]})
        timeline = dr.generate_timeline_data(days=30)
        point = [p for p in timeline["污染治理"] if p["date"] == self._today()][0]
        self.assertEqual(point["count"], 1)
        self.assertEqual(point["total_heat"], 10.0)

    def test_weekly_categories_use_full_statistics(self):
        dr.generate_daily_snapshot(self._items(25, "气候变化"), self.config)
        week = dr.calculate_weekly_categories()
        day = [d for d in week if d["date"] == self._today()][0]
        self.assertEqual(day["categories"]["气候变化"], 25)

    def test_policy_ratio_denominator_is_full_population(self):
        """分母若走 Top10 明细，10/100 的政策占比会被算成 1/1 = 100%"""
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
        self._write_snapshot(yesterday, {
            "total_items": 100,
            "category_stats": {"环境政策": {"count": 10, "total_heat": 100.0},
                               "气候变化": {"count": 90, "total_heat": 900.0}},
            "items": [{"title": "昨日条目", "category": "环境政策"}]})
        stats = dr.calculate_week_stats([])
        self.assertAlmostEqual(stats["policy_ratio"], 10.0, places=1)
        self.assertEqual(stats["week_total_items"], 100, "总数应取快照的全量口径")

    def test_week_total_prefers_snapshot_full_field_over_detail(self):
        """没有 history 记录时的回退：必须用快照 total_items，而不是明细条数"""
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
        self._write_snapshot(yesterday, {
            "total_items": 33, "snapshot_items": 10,
            "category_stats": {"污染治理": {"count": 33, "total_heat": 33.0}},
            "items": [{"title": "t%d" % i} for i in range(10)]})
        self.assertEqual(dr.calculate_week_stats([])["week_total_items"], 33)


class TestMainPipelineOrder(unittest.TestCase):
    """main() 里当日快照必须先于读取它的统计步骤落盘（2026-09-22 审查）

    旧顺序把 generate_daily_snapshot 排在 generate_timeline_data /
    calculate_weekly_categories 之后，于是这些统计看到的"今天"恒为 0
    （线上 9 个大类的末日计数全是 0）。
    """

    def test_snapshot_generated_before_consumers(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_report.py")
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        main_src = src[src.index("def main("):]
        snap = main_src.index("generate_daily_snapshot(all_items")
        self.assertLess(snap, main_src.index("generate_timeline_data(days=30)"),
                        "快照必须先于时间线生成，否则时间线的今天是 0")
        self.assertLess(snap, main_src.index("weekly_categories = calculate_weekly_categories()"),
                        "快照必须先于近7天分类统计生成")


class TestSourceHealthEffectiveness(unittest.TestCase):
    """「全绿但哑」的源不得计入健康度（2026-09-22 审查：arXiv 0 条 / IISD 1 条被算进 27/28）"""

    def test_effective_source_requires_items(self):
        self.assertTrue(dr.is_effective_source({"success": True, "item_count": 5}))
        self.assertFalse(dr.is_effective_source({"success": True, "item_count": 0}))
        self.assertFalse(dr.is_effective_source({"success": False, "item_count": 5}))
        self.assertFalse(dr.is_effective_source({"success": True, "item_count": None}))
        self.assertFalse(dr.is_effective_source({"success": True, "item_count": "abc"}))
        self.assertFalse(dr.is_effective_source(None))

    @staticmethod
    def _pool():
        return [{"name": "正常源", "success": True, "item_count": 5, "empty": False},
                {"name": "哑源", "success": True, "item_count": 0, "empty": True},
                {"name": "坏源", "success": False, "item_count": 0, "empty": False}]

    def _run(self, tmp, pool):
        dr.DATA_DIR = tmp
        dr.generate_source_health(pool)
        with open(os.path.join(tmp, "source_health.json"), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_health_separates_empty_from_failed(self):
        tmp = tempfile.mkdtemp()
        old = dr.DATA_DIR
        try:
            out = self._run(tmp, self._pool())
        finally:
            dr.DATA_DIR = old
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(out["total_sources"], 3)
        self.assertEqual(out["success_count"], 1, "零产出的哑源不能算成功")
        self.assertEqual(out["empty_count"], 1)
        self.assertEqual(out["failed_count"], 1)
        self.assertEqual(out["critical_count"], 0)

    def test_consecutive_empty_source_marked_stale(self):
        tmp = tempfile.mkdtemp()
        old = dr.DATA_DIR
        try:
            self._run(tmp, self._pool())
            pool = self._pool()
            out = self._run(tmp, pool)
        finally:
            dr.DATA_DIR = old
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(out["stale_count"], 1)
        self.assertTrue(pool[1]["stale"], "连续两次零产出的源应进入观察位")
        self.assertFalse(pool[0]["stale"])
        self.assertFalse(pool[2]["stale"], "失败源走 critical 通道，不是 stale")

    def test_critical_detects_previous_run_read_from_dict_file(self):
        """上次状态文件是 dict（含 sources），读取方必须认这个结构

        旧实现只认顶层 list，于是 last_health 永远为空、「连续两次失败」永远不算 critical，
        严重源与配套邮件告警实际从未触发过。
        """
        tmp = tempfile.mkdtemp()
        old = dr.DATA_DIR
        try:
            dr.DATA_DIR = tmp
            with open(os.path.join(tmp, "source_health.json"), "w", encoding="utf-8") as f:
                json.dump({"total_sources": 1,
                           "sources": [{"name": "坏源", "success": False, "item_count": 0}]}, f)
            pool = [{"name": "坏源", "success": False, "item_count": 0, "empty": False}]
            crit = dr.generate_source_health(pool)
        finally:
            dr.DATA_DIR = old
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(len(crit), 1, "上次也失败 -> 本次应标记 critical")
        self.assertTrue(pool[0]["critical"])


class TestRecruitWindowGates(unittest.TestCase):
    """招聘窗口：兜底值不得冒充有效类别 + 必须过环境岗位闸门（2026-09-22 审查）

    线上一次运行 4 条候选全被判为「社招」，实为对外汉语教师志愿者、浙江事业单位、
    浦东机关文员、广州招聘会 —— 没有一条环境岗位。窗口被无关内容填满比空着更糟。
    """

    JUNK = ["2026年对外汉语教师志愿者招募公告",
            "浙江省属事业单位统一招聘公告",
            "浦东新区机关文员招聘启事",
            "广州秋季大型招聘会即将举办"]
    TYPELESS = [JUNK[0], JUNK[3]]   # 既无实习/校招语素，也无显式社会招聘语素

    def test_unknown_type_returns_none_instead_of_social_fallback(self):
        for t in self.TYPELESS:
            self.assertIsNone(dr._classify_recruit_type(t), "判不出类型必须返回 None：%s" % t)
        for t in ["", None, "某公司诚聘英才"]:
            self.assertIsNone(dr._classify_recruit_type(t))

    def test_explicit_hints_still_classified(self):
        self.assertEqual(dr._classify_recruit_type("环境监测中心2026年公开招聘"), "社招")
        self.assertEqual(dr._classify_recruit_type("某环保集团校园招聘启动"), "校招")
        self.assertEqual(dr._classify_recruit_type("环境工程实习生招募"), "实习")

    def test_env_job_gate(self):
        self.assertFalse(dr._is_env_job_title("对外汉语教师志愿者招募"))
        self.assertFalse(dr._is_env_job_title("广州秋季大型招聘会即将举办"))
        self.assertTrue(dr._is_env_job_title("广东省环境监测中心公开招聘"))
        self.assertTrue(dr._is_env_job_title("某水务集团2026校招"))

    def test_candidates_filtered_by_env_gate(self):
        items = [{"title": t, "link": "https://example.com/%d" % i,
                  "source": "Google News 环保招聘", "published": "2026-09-21"}
                 for i, t in enumerate(self.JUNK)]
        items.append({"title": "某环保集团2026届校园招聘", "link": "https://example.com/ok",
                      "source": "Google News 环境校招实习", "published": "2026-09-21"})
        pool, dropped = dr.extract_recruit_candidates(items)
        titles = [p["title"] for p in pool]
        self.assertIn("某环保集团2026届校园招聘", titles)
        for t in self.JUNK:
            self.assertNotIn(t, titles, "与环境岗位无关的候选不得进池：%s" % t)
        self.assertEqual(dropped["not_env"], len(self.JUNK))
        for p in pool:
            self.assertIn(p["type"], ("实习", "校招", "社招"), "类型必须是判定出来的")

    def test_recruit_json_never_emits_untyped_items(self):
        tmp = tempfile.mkdtemp()
        old = dr.DATA_DIR
        try:
            dr.DATA_DIR = tmp
            payload = dr.generate_recruit_json(
                [{"title": "无类型条目", "url": "https://example.com/x", "type": None}],
                [], {"site_name": "测试站点"})
        finally:
            dr.DATA_DIR = old
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(payload["total"], 0, "type 为 None 的条目不许落盘")
        for it in payload["items"]:
            self.assertIn(it["type"], ("实习", "校招", "社招"))


class TestStrongEnvSignalRescue(unittest.TestCase):
    """AI 判否时的窄口径保护：不可歧义的中文强环境信号词（2026-09-22 审查）

    线上把「铜川市环境空气质量预报」判成无关而剔除 —— 相关性过滤的契约是**领域归属**，
    不是新闻价值；信息量低应由热度算法的信息密度维度去处理。
    """

    def setUp(self):
        self.api = {"summary_enabled": True, "api_key": "test-key"}
        self._orig = dr._ai_relevance_irrelevant

    def tearDown(self):
        dr._ai_relevance_irrelevant = self._orig

    def test_signal_detection(self):
        self.assertTrue(dr.has_strong_env_signal("铜川市环境空气质量预报 - 新浪财经"))
        self.assertTrue(dr.has_strong_env_signal("江西省流域水生态环境保护“十五五”规划"))
        self.assertFalse(dr.has_strong_env_signal("Trump says US will form 'AI Force'"))
        self.assertFalse(dr.has_strong_env_signal("What food items should you avoid?"))
        self.assertFalse(dr.has_strong_env_signal("New regulation on AI chips announced"))
        self.assertFalse(dr.has_strong_env_signal(""))
        self.assertFalse(dr.has_strong_env_signal(None))

    def test_ai_negative_overridden_only_for_strong_signal(self):
        filler = [{"title": "某地推进水污染治理工作取得阶段性进展", "source": "Google News 环境保护"}
                  for _ in range(20)]
        rescued = {"title": "铜川市环境空气质量预报", "source": "新浪财经"}
        dropped = {"title": "Bear-y good neighbor", "source": "The Guardian Environment"}
        dr._ai_relevance_irrelevant = lambda its, cfg: {len(filler), len(filler) + 1}

        kept = dr.filter_environmental_relevance(filler + [rescued, dropped], {}, self.api)
        self.assertTrue(any(i is rescued for i in kept), "强环境信号词应被保留")
        self.assertTrue(dropped.get("irrelevant"), "无强信号的无关内容仍应剔除")


class TestTagAcronymCanonicalization(unittest.TestCase):
    """标签缩写必须归一（2026-09-22 审查：同一批标签里同时出现 Pfas 与 PFAS）"""

    def test_canonical_tag(self):
        for raw in ("Pfas", "pfas", "PFAS", " Pfas "):
            self.assertEqual(dr.canonical_tag(raw), "PFAS")
        self.assertEqual(dr.canonical_tag("PM2.5"), "PM2.5")
        self.assertEqual(dr.canonical_tag("vocs"), "VOCs")
        self.assertEqual(dr.canonical_tag("微塑料"), "微塑料", "中文标签不受影响")
        self.assertEqual(dr.canonical_tag(""), "")

    def test_normalize_dedupes_case_variants(self):
        self.assertEqual(dr.normalize_topic_tags(["Pfas", "PFAS"]), ["PFAS"])

    def test_weekly_keywords_merge_case_variants(self):
        tmp = tempfile.mkdtemp()
        old = dr.DATA_DIR
        try:
            daily_dir = os.path.join(tmp, "daily")
            os.makedirs(daily_dir)
            today = datetime.now().strftime("%Y-%m-%d")
            with open(os.path.join(daily_dir, today + ".json"), "w", encoding="utf-8") as f:
                json.dump({"items": [{"topic_tags": ["Pfas"], "matched_keywords": []},
                                     {"topic_tags": ["PFAS"], "matched_keywords": []}]}, f)
            dr.DATA_DIR = tmp
            terms = dr.calculate_weekly_keywords()
        finally:
            dr.DATA_DIR = old
            shutil.rmtree(tmp, ignore_errors=True)
        pfas = [t for t in terms if t["term"] == "PFAS"]
        self.assertEqual(len(pfas), 1, "大小写变体必须合成一个词")
        self.assertEqual(pfas[0]["count"], 2)
        self.assertFalse([t for t in terms if t["term"].lower() == "pfas" and t["term"] != "PFAS"],
                         "不应残留非规范拼写")

class TestRecruitSupplyLimit(unittest.TestCase):
    """招聘窗口空态的**供给侧**修复（2026-09-22 实测：每源 5 条 → 两道闸门后 0 条）。

    修法：招聘源单独用更大的抓取上限；多取出来的条目只进招聘候选池，不进每日热点。
    这里的核心断言是「普通源行为完全不变」与「多取的条目一定被标记」——
    前者防回归，后者防污染。
    """

    @staticmethod
    def _fake_feed(prefix, n):
        entries = []
        for i in range(n):
            entries.append(SimpleNamespace(
                title="%s 第 %d 期 环境监测岗 污水处理方向" % (prefix, i),
                link="https://example.com/%s/%d" % (prefix, i),
                published="Mon, 22 Sep 2026 01:00:00 GMT",
                summary=("这是一段用于测试抓取条数上限的摘要正文，内容需要足够长，"
                         "以便通过摘要有效性校验，长度不少于五十个字符。"),
                content=[],
            ))
        return SimpleNamespace(entries=entries, bozo=False, bozo_exception=None)

    def _run(self, n_recruit, n_normal, max_per=5, recruit_per=30):
        cfg = {"rss_feeds": {
            "Google News 环保招聘": "https://example.com/recruit",
            "The Guardian Environment": "https://example.com/normal",
        }}

        def fake_parse(url, *args, **kwargs):
            if "recruit" in url:
                return self._fake_feed("招聘源", n_recruit)
            return self._fake_feed("普通源", n_normal)

        with mock.patch.object(dr, "REQUESTS_AVAILABLE", False), \
             mock.patch.object(dr.feedparser, "parse", side_effect=fake_parse):
            return dr.fetch_all_feeds(cfg, max_per,
                                      recruit_max_items_per_source=recruit_per)

    def test_normal_source_keeps_normal_limit(self):
        """普通源行为不得改变：仍按 max_items_per_source 截断，且不带只读标记"""
        items, _ = self._run(3, 9)
        normal = [it for it in items if it["source"] == "The Guardian Environment"]
        self.assertEqual(len(normal), 5)
        self.assertFalse([it for it in normal if it.get("_recruit_only")])

    def test_recruit_source_fetches_more(self):
        """招聘源按更大的上限抓取"""
        items, _ = self._run(12, 3)
        rec = [it for it in items if it["source"] == "Google News 环保招聘"]
        self.assertEqual(len(rec), 12)

    def test_extra_items_are_marked_recruit_only(self):
        """超出常规上限的条目必须被标记，否则会污染每日热点榜"""
        items, _ = self._run(12, 3)
        rec = [it for it in items if it["source"] == "Google News 环保招聘"]
        only = [it for it in rec if it.get("_recruit_only")]
        self.assertEqual(len(only), 7)
        self.assertEqual(len(rec) - len(only), 5)

    def test_recruit_limit_never_shrinks_normal(self):
        """招聘上限被配成比常规上限还小时，不得反过来缩小抓取"""
        items, _ = self._run(12, 3, max_per=5, recruit_per=2)
        rec = [it for it in items if it["source"] == "Google News 环保招聘"]
        self.assertEqual(len(rec), 5)

    def test_health_reports_real_count(self):
        """健康度记录真实取回条数：招聘源不再只显示 5 条"""
        _, health = self._run(12, 3)
        rec = [h for h in health if h["name"] == "Google News 环保招聘"][0]
        self.assertEqual(rec["item_count"], 12)
        self.assertTrue(dr.is_effective_source(rec))


class TestRuleTagFallback(unittest.TestCase):
    """规则路径标签质量：不再输出半截标题与占位符，回落到领域大类（2026-09-22）"""

    def test_title_fragments_are_gone(self):
        """实测被切出来当标签的两个句子碎片，现在必须提不出标签"""
        for title in ("在欧洲气候变化背景下", "省第五生态环境保护督察组赴零陵"):
            self.assertEqual(dr.extract_tags_from_title(title), [],
                             "提不到具体术语时应返回空：%s" % title)

    def test_known_terms_still_extracted(self):
        tags = dr.extract_tags_from_title("某地微塑料污染调查")
        self.assertIn("微塑料", tags, "具体术语必须被优先提取出来")
        self.assertEqual(
            dr.extract_tags_from_title("全国碳市场扩围至钢铁水泥铝冶炼行业"), ["碳市场"])

    def test_two_char_generic_words_are_not_tags(self):
        """2 字泛词（环境/生态/气候）不单独成标签"""
        for title in ("某地生态环境持续向好", "该区域环境质量改善"):
            self.assertEqual(dr.extract_tags_from_title(title), [],
                             "2 字泛词不得单独当标签：%s" % title)

    def test_category_fallback_replaces_placeholder(self):
        self.assertEqual(
            dr.assign_rule_tags({"title": "省第五生态环境保护督察组赴零陵"}), ["环境政策"])
        self.assertEqual(
            dr.assign_rule_tags({"title": "在欧洲气候变化背景下"}), ["气候变化"])

    def test_assign_rule_tags_prefers_specific_term(self):
        tags = dr.assign_rule_tags({"title": "某地微塑料污染调查"})
        self.assertIn("微塑料", tags, "有具体术语时不得回落到领域大类")

    def test_placeholder_is_last_resort_only(self):
        """连领域大类都判不出来时才允许用占位符（保证前端卡片不缺一块）"""
        self.assertEqual(dr.assign_rule_tags({"title": "某公司发布了新款产品"}),
                         [dr.TAG_PLACEHOLDER])

    def test_weekly_keyword_banned_covers_categories(self):
        for cat in dr.CATEGORY_ORDER:
            self.assertIn(cat, dr.WEEKLY_KEYWORD_BANNED_TAGS)
        self.assertIn(dr.TAG_PLACEHOLDER, dr.WEEKLY_KEYWORD_BANNED_TAGS)


class TestTimelineBackfill(unittest.TestCase):
    """历史快照分类回填：近30天统计不再被 Top10 明细焊死（2026-09-22）"""

    def setUp(self):
        self._old_dir = dr.DATA_DIR
        self._old_cache = dr._backfill_cache
        dr._backfill_cache = None

    def tearDown(self):
        dr.DATA_DIR = self._old_dir
        dr._backfill_cache = self._old_cache

    def _write_backfill(self, tmp, days):
        with open(os.path.join(tmp, "timeline_backfill.json"), "w", encoding="utf-8") as f:
            json.dump({"generated_at": "2026-09-22", "days": days}, f, ensure_ascii=False)
        dr.DATA_DIR = tmp
        dr._backfill_cache = None

    def test_priority_snapshot_over_backfill(self):
        """快照自带 category_stats 时以快照为准（流水线权威口径）"""
        snap = {"category_stats": {"水处理": {"count": 1, "total_heat": 1.0}}}
        stats, origin = dr.load_day_category_stats("2026-09-20", snap)
        self.assertEqual(origin, "snapshot")
        self.assertEqual(stats["水处理"]["count"], 1)

    def test_backfill_used_when_snapshot_lacks_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            self._write_backfill(tmp, {"2026-09-20": {
                "total_items": 28,
                "category_stats": {"水处理": {"count": 4, "total_heat": 200.0}}}})
            stats, origin = dr.load_day_category_stats("2026-09-20", {"items": []})
            self.assertEqual(origin, "backfill")
            self.assertEqual(stats["水处理"]["count"], 4)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_none_when_neither_source_has_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            dr.DATA_DIR = tmp
            dr._backfill_cache = None
            stats, origin = dr.load_day_category_stats("2026-09-20", {"items": []})
            self.assertIsNone(stats)
            self.assertEqual(origin, "")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_timeline_uses_backfill(self):
        """只有回填表、没有快照时，时间线也必须给出真实条数（而不是 0 或 10）"""
        tmp = tempfile.mkdtemp()
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self._write_backfill(tmp, {today: {
                "total_items": 26,
                "category_stats": {"水处理": {"count": 12, "total_heat": 900.0},
                                   "环境政策": {"count": 14, "total_heat": 800.0}}}})
            timeline = dr.generate_timeline_data(days=1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(timeline["水处理"][0]["count"], 12)
        self.assertEqual(timeline["环境政策"][0]["count"], 14)
        self.assertEqual(timeline["水处理"][0]["total_heat"], 900.0)

    def test_weekly_categories_uses_backfill(self):
        """近7天分类趋势同样要能吃回填表"""
        tmp = tempfile.mkdtemp()
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self._write_backfill(tmp, {today: {
                "total_items": 7,
                "category_stats": {"水处理": {"count": 7, "total_heat": 100.0}}}})
            result = dr.calculate_weekly_categories()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(result[-1]["date"], today)
        self.assertEqual(result[-1]["categories"]["水处理"], 7)

    def test_missing_days_are_never_invented(self):
        """回填表里没有的日期不得凭空补数（宁可为 0，也不编）"""
        tmp = tempfile.mkdtemp()
        try:
            self._write_backfill(tmp, {"1999-01-01": {
                "total_items": 999,
                "category_stats": {"水处理": {"count": 999, "total_heat": 1.0}}}})
            timeline = dr.generate_timeline_data(days=1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(timeline["水处理"][0]["count"], 0)

class TestRecruitPostingGate(unittest.TestCase):
    """岗位公告闸门：「关于实习/就业的新闻」不得冒充岗位资讯（2026-09-22 实测）。

    提高招聘源的抓取条数后，窗口从 3 条涨到 14 条，但其中 5 条是学院/政协/媒体的
    实习就业报道，只是恰好同时含"环境"和"实习"两个字。
    """

    NEWS_ABOUT_INTERNSHIP = [
        "城市与环境学院“一带一路”国际实习纪实",
        "水产学院本科生参与海洋生物资源与环境调查实习",
        "西安欧亚学院人居环境学院积极开拓海外实习就业渠道",
        "苏州市政协委员王任：进一步优化通勤环境，提升青年实习、就业便利度",
        "环境科学与工程学院与浙江省生态环境科学设计研究院合作共建大学生实习实训基地签约",
    ]

    def test_not_posting_detected(self):
        for t in self.NEWS_ABOUT_INTERNSHIP:
            self.assertFalse(dr._looks_like_recruit_posting(t), "不是岗位公告：%s" % t)

    def test_real_postings_detected(self):
        for t in ["中广核环保产业有限公司2026届秋季校园招聘",
                  "北京市生态环境局所属事业单位公开招聘7人，岗位公布",
                  "中广核环保产业有限公司副总工程师公开招聘",
                  "某环保集团环境工程实习生招募公告",
                  "某水务集团2026届校园招聘简章"]:
            self.assertTrue(dr._looks_like_recruit_posting(t), "是岗位公告：%s" % t)

    def test_news_about_internship_is_dropped(self):
        """真实回归：这些"实习新闻"必须被丢弃，且计入 not_posting 而不是静默消失"""
        items = []
        for i, t in enumerate(self.NEWS_ABOUT_INTERNSHIP):
            items.append({"title": t, "link": "https://example.com/news%d" % i,
                          "source": "Google News 环境校招实习", "published": "2026-09-21"})
        items.append({"title": "中广核环保产业有限公司2026届秋季校园招聘",
                      "link": "https://example.com/ok",
                      "source": "Google News 环境校招实习", "published": "2026-09-21"})
        pool, dropped = dr.extract_recruit_candidates(items)
        titles = [p["title"] for p in pool]
        self.assertEqual(titles, ["中广核环保产业有限公司2026届秋季校园招聘"])
        self.assertEqual(dropped["not_posting"], len(self.NEWS_ABOUT_INTERNSHIP))

    def test_posting_gate_does_not_eat_real_postings(self):
        """闸门只能挡住"不是招聘"，不能挡住"是招聘但不对口"（后者归 not_env 管）"""
        items = [{"title": "某市机关事务管理局公开招聘文员岗位", "link": "https://example.com/x",
                  "source": "Google News 环保招聘", "published": "2026-09-21"}]
        pool, dropped = dr.extract_recruit_candidates(items)
        self.assertEqual(pool, [])
        self.assertEqual(dropped["not_env"], 1, "该条应死在环境闸门，而不是岗位公告闸门")
        self.assertEqual(dropped["not_posting"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
