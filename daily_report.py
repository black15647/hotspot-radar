#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境学子雷达 - 每日热点报告生成器
依赖安装：pip install feedparser pyyaml jieba
"""

import os
import sys
import json
import csv
import math
import re
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

try:
    import feedparser
except ImportError:
    print("[错误] 缺少依赖 feedparser，请执行：pip install feedparser pyyaml jieba")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("[错误] 缺少依赖 pyyaml，请执行：pip install feedparser pyyaml jieba")
    sys.exit(1)

# jieba 为可选依赖，未安装时跳过分词功能
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("[警告] 未安装 jieba，新词提取功能将被跳过。安装：pip install jieba")

# 中文停用词列表
STOP_WORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
    "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么",
    "如何", "为什么", "可以", "可能", "应该", "需要", "已经", "正在", "将", "被",
    "把", "让", "使", "从", "向", "对", "与", "及", "或", "但", "而", "且", "并",
    "还", "又", "再", "才", "只", "仅", "最", "更", "比较", "非常", "十分", "极其",
    "因为", "所以", "如果", "虽然", "但是", "然而", "因此", "于是", "从而", "进而",
    "通过", "进行", "实现", "开展", "推进", "加强", "提升", "提高", "改善", "完善",
    "建立", "建设", "构建", "营造", "打造", "形成", "成为", "作为", "属于", "关于",
    "对于", "基于", "根据", "按照", "依照", "通过", "经过", "由于", "鉴于", "关于",
    "目前", "当前", "如今", "现在", "今天", "昨天", "明天", "今年", "去年", "明年",
    "近日", "日前", "近期", "最近", "以来", "以后", "之前", "之中", "之内", "之外",
    "以上", "以下", "以内", "以外", "以前", "以后", "以上", "以下", "之一", "之一",
    "等", "等等", "之类", "等等", "什么的", "的话", "的话", "呢", "吧", "啊", "呀",
    "哦", "嗯", "哈", "嘿", "哎", "唉", "喂", "嗯", "的话", "的话", "这个", "那个",
    "这些", "那些", "这样", "那样", "这么", "那么", "这里", "那里", "此处", "彼处",
    "该", "此", "其", "之", "乎", "者", "也", "矣", "焉", "哉", "乎", "尔", "汝",
    "若", "如", "似", "像", "同", "跟", "和", "与", "及", "或", "或者", "还是",
    "要么", "与其", "不如", "宁可", "也不", "即使", "就算", "哪怕", "任凭", "无论",
    "不管", "不论", "凡是", "所有", "一切", "全部", "整个", "整体", "总体", "总共",
    "合计", "共计", "约", "大约", "大概", "大致", "差不多", "几乎", "将近", "接近",
    "左右", "上下", "前后", "早晚", "迟早", "早晚", "终于", "最终", "最后", "起初",
    "开始", "结束", "停止", "继续", "持续", "不断", "一直", "始终", "永远", "永久",
    "长期", "短期", "近期", "远期", "中期", "周期", "期间", "时期", "时代", "时间",
    "时候", "时刻", "时分", "时候", "功夫", "工夫", "精力", "精神", "力量", "力气",
    "能力", "本事", "本领", "才华", "才能", "才智", "智谋", "智慧", "智力", "智商",
    "情商", "胆商", "逆商", "财商", "健商", "心商", "灵商", "德商", "志商", "健商",
])

# ============================================================
# 常量与默认配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

DEFAULT_KEYWORDS = [
    "气候变化", "碳中和", "碳排放", "水污染", "大气污染", "土壤污染",
    "微塑料", "新污染物", "重金属", "生物多样性", "生态修复", "生态系统",
    "可再生能源", "清洁能源", "循环经济", "环保督察", "环评", "绿色金融",
    "可持续发展", "环境健康", "垃圾分类", "塑料污染", "海洋保护",
    "考研", "招聘", "实习", "竞赛", "水处理", "土壤修复",
    "环境工程", "环境科学"
]

DEFAULT_SOURCE_WEIGHTS = {
    "Nature": 2.0,
    "Nature Sustainability": 2.0,
    "Nature 环境科学": 2.0,
    "Google News 环境保护": 1.5,
    "Google News 气候变化": 1.5,
    "Google News 生态环境": 1.5,
    "Google News 环境污染": 1.5,
    "Google News 环保招聘": 1.5,
    "Google News 环境考研": 1.5,
    "Google News 环境竞赛": 1.5,
}

DEFAULT_RSS_FEEDS = {
    "Google News 环境保护": "https://news.google.com/rss/search?q=环境保护&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 气候变化": "https://news.google.com/rss/search?q=气候变化&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 生态环境": "https://news.google.com/rss/search?q=生态环境&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 环境污染": "https://news.google.com/rss/search?q=环境污染&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 环保招聘": "https://news.google.com/rss/search?q=环保招聘&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 环境考研": "https://news.google.com/rss/search?q=环境考研&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "Google News 环境竞赛": "https://news.google.com/rss/search?q=环境竞赛&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "The Guardian Environment": "https://www.theguardian.com/environment/rss",
    "Yale Environment 360": "https://e360.yale.edu/feed.xml",
    "BBC 科学与环境": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "Nature": "https://rsshub.app/nature/research",
    "Nature Sustainability": "https://rsshub.app/nature/natsustain",
    "Nature 环境科学": "https://www.nature.com/subjects/environmental-sciences.rss",
    "Water Research": "https://rss.sciencedirect.com/publication/science/00431354",
    "ScienceDaily 环境科学": "https://www.sciencedaily.com/rss/earth_climate/environmental_science.xml",
}

DEFAULT_CONFIG = {
    "site_name": "环境学子雷达",
    "rss_feeds": DEFAULT_RSS_FEEDS,
    "keywords": DEFAULT_KEYWORDS,
    "user_keywords": [],
    "weights": {
        "source_weights": DEFAULT_SOURCE_WEIGHTS,
        "time_decay": 0.8,
        "keyword_bonus": 2.0,
    },
    "email_config": {
        "smtp_server": "",
        "smtp_port": 465,
        "sender": "",
        "password": "",
        "receiver": "",
    },
    "max_items_per_source": 5,
    "max_total_items": 50,
}


# ============================================================
# 工具函数
# ============================================================

def ensure_data_dir():
    """确保 data 目录及子目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "daily"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "archive"), exist_ok=True)


def safe_json_dump(data, path, ensure_ascii=False, indent=2):
    """
    安全写入 JSON 文件：
    1. 使用 json.dump 序列化（自动转义特殊字符）
    2. 写入后重新读取验证合法性
    3. 验证失败时抛出异常，避免生成损坏的 JSON
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
    # 写入后验证
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        print(f"[警告] JSON 验证失败 {path}: {e}")
        raise


def sanitize_str(value, default=""):
    """确保值为字符串，None 转为默认值"""
    if value is None:
        return default
    return str(value)


def load_config():
    """读取配置文件，不存在则创建默认配置"""
    if not os.path.exists(CONFIG_PATH):
        print(f"[信息] 未找到配置文件，正在创建默认配置：{CONFIG_PATH}")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    # 合并默认配置
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    # 合并 weights
    if "weights" in user_config and isinstance(user_config["weights"], dict):
        config["weights"] = {**DEFAULT_CONFIG["weights"], **user_config["weights"]}
        if "source_weights" in user_config["weights"] and isinstance(user_config["weights"]["source_weights"], dict):
            config["weights"]["source_weights"] = {**DEFAULT_SOURCE_WEIGHTS, **user_config["weights"]["source_weights"]}

    # 合并 email_config
    if "email_config" in user_config and isinstance(user_config["email_config"], dict):
        config["email_config"] = {**DEFAULT_CONFIG["email_config"], **user_config["email_config"]}

    # 确保 keywords 不为空
    if not config.get("keywords"):
        config["keywords"] = DEFAULT_KEYWORDS

    # 确保 rss_feeds 不为空
    if not config.get("rss_feeds"):
        config["rss_feeds"] = DEFAULT_RSS_FEEDS

    return config


def parse_published_time(entry):
    """解析条目的发布时间，返回 datetime 对象（UTC）"""
    time_struct = None
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        if hasattr(entry, attr) and getattr(entry, attr):
            time_struct = getattr(entry, attr)
            break

    if time_struct:
        try:
            return datetime(*time_struct[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    # 尝试解析字符串
    for attr in ("published", "updated", "created"):
        val = getattr(entry, attr, None)
        if val:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

    return None


def clean_html(text):
    """清理 HTML 标签，返回纯文本"""
    if not text:
        return ""
    # 移除 script 和 style 内容
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 解码 HTML 实体
    import html as html_module
    text = html_module.unescape(text)
    # 合并空白
    text = re.sub(r"\s+", " ", text).strip()
    return text


# 常见元数据行前缀（不区分大小写）
_METADATA_PREFIXES = [
    r"publication date", r"source", r"author", r"authors", r"author\(s\)",
    r"volume", r"issue", r"pages", r"doi", r"issn", r"isbn",
    r"publisher", r"journal", r"journal name", r"article type",
    r"document type", r"language", r"copyright", r"rights",
    r"citation", r"abstract", r"keywords", r"subjects",
    r"date", r"published", r"updated", r"created",
    r"category", r"tags", r"section", r"column",
]

_METADATA_PATTERN = re.compile(
    r"^\s*(" + "|".join(_METADATA_PREFIXES) + r")\s*[:：]",
    re.IGNORECASE
)

# 元数据关键词（用于判断整段是否主要是元数据）
_METADATA_KEYWORDS = [
    "author", "authors", "volume", "issue", "pages", "doi",
    "journal", "publisher", "publication date", "issn", "isbn",
    "copyright", "document type", "article type", "citation",
]


def remove_metadata_lines(text):
    """去除以元数据前缀开头的行，返回清洗后的文本"""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _METADATA_PATTERN.match(stripped):
            continue
        cleaned_lines.append(stripped)
    return " ".join(cleaned_lines).strip()


def is_likely_metadata(text):
    """判断文本是否主要由元数据构成（连续出现多个元数据关键词）"""
    if not text:
        return True
    text_lower = text.lower()
    # 统计元数据关键词出现次数
    count = 0
    for kw in _METADATA_KEYWORDS:
        if kw in text_lower:
            count += 1
    # 如果出现3个以上元数据关键词，且文本较短，认为是元数据
    if count >= 3 and len(text) < 500:
        return True
    # 如果文本以元数据前缀开头且总长度小于100，认为是元数据
    if _METADATA_PATTERN.match(text.strip()) and len(text) < 100:
        return True
    return False


def extract_first_long_sentence(text):
    """从文本中提取第一个较长的句子（>=30字符），用于元数据混杂时提取真正摘要"""
    if not text:
        return ""
    # 按句子结束符分割
    sentences = re.split(r"(?<=[。！？.!?])\s+", text)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) >= 30:
            return sent
    # 如果没有长句子，返回第一个非空句子
    for sent in sentences:
        sent = sent.strip()
        if sent:
            return sent
    return ""


def extract_summary(entry):
    """
    提取摘要：
    1. 优先从 content 字段提取（拼接所有 value）
    2. 若 content 太短（<50字符），尝试 description
    3. 若仍太短，使用 summary
    4. 清洗 HTML、去除元数据行
    5. 若清洗后仍主要是元数据，尝试提取第一个长句子
    6. 最终摘要过短或明显是元数据则返回空字符串
    最大长度 5000 字符
    """
    MAX_LEN = 5000
    MIN_VALID_LEN = 30  # 小于此长度认为无效摘要

    # 第一步：从 content 提取
    raw_text = ""
    content = getattr(entry, "content", None)
    if content and isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("value"):
                parts.append(c["value"])
            elif hasattr(c, "value") and c.value:
                parts.append(c.value)
        if parts:
            raw_text = " ".join(parts)

    # 第二步：content 太短则尝试 description
    if len(clean_html(raw_text)) < 50:
        description = getattr(entry, "description", "") or ""
        if description and len(clean_html(description)) >= 50:
            raw_text = description

    # 第三步：仍太短则使用 summary
    if len(clean_html(raw_text)) < 50:
        summary = getattr(entry, "summary", "") or ""
        if summary:
            raw_text = summary

    if not raw_text:
        return ""

    # 第四步：清洗 HTML
    text = clean_html(raw_text)

    # 第五步：去除元数据行
    text = remove_metadata_lines(text)

    # 第六步：如果清洗后仍主要是元数据，尝试提取第一个长句子
    if is_likely_metadata(text):
        text = extract_first_long_sentence(text)

    # 第七步：截断到最大长度
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN].rsplit(" ", 1)[0] + "..."

    # 第八步：最终校验——过短或仍为元数据则返回空
    if len(text) < MIN_VALID_LEN or is_likely_metadata(text):
        return ""

    return text


def match_keywords(text, keywords):
    """
    在文本中匹配关键词，返回匹配到的关键词列表
    - 不区分英文大小写
    - 中文关键词：直接包含匹配
    - 英文关键词：使用单词边界匹配（避免 water 匹配 waterfall）
    """
    if not text:
        return []
    text_lower = text.lower()
    matched = []
    for kw in keywords:
        if not kw:
            continue
        kw_lower = kw.lower()
        # 判断是否为纯英文（含空格、连字符的英文短语也按英文处理）
        if re.match(r'^[a-zA-Z\s\-]+$', kw_lower):
            # 英文关键词：使用单词边界匹配
            pattern = r'\b' + re.escape(kw_lower.strip()) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(kw)
        else:
            # 中文或混合关键词：直接包含匹配（不区分大小写）
            if kw_lower in text_lower:
                matched.append(kw)
    return matched


def get_source_weight(source_name, source_weights):
    """获取来源权重"""
    return source_weights.get(source_name, 1.0)


# ============================================================
# 核心逻辑
# ============================================================

def fetch_all_feeds(config, max_items_per_source):
    """
    抓取所有 RSS 源，返回 (条目列表, 源健康度列表)
    每个源健康度记录：名称、URL、抓取时间、成功/失败、耗时、获取条数、错误信息
    """
    rss_feeds = config.get("rss_feeds", {})
    all_items = []
    source_health = []

    for source_name, url in rss_feeds.items():
        start_time = time.time()
        fetch_time = datetime.now(timezone.utc).isoformat()
        success = False
        count = 0
        error_msg = ""

        try:
            print(f"[抓取] {source_name} ...")
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                error_msg = f"解析失败：{feed.bozo_exception}"
                print(f"  [警告] {error_msg}")
            else:
                entries = feed.entries[:max_items_per_source]

                for entry in entries:
                    title = getattr(entry, "title", "").strip()
                    link = getattr(entry, "link", "").strip()

                    if not title:
                        continue

                    published = parse_published_time(entry)
                    summary = extract_summary(entry)

                    all_items.append({
                        "title": title,
                        "link": link,
                        "source": source_name,
                        "published": published.isoformat() if published else None,
                        "published_dt": published,
                        "summary": summary,
                    })
                    count += 1

                success = True
                print(f"  [成功] 获取 {count} 条")

        except Exception as e:
            error_msg = str(e)
            print(f"  [错误] 抓取失败，跳过：{e}")

        elapsed = round(time.time() - start_time, 2)
        source_health.append({
            "name": source_name,
            "url": url,
            "last_check": fetch_time,
            "success": success,
            "elapsed_seconds": elapsed,
            "item_count": count,
            "error": error_msg if not success else "",
        })

    return all_items, source_health


def deduplicate_items(items):
    """按链接去重，链接为空则按标题去重"""
    seen_links = set()
    seen_titles = set()
    unique = []

    for item in items:
        link = item.get("link", "")
        title = item.get("title", "")

        if link:
            if link in seen_links:
                continue
            seen_links.add(link)
        else:
            if title in seen_titles:
                continue
            seen_titles.add(title)

        unique.append(item)

    return unique


def filter_by_time(items, hours=48):
    """只保留最近 N 小时内的条目；发布时间缺失则按当前时间减24小时处理"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    filtered = []

    for item in items:
        published_dt = item.get("published_dt")
        if published_dt is None:
            # 发布时间缺失，按当前时间减24小时处理
            item["published_dt"] = now - timedelta(hours=24)
            item["published"] = item["published_dt"].isoformat()
            item["_time_fallback"] = True
            filtered.append(item)
        elif published_dt >= cutoff:
            filtered.append(item)

    return filtered


def calculate_hotness(items, config):
    """
    计算热度分数
    热度 = 5 + 来源权重×3 + 关键词匹配数×keyword_bonus + 主题聚合加分 + 10×exp(-hours/24)
    主题聚合加分：同一关键词在多个条目标题/摘要中出现，额外加2×包含该关键词的条目数
    """
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    weights = config.get("weights", {})
    source_weights = weights.get("source_weights", DEFAULT_SOURCE_WEIGHTS)
    keyword_bonus = weights.get("keyword_bonus", 2.0)

    now = datetime.now(timezone.utc)

    # 第一步：为每个条目匹配关键词
    for item in items:
        text = item.get("title", "") + " " + item.get("summary", "")
        item["matched_keywords"] = match_keywords(text, keywords)

    # 第二步：统计每个关键词在多少个条目中出现（用于主题聚合加分）
    keyword_item_count = defaultdict(int)
    for item in items:
        for kw in set(item["matched_keywords"]):
            keyword_item_count[kw] += 1

    # 第三步：计算每条的热度
    for item in items:
        # 基础分
        score = 5.0

        # 来源权重加分
        source_weight = get_source_weight(item.get("source", ""), source_weights)
        score += source_weight * 3

        # 关键词匹配加分
        matched = item.get("matched_keywords", [])
        score += len(matched) * keyword_bonus

        # 主题聚合加分
        aggregation_bonus = 0.0
        for kw in set(matched):
            count = keyword_item_count.get(kw, 0)
            aggregation_bonus += 2 * count
        score += aggregation_bonus

        # 时间衰减加分
        published_dt = item.get("published_dt")
        if published_dt:
            hours_ago = (now - published_dt).total_seconds() / 3600.0
            if hours_ago < 0:
                hours_ago = 0
            time_score = 10 * math.exp(-hours_ago / 24)
        else:
            time_score = 0
        score += time_score

        item["hotness"] = round(score, 2)
        item["source_weight"] = source_weight
        item["aggregation_bonus"] = round(aggregation_bonus, 2)

    return items


def sort_and_limit(items, max_total):
    """按热度从高到低排序，取前 max_total 条"""
    items.sort(key=lambda x: x.get("hotness", 0), reverse=True)
    return items[:max_total]


def generate_analysis(item, config):
    """
    为单个热点条目生成一句话分析
    示例："该条目涉及【气候变化】话题，热度主要由时间新鲜度和来源权威性驱动，建议关注。"
    """
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    matched = item.get("matched_keywords", [])

    # 选择话题：取匹配到的关键词中出现次数最多的那个
    if matched:
        topic = matched[0]  # matched_keywords 已按配置顺序，取第一个
    else:
        topic = "环境领域"

    # 分析热度驱动因素
    drivers = []
    source_weight = item.get("source_weight", 1.0)
    if source_weight >= 2.0:
        drivers.append("来源权威性")
    elif source_weight >= 1.5:
        drivers.append("来源影响力")

    published_dt = item.get("published_dt")
    if published_dt:
        hours_ago = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600.0
        if hours_ago <= 24:
            drivers.append("时间新鲜度")

    if len(matched) >= 3:
        drivers.append("主题热度")
    elif len(matched) >= 1:
        drivers.append("关键词聚焦")

    if not drivers:
        drivers.append("综合因素")

    driver_text = "和".join(drivers[:2]) if len(drivers) >= 2 else drivers[0]

    # 根据热度给出建议
    hotness = item.get("hotness", 0)
    if hotness >= 20:
        suggestion = "重点关注"
    elif hotness >= 12:
        suggestion = "建议关注"
    else:
        suggestion = "可留意"

    analysis = f"该条目涉及【{topic}】话题，热度主要由{driver_text}驱动，{suggestion}。"
    return analysis


def generate_pending_terms(items, config):
    """
    使用 jieba 分词从标题中提取候选新词，生成 pending_terms.json
    过滤掉已存在于 glossary.json 和 config keywords 中的词
    只保留出现次数 >= 2 的词
    """
    if not JIEBA_AVAILABLE:
        print("[跳过] jieba 未安装，跳过分词提取")
        path = os.path.join(DATA_DIR, "pending_terms.json")
        safe_json_dump([], path)
        return []

    # 加载已有知识库词条
    existing_terms = set()
    glossary_path = os.path.join(DATA_DIR, "glossary.json")
    if os.path.exists(glossary_path):
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                glossary = json.load(f)
                if isinstance(glossary, list):
                    for item in glossary:
                        if isinstance(item, dict) and item.get("term"):
                            existing_terms.add(item["term"].lower())
        except Exception:
            pass

    # 配置中的关键词也排除
    config_keywords = set([kw.lower() for kw in config.get("keywords", DEFAULT_KEYWORDS)])

    # 分词统计
    term_contexts = defaultdict(list)
    term_count = Counter()

    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        words = jieba.lcut(title)
        seen_in_title = set()
        for word in words:
            word = word.strip()
            # 过滤：长度 >= 2，不是停用词，不是纯数字/英文单字母
            if len(word) < 2:
                continue
            if word in STOP_WORDS:
                continue
            if re.match(r'^[\d\s\W]+$', word):
                continue
            if re.match(r'^[a-zA-Z]$', word):
                continue
            # 排除已存在于知识库或配置中的词
            word_lower = word.lower()
            if word_lower in existing_terms or word_lower in config_keywords:
                continue
            # 每个词在同一标题中只计一次
            if word not in seen_in_title:
                seen_in_title.add(word)
                term_count[word] += 1
                if len(term_contexts[word]) < 3:
                    term_contexts[word].append(title)

    # 筛选出现次数 >= 2 的词，按次数降序
    pending = []
    for term, count in term_count.most_common():
        if count >= 2:
            pending.append({
                "term": sanitize_str(term),
                "count": int(count),
                "contexts": [sanitize_str(ctx) for ctx in term_contexts[term]],
            })

    # 写入文件
    path = os.path.join(DATA_DIR, "pending_terms.json")
    safe_json_dump(pending, path)
    print(f"[生成] {path}（候选词 {len(pending)} 个）")
    return pending


# ============================================================
# 输出生成
# ============================================================

def generate_source_health(source_health):
    """
    生成 docs/data/source_health.json
    - 读取上次的源健康状态
    - 对比本次和上次，连续两次失败的源标记为 critical: true
    - 返回 critical 源列表，用于邮件通知
    """
    health_path = os.path.join(DATA_DIR, "source_health.json")

    # 读取上次状态
    last_health = {}
    if os.path.exists(health_path):
        try:
            with open(health_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data, list):
                    for item in old_data:
                        if item.get("name"):
                            last_health[item["name"]] = item
        except Exception:
            last_health = {}

    # 处理本次状态，标记连续失败
    critical_sources = []
    for src in source_health:
        name = src.get("name", "")
        last_success = last_health.get(name, {}).get("success", True)
        current_success = src.get("success", False)
        # 连续两次失败（上次失败且本次也失败）
        if not last_success and not current_success:
            src["critical"] = True
            critical_sources.append(src)
        else:
            src["critical"] = False

    # 写入文件
    output = {
        "last_update": datetime.now(timezone.utc).isoformat(),
        "total_sources": len(source_health),
        "success_count": sum(1 for s in source_health if s.get("success")),
        "failed_count": sum(1 for s in source_health if not s.get("success")),
        "critical_count": len(critical_sources),
        "sources": source_health,
    }
    safe_json_dump(output, health_path)
    print(f"[源健康] 成功 {output['success_count']}/{output['total_sources']}，失败 {output['failed_count']}，严重 {output['critical_count']}")
    return critical_sources


def generate_latest_json(items, config):
    """生成 data/latest.json"""
    site_name = config.get("site_name", "环境学子雷达")
    keywords = config.get("keywords", DEFAULT_KEYWORDS)

    # 关键词分析（前10）
    all_keywords = []
    for item in items:
        all_keywords.extend(item.get("matched_keywords", []))
    keyword_counter = Counter(all_keywords)
    top_keywords = [{"keyword": kw, "count": cnt} for kw, cnt in keyword_counter.most_common(10)]

    # 热点总结
    if top_keywords:
        top5 = "、".join([k["keyword"] for k in top_keywords[:5]])
        summary = f"今日热点围绕{top5}等话题，共聚合{len(items)}条资讯。"
    else:
        summary = f"今日共聚合{len(items)}条资讯。"

    # 构建条目列表（移除内部字段，确保所有值为可序列化的基本类型）
    output_items = []
    for item in items:
        # 生成分析
        analysis = generate_analysis(item, config)
        item["analysis"] = analysis
        output_items.append({
            "title": sanitize_str(item.get("title")),
            "link": sanitize_str(item.get("link")),
            "source": sanitize_str(item.get("source")),
            "published": sanitize_str(item.get("published")),
            "hotness": float(item.get("hotness", 0)),
            "summary": sanitize_str(item.get("summary")),
            "analysis": sanitize_str(analysis),
            "matched_keywords": [sanitize_str(kw) for kw in item.get("matched_keywords", [])],
        })

    data = {
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "site_name": sanitize_str(site_name),
        "total_items": len(output_items),
        "items": output_items,
        "keyword_analysis": top_keywords,
        "hot_summary": sanitize_str(summary),
    }

    path = os.path.join(DATA_DIR, "latest.json")
    safe_json_dump(data, path)
    print(f"[生成] {path}（{len(output_items)} 条）")
    return data


def generate_daily_snapshot(items, config):
    """
    生成每日数据快照文件 docs/data/daily/YYYY-MM-DD.json
    包含当日 Top10 条目列表，覆盖写入
    """
    site_name = config.get("site_name", "环境学子雷达")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 取 Top10
    top10 = items[:10]
    output_items = []
    for item in top10:
        output_items.append({
            "title": sanitize_str(item.get("title")),
            "link": sanitize_str(item.get("link")),
            "source": sanitize_str(item.get("source")),
            "published": sanitize_str(item.get("published")),
            "hotness": float(item.get("hotness", 0)),
            "summary": sanitize_str(item.get("summary")),
            "analysis": sanitize_str(item.get("analysis", "")),
            "matched_keywords": [sanitize_str(kw) for kw in item.get("matched_keywords", [])],
        })

    data = {
        "report_date": today,
        "site_name": sanitize_str(site_name),
        "total_items": len(output_items),
        "items": output_items,
    }

    daily_dir = os.path.join(DATA_DIR, "daily")
    path = os.path.join(daily_dir, f"{today}.json")
    safe_json_dump(data, path)
    print(f"[生成] {path}（Top {len(output_items)}）")
    return data


def generate_monthly_archive(items, config):
    """
    生成/更新月度归档文件 docs/data/archive/YYYY-MM.json
    包含该月内每天的摘要信息（日期、总条目数、前5关键词）
    按日期去重更新
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    year_month = today[:7]  # YYYY-MM

    # 统计今日关键词
    all_keywords = []
    for item in items:
        all_keywords.extend(item.get("matched_keywords", []))
    top5 = [kw for kw, _ in Counter(all_keywords).most_common(5)]

    today_record = {
        "date": today,
        "total_items": len(items),
        "keywords": [sanitize_str(kw) for kw in top5],
    }

    archive_dir = os.path.join(DATA_DIR, "archive")
    path = os.path.join(archive_dir, f"{year_month}.json")

    # 读取已有归档（如果存在）
    archive_data = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if isinstance(existing, list):
                    archive_data = existing
        except Exception:
            archive_data = []

    # 按日期去重更新
    archive_data = [r for r in archive_data if r.get("date") != today]
    archive_data.append(today_record)

    # 按日期排序
    archive_data.sort(key=lambda x: x.get("date", ""))

    safe_json_dump(archive_data, path)
    print(f"[更新] {path}（本月共 {len(archive_data)} 天记录）")
    return archive_data


def generate_daily_report_md(items, config):
    """生成 data/daily_report.md（仅Top10）"""
    site_name = config.get("site_name", "环境学子雷达")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# {site_name} - 每日热点报告")
    lines.append(f"")
    lines.append(f"**日期**：{today}")
    lines.append(f"**总条目数**：{len(items)}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 🔥 今日热点 TOP 10")
    lines.append(f"")

    top10 = items[:10]
    for i, item in enumerate(top10, 1):
        title = item.get("title", "无标题")
        link = item.get("link", "#")
        source = item.get("source", "未知来源")
        hotness = item.get("hotness", 0)
        published = item.get("published", "")
        summary = item.get("summary", "")
        keywords = item.get("matched_keywords", [])

        lines.append(f"### {i}. [{title}]({link})")
        lines.append(f"")
        lines.append(f"- **来源**：{source}")
        lines.append(f"- **热度**：{hotness}")
        if published:
            lines.append(f"- **发布时间**：{published}")
        if keywords:
            lines.append(f"- **关键词**：{', '.join(keywords)}")
        lines.append(f"")
        if summary:
            lines.append(f"> {summary}")
            lines.append(f"")
        analysis = item.get("analysis", "")
        if analysis:
            lines.append(f"**📊 分析**：{analysis}")
            lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    path = os.path.join(DATA_DIR, "daily_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[生成] {path}（Top 10）")
    return path


def load_history():
    """加载历史记录"""
    path = os.path.join(DATA_DIR, "history.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_history(history):
    """保存历史记录"""
    path = os.path.join(DATA_DIR, "history.json")
    safe_json_dump(history, path)
    print(f"[更新] {path}（共 {len(history)} 条记录）")


def update_history(items, config, backfill=False):
    """
    更新 history.json
    - 冷启动：按条目发布日期分组生成最近7天记录
    - 日常：追加今天记录
    - 保留365条，按日期去重更新
    - 每条记录包含 keyword_counts（每个关键词当日出现次数），用于热点事件时间线
    """
    history = load_history()
    keywords = config.get("keywords", DEFAULT_KEYWORDS)

    def build_record(date_str, group_items):
        """构建单条历史记录，包含关键词计数"""
        day_keywords = []
        for item in group_items:
            day_keywords.extend(item.get("matched_keywords", []))
        top5 = [kw for kw, _ in Counter(day_keywords).most_common(5)]
        # 统计每个关键词的出现次数（用于时间线）
        keyword_counts = dict(Counter(day_keywords))
        return {
            "date": date_str,
            "total_items": len(group_items),
            "keywords": top5,
            "keyword_counts": keyword_counts,
        }

    if backfill:
        print("[冷启动] 按发布日期生成最近7天历史记录...")
        # 按发布日期分组
        date_groups = defaultdict(list)
        for item in items:
            published_dt = item.get("published_dt")
            if published_dt:
                date_str = published_dt.strftime("%Y-%m-%d")
                date_groups[date_str].append(item)

        # 取最近7天
        sorted_dates = sorted(date_groups.keys(), reverse=True)[:7]
        for date_str in sorted_dates:
            group_items = date_groups[date_str]
            record = build_record(date_str, group_items)
            # 按日期去重
            history = [h for h in history if h.get("date") != date_str]
            history.append(record)
    else:
        # 日常追加今天记录
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        record = build_record(today, items)
        # 按日期去重更新
        history = [h for h in history if h.get("date") != today]
        history.append(record)

    # 按日期排序
    history.sort(key=lambda x: x.get("date", ""), reverse=True)
    # 保留365条
    history = history[:365]
    save_history(history)
    return history


def generate_history_csv(history):
    """生成 data/history.csv"""
    path = os.path.join(DATA_DIR, "history.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["日期", "条目数", "关键词列表"])
        for record in history:
            date = record.get("date", "")
            total = record.get("total_items", 0)
            keywords = ", ".join(record.get("keywords", []))
            writer.writerow([date, total, keywords])
    print(f"[生成] {path}")


def generate_personal_latest(items, config):
    """如果 user_keywords 存在且不为空，生成 data/personal_latest.json"""
    user_keywords = config.get("user_keywords", [])
    if not user_keywords:
        return None

    # 过滤出匹配用户关键词的条目
    personal_items = []
    for item in items:
        text = sanitize_str(item.get("title")) + " " + sanitize_str(item.get("summary"))
        matched = match_keywords(text, user_keywords)
        if matched:
            personal_item = {
                "title": sanitize_str(item.get("title")),
                "link": sanitize_str(item.get("link")),
                "source": sanitize_str(item.get("source")),
                "published": sanitize_str(item.get("published")),
                "hotness": float(item.get("hotness", 0)),
                "summary": sanitize_str(item.get("summary")),
                "analysis": sanitize_str(item.get("analysis", generate_analysis(item, config))),
                "matched_user_keywords": [sanitize_str(kw) for kw in matched],
            }
            personal_items.append(personal_item)

    personal_items.sort(key=lambda x: x.get("hotness", 0), reverse=True)

    data = {
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "user_keywords": [sanitize_str(kw) for kw in user_keywords],
        "total_items": len(personal_items),
        "items": personal_items,
    }

    path = os.path.join(DATA_DIR, "personal_latest.json")
    safe_json_dump(data, path)
    print(f"[生成] {path}（个性化 {len(personal_items)} 条）")
    return data


def send_email(config, report_path, critical_sources=None):
    """发送邮件给站长个人，如有连续失败的源则在正文顶部附加警告"""
    if critical_sources is None:
        critical_sources = []
    email_config = config.get("email_config", {})
    receiver = email_config.get("receiver", "")

    if not receiver:
        print("[信息] 未配置收件人，跳过邮件发送")
        return

    smtp_server = email_config.get("smtp_server", "")
    smtp_port = email_config.get("smtp_port", 465)
    sender = email_config.get("sender", "")
    password = email_config.get("password", "")

    if not all([smtp_server, sender, password]):
        print("[警告] 邮件配置不完整，跳过发送")
        return

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 如有连续失败的源，在正文顶部附加警告
        if critical_sources:
            warning = "⚠️ 以下 RSS 源连续两次失败，请及时检查和处理：\n"
            for src in critical_sources:
                name = src.get("name", "未知源")
                error = src.get("error", "未知错误")
                warning += f"  - {name}：{error}\n"
            warning += "\n" + "=" * 50 + "\n\n"
            content = warning + content

        site_name = config.get("site_name", "环境学子雷达")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subject = f"[{site_name}] 每日热点报告 - {today}"

        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = Header(sender)
        msg["To"] = Header(receiver)
        msg["Subject"] = Header(subject, "utf-8")

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()

        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print(f"[邮件] 已发送至 {receiver}")

    except Exception as e:
        print(f"[错误] 邮件发送失败：{e}")


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("环境学子雷达 - 每日热点报告生成器")
    print("=" * 60)

    ensure_data_dir()
    config = load_config()

    # 冷启动判断
    history_path = os.path.join(DATA_DIR, "history.json")
    history_exists = os.path.exists(history_path)
    history_empty = True
    if history_exists:
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                history_empty = not (isinstance(data, list) and len(data) > 0)
        except Exception:
            history_empty = True

    backfill = (not history_exists) or history_empty
    max_items_per_source = config.get("max_items_per_source", 5)

    if backfill:
        print("[冷启动] 检测到首次运行，max_items_per_source 临时设为 10")
        max_items_per_source = 10

    print(f"[配置] 站点名称：{config.get('site_name')}")
    print(f"[配置] RSS 源数量：{len(config.get('rss_feeds', {}))}")
    print(f"[配置] 每源最大条数：{max_items_per_source}")
    print(f"[配置] 总条目上限：{config.get('max_total_items', 50)}")
    print()

    # 1. 抓取所有源
    print("--- 第一步：抓取 RSS 源 ---")
    all_items, source_health = fetch_all_feeds(config, max_items_per_source)
    print(f"[统计] 共抓取 {len(all_items)} 条")
    print()

    # 2. 去重
    print("--- 第二步：去重 ---")
    all_items = deduplicate_items(all_items)
    print(f"[统计] 去重后 {len(all_items)} 条")
    print()

    # 3. 时间过滤（48小时）
    print("--- 第三步：时间过滤（最近48小时）---")
    all_items = filter_by_time(all_items, hours=48)
    print(f"[统计] 过滤后 {len(all_items)} 条")
    print()

    # 4. 热度计算
    print("--- 第四步：热度计算 ---")
    all_items = calculate_hotness(all_items, config)
    print("[完成] 热度计算完毕")
    print()

    # 5. 排序并限制总数
    print("--- 第五步：排序与截断 ---")
    max_total = config.get("max_total_items", 50)
    all_items = sort_and_limit(all_items, max_total)
    print(f"[统计] 最终候选池 {len(all_items)} 条")
    print()

    # 6. 生成 latest.json
    print("--- 第六步：生成输出文件 ---")
    latest_data = generate_latest_json(all_items, config)
    generate_daily_snapshot(all_items, config)
    generate_monthly_archive(all_items, config)
    generate_pending_terms(all_items, config)
    critical_sources = generate_source_health(source_health)

    # 7. 生成 daily_report.md
    report_path = generate_daily_report_md(all_items, config)

    # 8. 更新 history.json
    history = update_history(all_items, config, backfill=backfill)

    # 9. 生成 history.csv
    generate_history_csv(history)

    # 10. 生成 personal_latest.json（如果有用户关键词）
    generate_personal_latest(all_items, config)

    # 11. 发送邮件（如果配置了）
    print()
    print("--- 第七步：邮件推送 ---")
    send_email(config, report_path, critical_sources)

    print()
    print("=" * 60)
    print("全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
