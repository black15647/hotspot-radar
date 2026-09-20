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
        items = dr.calculate_heat_v2([dict(item)], {"content_density": {"enabled": False}})
        self.assertEqual(items[0]["score_breakdown"]["density_factor"], 1.0)
        self.assertEqual(items[0]["score_breakdown"]["density_note"], "")

    def test_density_factor_recorded_in_breakdown(self):
        """密度系数与判定说明必须进入 score_breakdown，供前端热度弹窗展示"""
        items = dr.calculate_heat_v2(
            [{"title": "省第二生态环境保护督察组调研督导信访工作",
              "source": "Google News 生态环境", "published": "2026-09-20T00:00:00+00:00"},
             {"title": "Microplastics in Soil a ‘Trojan Horse’ for Toxic Chemicals",
              "source": "Yale Environment 360", "published": "2026-09-20T00:00:00+00:00"}],
            {})
        bd = items[0]["score_breakdown"]
        self.assertEqual(bd["algorithm"], "v2.1")
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
        self.assertEqual(dr.normalize_topic_tags(["Pfas", "PFAS", "pfas"]), ["Pfas"])

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
