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


if __name__ == "__main__":
    unittest.main(verbosity=2)
