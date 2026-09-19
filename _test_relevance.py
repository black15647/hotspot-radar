# -*- coding: utf-8 -*-
"""环境学子雷达 —— 开发期冒烟测试（相关性过滤 / 摘要策略）

覆盖两条容易被误判的行为：
1. 相关性过滤的兜底阈值是 daily_report.MIN_KEPT_ITEMS（=20）：保留数低于该值时会整体取消过滤。
   因此样本量必须足够大才能验证过滤真的生效，小样本只能验证兜底。
2. 摘要策略是「保证每条都有摘要」：无原文时基于标题生成规则摘要，
   见 _fallback_rule_summary 的最终校验分支。
"""
import os
import sys

# 基于脚本自身位置推导项目根目录，避免写死绝对路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_report as dr  # noqa: E402

API_OFF = {
    "summary_enabled": False, "api_key": "", "reader_enabled": False,
    "jina_key": "", "local_extraction": False, "base_url": "",
    "model": "", "max_tokens": 100,
}
API_ON = {
    "summary_enabled": True, "api_key": "dummy-key", "reader_enabled": False,
    "jina_key": "", "local_extraction": False, "base_url": "https://example.com/v1",
    "model": "m", "max_tokens": 100,
}

print("=" * 50)
print("测试1: 环境领域相关性过滤（规则降级，AI 未启用）")
print("=" * 50)
config = dr.load_config()
print("keywords 数量:", len(config.get("keywords", [])))
print("兜底阈值 MIN_KEPT_ITEMS =", dr.MIN_KEPT_ITEMS)

# 1a. 大样本：样本数远高于兜底阈值 -> 过滤必须真正生效
print("\n[1a] 大样本（30 条，含 4 条明确无关）—— 兜底不应触发")
big = [{"title": f"某地推进垃圾分类与循环经济示范城市建设第{i}期", "link": f"e{i}"}
       for i in range(26)]
big += [
    {"title": "欧盟推进碳边境调节机制，专家分析对出口影响", "link": "a"},
    {"title": "今日沪深股市收评：两市震荡整理", "link": "b"},
    {"title": "英超联赛周末战报：曼城客场取胜", "link": "c"},
    {"title": "某市发布新款手机评测：影像能力大幅提升", "link": "f"},
]
kept_big = dr.filter_environmental_relevance(big, config, API_OFF)
flagged = [i["title"] for i in big if i.get("irrelevant")]
print(f"  输入 {len(big)} 条 -> 保留 {len(kept_big)} 条，标记无关 {len(flagged)} 条")
assert len(kept_big) < len(big), "大样本下过滤应生效（保留数须少于输入数）"
assert flagged, "大样本下应有条目被标记为无关"
assert kept_big, "过滤后不应为空"
print("  [PASS] 大样本过滤生效，兜底未被误触发")

# 1b. 小样本：保留数低于阈值 -> 兜底取消过滤，保留全部并清除无关标记
print("\n[1b] 小样本（5 条）—— 兜底应触发，保留全部")
small = [
    {"title": "欧盟推进碳边境调节机制，专家分析对出口影响", "link": "a"},
    {"title": "今日沪深股市收评：两市震荡整理", "link": "b"},
    {"title": "英超联赛周末战报：曼城客场取胜", "link": "c"},
    {"title": "气候变化加剧极端天气，多国强化应对措施", "link": "d"},
    {"title": "某地推进垃圾分类与循环经济示范城市建设", "link": "e"},
]
kept_small = dr.filter_environmental_relevance(small, config, API_OFF)
print(f"  输入 {len(small)} 条 -> 保留 {len(kept_small)} 条")
assert len(kept_small) == len(small), f"小样本保留了 {len(kept_small)}/{len(small)} 条，兜底未生效"
assert not any(i.get("irrelevant") for i in small), "兜底取消过滤时应清除 irrelevant 标记"
print("  [PASS] 小样本兜底生效（保留数低于阈值则整体不过滤）")

print()
print("=" * 50)
print("测试2: 批量摘要 —— 保证每条都有摘要（无原文时基于标题生成）")
print("=" * 50)
t_items = [
    {"title": "标题A：某地水污染治理新进展", "link": "x", "summary": ""},
    {"title": "标题B：可再生能源装机创新高", "link": "y",
     "summary": "这是一段足够长的有效原始摘要，用于验证已有摘要不会被重复生成，长度超过二十个字符标准。"},
    {"title": "标题C：循环经济试点", "link": "z",
     "summary": "标题C：循环经济试点"},  # 与标题相同 -> 视为无效摘要
]
dr.generate_batch_summaries(t_items, API_ON)
for it in t_items:
    print(f"  [{it['title'][:12]}] summary={it['summary'][:34]!r}")
assert t_items[1]["summary"].startswith("这是一段"), "条目1 已有有效摘要，不应被覆盖"
assert t_items[0]["summary"], "条目0 无原文也应产出摘要（不得为空）"
assert t_items[0]["summary"] != "标题A：某地水污染治理新进展", "条目0 摘要须经过规则加工而非原样复制标题"
assert t_items[2]["summary"], "条目2 摘要与标题相同，应重新生成而非留空"
# 规则兜底产出的摘要不得是空洞模板
for it in t_items:
    for pat in dr._BAD_SUMMARY_PATTERNS:
        assert not pat.match(it["summary"]), f"摘要命中无信息量模板：{it['summary']!r}"
print("  [PASS] 批量摘要保证每条都有有效摘要，且不含空洞模板")

print()
print("=" * 50)
print("测试3: generate_ai_summary 无原文返回空（不基于标题猜测）")
print("=" * 50)
r = dr.generate_ai_summary({"title": "无原文标题", "link": "no-link", "summary": ""}, API_ON)
print("  返回:", repr(r))
assert r == "", "无原文时 generate_ai_summary 应返回空"
print("  [PASS] generate_ai_summary 不基于标题猜测")

print()
print("全部测试通过")
