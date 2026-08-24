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

# 可选依赖：用于原文提取和 AI 摘要
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

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
# 候选新词屏蔽词表（媒体名称、无意义英文词、非专业词汇）
# ============================================================
PENDING_TERM_BLOCKLIST = set([
    # 媒体名称（中文）
    "搜狐网", "中央网", "新华网", "环球网", "澎湃", "腾讯", "网易", "新浪", "凤凰网",
    "中国网", "央视网", "人民网", "中新网", "参考消息", "联合早报", "新浪财经", "财新网",
    "界面新闻", "每经网", "第一财经", "证券时报", "中国证券报", "上海证券报", "经济观察报",
    "21世纪经济报道", "每日经济新闻", "中国青年报", "光明日报", "经济日报", "工人日报",
    "科技日报", "法治日报", "解放军报", "中国教育报", "中国环境报", "中国自然资源报",
    "中国能源报", "中国水利报", "中国气象报", "中国海洋报", "中国绿色时报",
    # 媒体名称（英文）
    "BBC", "CNN", "Guardian", "Reuters", "AFP", "AP", "AP News", "CNN", "Fox", "Fox News",
    "NBC", "ABC", "CBS", "MSNBC", "Bloomberg", "Forbes", "WSJ", "New York Times", "NYT",
    "Washington Post", "WaPo", "Economist", "Time", "Newsweek", "US News", "HuffPost",
    "BuzzFeed", "Vice", "Vox", "Slate", "Salon", "Mother Jones", "Nation", "Atlantic",
    "New Yorker", "Wired", "TechCrunch", "The Verge", "Ars Technica", "Engadget",
    "Mashable", "Business Insider", "Quartz", "Axios", "Politico", "Hill", "Roll Call",
    # 常见英文无意义词
    "to", "do", "come", "in", "on", "at", "the", "of", "and", "or", "for", "with", "is",
    "are", "be", "it", "as", "by", "from", "this", "that", "what", "when", "who", "how",
    "why", "not", "no", "yes", "so", "if", "then", "can", "may", "will", "would", "should",
    "could", "up", "down", "out", "off", "over", "under", "again", "further", "once",
    "here", "there", "where", "which", "whom", "whose", "its", "his", "her", "their",
    "our", "your", "my", "me", "him", "them", "us", "you", "we", "they", "he", "she",
    "an", "a", "any", "all", "some", "each", "every", "both", "few", "many", "much",
    "more", "most", "other", "such", "own", "same", "than", "too", "very", "just",
    "about", "above", "after", "before", "between", "during", "through", "without",
    "within", "along", "across", "behind", "below", "beneath", "beside", "beyond",
    "near", "onto", "toward", "upon", "via", "per", "etc", "vs", "etc.", "i.e.", "e.g.",
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "inc", "ltd", "co", "corp", "dept",
    "gov", "edu", "org", "com", "net", "org", "info", "biz", "tv", "radio", "press",
    # 其他非专业词（中文）
    "今天", "昨天", "报道", "新闻", "记者", "编辑", "评论", "视频", "图片", "来源", "作者",
    "日期", "时间", "发布", "点击", "阅读", "查看", "全文", "摘要", "原文", "链接", "相关",
    "热点", "资讯", "动态", "消息", "快讯", "专题", "独家", "原创", "首发", "重磅", "突发",
    "刚刚", "最新", "关注", "热议", "火了", "爆了", "疯传", "刷屏", "围观", "速看", "扩散",
    "转发", "收藏", "点赞", "订阅", "扫码", "下载", "客户端", "APP", "网站", "公众号",
    "微博", "微信", "抖音", "快手", "B站", "知乎", "豆瓣", "小红书", "视频号", "头条",
    "百度", "阿里", "腾讯", "字节", "美团", "京东", "拼多多", "网易", "新浪", "搜狐",
    "凤凰", "澎湃", "界面", "财新", "第一财经", "每日经济新闻", "21世纪经济报道",
    "经济观察报", "证券时报", "中国证券报", "上海证券报", "参考消息", "联合早报",
    "央视", "央视网", "人民网", "新华网", "中新网", "中国网", "环球网", "凤凰网",
    "搜狐", "网易", "新浪", "腾讯", "百度", "阿里", "字节", "美团", "京东", "拼多多",
    "公司", "企业", "集团", "有限公司", "股份", "控股", "投资", "融资", "上市", "退市",
    "并购", "重组", "破产", "清算", "拍卖", "招标", "投标", "中标", "签约", "合作",
    "协议", "合同", "备忘录", "意向书", "框架", "战略", "战术", "策略", "规划", "计划",
    "方案", "措施", "办法", "规定", "规则", "制度", "机制", "体制", "体系", "系统",
    "模式", "方式", "方法", "手段", "途径", "渠道", "路径", "方向", "目标", "目的",
    "任务", "工作", "活动", "行动", "运动", "项目", "工程", "建设", "发展", "改革",
    "开放", "创新", "创业", "创造", "发明", "发现", "研究", "探索", "实践", "实验",
    "试验", "测试", "检验", "检测", "监测", "监控", "监督", "管理", "治理", "整治",
    "整顿", "规范", "标准", "指标", "参数", "数据", "信息", "知识", "技术", "技能",
    "能力", "水平", "质量", "数量", "规模", "范围", "领域", "行业", "产业", "事业",
    "企业", "公司", "单位", "机构", "组织", "团体", "协会", "学会", "联盟", "联合会",
    "委员会", "办公室", "部门", "处", "科", "室", "组", "队", "班", "级", "届", "次",
    "年度", "季度", "月度", "周度", "日度", "时刻", "时段", "时期", "时代", "阶段",
    "步骤", "环节", "过程", "流程", "程序", "顺序", "次序", "先后", "前后", "左右",
    "上下", "高低", "大小", "多少", "长短", "宽窄", "厚薄", "轻重", "快慢", "远近",
    "深浅", "浓淡", "强弱", "软硬", "新旧", "老幼", "男女", "老少", "中外", "古今",
    "东西", "南北", "前后", "左右", "上下", "内外", "表里", "本末", "始终", "因果",
    "是非", "对错", "好坏", "优劣", "美丑", "善恶", "真假", "虚实", "有无", "多少",
    "盈亏", "涨跌", "升降", "增减", "进退", "攻守", "胜负", "成败", "得失", "利弊",
    "取舍", "选择", "抉择", "决定", "决策", "决议", "结论", "总结", "概括", "归纳",
    "演绎", "分析", "综合", "比较", "对比", "对照", "类比", "比喻", "象征", "代表",
    "表示", "表达", "表现", "体现", "反映", "反应", "回应", "响应", "答复", "回答",
    "问题", "答案", "疑问", "疑惑", "困惑", "迷茫", "茫然", "不解", "难懂", "深奥",
    "浅显", "通俗", "易懂", "简单", "复杂", "繁琐", "繁杂", "庞杂", "杂乱", "凌乱",
    "整齐", "整洁", "干净", "清洁", "卫生", "健康", "安全", "危险", "风险", "隐患",
    "危机", "灾难", "灾害", "灾祸", "事故", "事件", "事情", "事务", "事项", "项目",
    "条目", "条款", "款项", "项目", "科目", "类别", "种类", "类型", "形式", "形态",
    "形状", "形象", "样貌", "外貌", "外观", "外表", "表面", "里面", "内部", "内在",
    "内涵", "含义", "意义", "意思", "定义", "概念", "范畴", "领域", "范围", "边界",
    "界限", "限制", "约束", "束缚", "桎梏", "枷锁", "牢笼", "陷阱", "圈套", "骗局",
    "欺诈", "欺骗", "诈骗", "造假", "仿冒", "假冒", "伪劣", "劣质", "次品", "废品",
    "垃圾", "废物", "废料", "废渣", "废水", "废气", "噪声", "噪音", "辐射", "放射",
    "污染", "净化", "治理", "整治", "整顿", "清理", "清除", "消除", "消灭", "灭绝",
    "绝种", "濒危", "珍稀", "珍贵", "宝贵", "重要", "关键", "核心", "重点", "要点",
    "难点", "疑点", "焦点", "热点", "亮点", "特点", "特征", "特色", "特性", "属性",
    "性质", "本质", "实质", "内容", "形式", "表象", "现象", "迹象", "征兆", "预兆",
    "预言", "预测", "预报", "预警", "预告", "通知", "通告", "公告", "布告", "告示",
    "声明", "宣言", "口号", "标语", "题词", "留言", "寄语", "祝词", "贺词", "悼词",
    "颂词", "赞词", "贬词", "褒词", "名词", "动词", "形容词", "副词", "介词", "连词",
    "助词", "叹词", "量词", "代词", "数词", "冠词", "语法", "句法", "词法", "语义",
    "语用", "语境", "语感", "语调", "语气", "口音", "方言", "土语", "俗语", "谚语",
    "成语", "典故", "寓言", "神话", "传说", "故事", "小说", "散文", "诗歌", "戏剧",
    "电影", "电视", "广播", "报纸", "杂志", "期刊", "图书", "文献", "资料", "档案",
    "记录", "记载", "记述", "描述", "描写", "描绘", "刻画", "塑造", "创造", "创作",
    "制作", "制造", "生产", "加工", "处理", "处置", "办理", "料理", "整理", "整顿",
    "治理", "管理", "管辖", "监管", "监督", "监察", "检察", "检查", "检验", "检测",
    "测验", "测试", "试验", "实验", "实践", "实习", "实训", "实操", "实战", "实务",
    "实际", "现实", "现状", "态势", "形势", "局势", "局面", "场景", "情景", "情境",
    "环境", "氛围", "气氛", "气场", "磁场", "电场", "引力场", "量子场", "规范场",
    "量子", "粒子", "原子", "分子", "离子", "电子", "质子", "中子", "核子", "夸克",
    "弦", "膜", "维", "度", "量", "数", "值", "率", "比", "例", "式", "型", "类",
    "种", "属", "科", "目", "纲", "门", "界", "域", "系", "族", "组", "群", "团",
    "队", "班", "排", "连", "营", "团", "旅", "师", "军", "兵团", "集团军", "方面军",
    "军区", "战区", "司令部", "指挥部", "参谋部", "政治部", "后勤部", "装备部", "技术部",
    "情报部", "通信部", "电子部", "网络部", "信息部", "数据部", "算法部", "工程部",
    "产品部", "设计部", "市场部", "销售部", "客服部", "人事部", "财务部", "法务部",
    "行政部", "办公室", "秘书处", "档案室", "资料室", "图书室", "阅览室", "展览室",
    "陈列室", "标本室", "实验室", "化验室", "检测室", "监测室", "控制室", "操作室",
    "机房", "配电室", "锅炉房", "水泵房", "风机房", "空压机房", "制冷机房", "换热站",
    "变电站", "开关站", "配电站", "变电所", "发电站", "水电站", "火电站", "核电站",
    "风电站", "光伏电站", "太阳能电站", "地热电站", "潮汐电站", "波浪电站", "生物质电站",
    "垃圾电站", "焚烧厂", "填埋场", "堆肥厂", "污水处理厂", "净水厂", "自来水厂",
    "供水厂", "排水厂", "泵站", "闸站", "坝", "堤", "堰", "渠", "管", "沟", "池",
    "塘", "湖", "河", "江", "海", "洋", "湾", "峡", "岛", "礁", "滩", "涂", "岸",
    "滨", "港", "湾", "埠", "码头", "渡口", "车站", "机场", "港口", "码头", "仓库",
    "货场", "堆场", "停车场", "加油站", "加气站", "充电站", "换电站", "服务区", "休息区",
    "收费站", "检查站", "卡子", "关卡", "关隘", "要塞", "堡垒", "城堡", "城池", "城墙",
    "城门", "城楼", "钟楼", "鼓楼", "塔", "阁", "楼", "台", "榭", "轩", "斋", "堂",
    "馆", "所", "院", "园", "苑", "囿", "圃", "田", "地", "土", "山", "水", "林",
    "草", "花", "鸟", "兽", "虫", "鱼", "虾", "蟹", "贝", "螺", "蚌", "蛤", "蛎",
    "蚬", "蛏", "蚶", "蛤", "蚝", "鲍", "参", "翅", "肚", "掌", "筋", "皮", "毛",
    "发", "角", "牙", "齿", "舌", "唇", "鼻", "耳", "眼", "眉", "额", "脸", "面",
    "头", "颈", "肩", "胸", "腹", "背", "腰", "臀", "腿", "膝", "脚", "手", "指",
    "掌", "腕", "肘", "臂", "腋", "肋", "肝", "胆", "脾", "胃", "肠", "肾", "膀胱",
    "心", "肺", "脑", "髓", "骨", "筋", "脉", "血", "肉", "皮", "毛", "发", "甲",
    "爪", "蹄", "角", "牙", "齿", "喙", "嘴", "口", "鼻", "耳", "眼", "眉", "额",
    "脸", "面", "头", "颈", "肩", "胸", "腹", "背", "腰", "臀", "腿", "膝", "脚",
    "手", "指", "掌", "腕", "肘", "臂", "腋", "肋",
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
        # 热度分数明细（用于前端点击展示）
        item["score_breakdown"] = {
            "base": 5.0,
            "source_score": round(source_weight * 3, 2),
            "keyword_score": round(len(matched) * keyword_bonus, 2),
            "time_score": round(time_score, 2),
            "topic_bonus": round(aggregation_bonus, 2),
            "total": round(score, 2),
        }

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
            # 去除首尾标点
            word = re.sub(r'^[\s\W_]+|[\s\W_]+$', '', word)
            # 过滤：长度 >= 2
            if len(word) < 2:
                continue
            # 过滤：停用词
            if word in STOP_WORDS:
                continue
            # 过滤：候选新词屏蔽词表（媒体名称、无意义英文词、非专业词汇）
            if word.lower() in PENDING_TERM_BLOCKLIST or word in PENDING_TERM_BLOCKLIST:
                continue
            # 过滤：纯数字/标点/空白
            if re.match(r'^[\d\s\W]+$', word):
                continue
            # 过滤：纯英文单字母
            if re.match(r'^[a-zA-Z]$', word):
                continue
            # 过滤：纯英文且长度<=2的无意义词（如 to, in, on, at 等已在屏蔽词表，这里兜底）
            if re.match(r'^[a-zA-Z]{1,2}$', word):
                continue
            # 排除已存在于知识库或配置中的词
            word_lower = word.lower()
            if word_lower in existing_terms or word_lower in config_keywords:
                continue
            # 每个词在同一标题中只计一次，contexts 去重
            if word not in seen_in_title:
                seen_in_title.add(word)
                term_count[word] += 1
                # contexts 去重：同一标题只保留一次
                if title not in term_contexts[word] and len(term_contexts[word]) < 3:
                    term_contexts[word].append(title)

    # 筛选出现次数 >= 2 的词，按次数降序
    pending = []
    seen_terms = set()  # 最终去重，确保没有重复的 term
    for term, count in term_count.most_common():
        if count >= 2:
            term_clean = sanitize_str(term)
            # 最终去重检查
            if term_clean.lower() in seen_terms:
                continue
            seen_terms.add(term_clean.lower())
            # contexts 去重
            unique_contexts = []
            for ctx in term_contexts[term]:
                ctx_clean = sanitize_str(ctx)
                if ctx_clean not in unique_contexts:
                    unique_contexts.append(ctx_clean)
            pending.append({
                "term": term_clean,
                "count": int(count),
                "contexts": unique_contexts[:3],
            })

    # 写入文件
    path = os.path.join(DATA_DIR, "pending_terms.json")
    safe_json_dump(pending, path)
    print(f"[生成] {path}（候选词 {len(pending)} 个）")
    return pending


# ============================================================
# AI 功能：原文提取、智谱 GLM 摘要、关键词提取
# ============================================================

def get_api_config(config):
    """获取 API 配置，环境变量优先覆盖 config.yaml"""
    summary_api = config.get("summary_api", {})
    reader_api = config.get("reader_api", {})
    # 环境变量覆盖
    zhipu_key = os.environ.get("ZHIPU_API_KEY", summary_api.get("api_key", ""))
    jina_key = os.environ.get("JINA_API_KEY", reader_api.get("jina_api_key", ""))
    return {
        "summary_enabled": summary_api.get("enabled", False) and bool(zhipu_key),
        "zhipu_key": zhipu_key,
        "model": summary_api.get("model", "glm-4.7-flash"),
        "base_url": summary_api.get("base_url", "https://open.bigmodel.cn/api/paas/v4/"),
        "max_tokens": summary_api.get("max_tokens", 150),
        "reader_enabled": reader_api.get("enabled", True),
        "local_extraction": reader_api.get("local_extraction", True),
        "jina_key": jina_key,
        "jina_base_url": reader_api.get("jina_base_url", "https://r.jina.ai/"),
    }


def extract_article_text(url, api_config):
    """
    提取文章正文纯文本
    优先使用 readability + html2text 本地提取
    失败则使用 Jina Reader 兜底
    全部失败返回 None
    优化：更真实的请求头、特定域名降级、减少日志刷屏
    """
    if not api_config["reader_enabled"] or not REQUESTS_AVAILABLE:
        return None

    # 提取域名，用于判断是否为反爬严格的域名
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
    except Exception:
        domain = ""

    # 对已知反爬严格的域名，如果没有配置 Jina key，直接跳过本地提取
    has_jina = bool(api_config.get("jina_key"))
    is_strict = any(sd in domain for sd in STRICT_DOMAINS)
    if is_strict and not has_jina:
        if domain not in FAILED_DOMAINS:
            FAILED_DOMAINS.add(domain)
            print(f"[原文提取] 跳过反爬严格域名：{domain}")
        return None

    # 更真实的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # 第一步：本地提取
    if api_config["local_extraction"] and READABILITY_AVAILABLE and HTML2TEXT_AVAILABLE:
        try:
            resp = requests.get(url, timeout=15, headers=headers)
            # 对 403、401、405 等错误，直接返回 None，不再重试
            if resp.status_code in (401, 403, 405):
                if domain not in FAILED_DOMAINS:
                    FAILED_DOMAINS.add(domain)
                    print(f"[原文提取] 跳过：{resp.status_code} Forbidden ({domain})")
                return None
            resp.raise_for_status()
            doc = Document(resp.text)
            summary_html = doc.summary()
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            text = h.handle(summary_html).strip()
            if len(text) >= 50:
                return text[:5000]
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if domain not in FAILED_DOMAINS:
                FAILED_DOMAINS.add(domain)
                print(f"[原文提取] HTTP错误 {status_code} ({domain})")
        except Exception as e:
            if domain not in FAILED_DOMAINS:
                FAILED_DOMAINS.add(domain)
                print(f"[原文提取] 本地提取失败: {str(e)[:50]} ({domain})")

    # 第二步：Jina Reader 兜底
    if api_config["jina_key"]:
        try:
            jina_url = api_config["jina_base_url"] + url
            resp = requests.get(jina_url, timeout=20, headers={
                "Authorization": f"Bearer {api_config['jina_key']}"
            })
            resp.raise_for_status()
            text = resp.text.strip()
            if len(text) >= 50:
                return text[:5000]
        except Exception as e:
            if domain not in FAILED_DOMAINS:
                FAILED_DOMAINS.add(domain)
                print(f"[原文提取] Jina 提取失败: {str(e)[:50]} ({domain})")

    return None


# 智谱 API 连续失败计数器（连续失败5次后停止AI调用）
ZHIPU_CONSECUTIVE_FAILURES = 0
ZHIPU_MAX_CONSECUTIVE_FAILURES = 5

# 原文提取失败域名集合（避免重复打印相同错误）
FAILED_DOMAINS = set()
# 已知反爬严格的域名，没有 Jina key 时直接跳过
STRICT_DOMAINS = ["sciencedirect.com", "acs.org", "nature.com", "pnas.org", "iopscience.iop.org"]

# ============================================================
# 英文翻译功能（本地词表 + MyMemory 免费 API）
# ============================================================

# 内置环境专业英文-中文词表（基础版）
BUILTIN_EN_ZH_GLOSSARY = {
    "climate resilience": "气候韧性",
    "carbon tariff": "碳关税",
    "carbon border adjustment": "碳边境调节",
    "microplastics": "微塑料",
    "emerging contaminants": "新污染物",
    "heavy metals": "重金属",
    "biodiversity": "生物多样性",
    "ecological restoration": "生态修复",
    "ecosystem": "生态系统",
    "renewable energy": "可再生能源",
    "clean energy": "清洁能源",
    "circular economy": "循环经济",
    "green finance": "绿色金融",
    "environmental impact assessment": "环境影响评价",
    "waste classification": "垃圾分类",
    "plastic pollution": "塑料污染",
    "marine conservation": "海洋保护",
    "wetland conservation": "湿地保护",
    "desertification": "荒漠化",
    "ozone layer": "臭氧层",
    "acid rain": "酸雨",
    "eutrophication": "富营养化",
    "photocatalysis": "光催化",
    "adsorption": "吸附",
    "membrane separation": "膜分离",
    "advanced oxidation": "高级氧化",
    "water treatment": "水处理",
    "sewage treatment": "污水处理",
    "soil remediation": "土壤修复",
    "solid waste treatment": "固废处理",
    "environmental monitoring": "环境监测",
    "remote sensing": "遥感",
    "life cycle assessment": "生命周期评价",
    "carbon footprint": "碳足迹",
    "carbon neutrality": "碳中和",
    "carbon peak": "碳达峰",
    "carbon emission": "碳排放",
    "carbon sink": "碳汇",
    "carbon trading": "碳交易",
    "greenhouse gas": "温室气体",
    "global warming": "全球变暖",
    "climate change": "气候变化",
    "new energy": "新能源",
    "new energy vehicle": "新能源汽车",
    "water pollution": "水污染",
    "air pollution": "大气污染",
    "soil pollution": "土壤污染",
    "pm2.5": "PM2.5",
    "volatile organic compounds": "挥发性有机物",
    "environmental protection": "环境保护",
    "environmental inspection": "环保督察",
    "sustainable development": "可持续发展",
    "environmental health": "环境健康",
    "environmental science": "环境科学",
    "environmental engineering": "环境工程",
    "ecology": "生态学",
    "cop": "联合国气候变化大会",
    "paris agreement": "巴黎协定",
    "kyoto protocol": "京都议定书",
    "montreal protocol": "蒙特利尔议定书",
    "united nations": "联合国",
    "world health organization": "世界卫生组织",
    "intergovernmental panel on climate change": "政府间气候变化专门委员会",
}


def is_chinese(text):
    """判断文本是否主要为中文（中文字符占比超过30%）"""
    if not text:
        return True
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text.strip())
    if total_chars == 0:
        return True
    return (chinese_chars / total_chars) > 0.3


def translate_en_to_zh(text):
    """
    将英文文本翻译为中文
    - 中文或为空直接返回
    - 优先使用本地环境专业词表匹配
    - 本地词表无法匹配时，调用 MyMemory 免费翻译 API
    - 翻译失败保留英文原文
    """
    if not text or not text.strip():
        return text
    if is_chinese(text):
        return text

    text_lower = text.lower().strip()

    # 第一步：尝试本地词表精确匹配（整个文本）
    if text_lower in BUILTIN_EN_ZH_GLOSSARY:
        return BUILTIN_EN_ZH_GLOSSARY[text_lower]

    # 尝试读取外部词表文件（如果存在）
    external_glossary = {}
    glossary_path = os.path.join(DATA_DIR, "en_zh_glossary.json")
    if os.path.exists(glossary_path):
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                external_glossary = json.load(f)
            if text_lower in external_glossary:
                return external_glossary[text_lower]
        except Exception:
            pass

    # 第二步：调用 MyMemory 免费翻译 API
    if not REQUESTS_AVAILABLE:
        return text

    try:
        import urllib.parse
        encoded_text = urllib.parse.quote(text[:500])
        api_url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|zh-CN"
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        translated = result.get("responseData", {}).get("translatedText", "")
        if translated and translated.strip() and translated != text:
            return translated.strip()
    except Exception as e:
        # 翻译失败静默处理，保留原文
        pass

    return text


def call_zhipu_api(prompt, api_config, max_tokens=None):
    """
    调用智谱 GLM API（OpenAI 兼容格式），返回生成的文本，失败返回 None
    增加重试机制：429或超时后等待重试，最多3次，等待时间递增3/6/10秒
    连续失败5次后停止AI调用
    """
    global ZHIPU_CONSECUTIVE_FAILURES

    if not api_config["summary_enabled"] or not api_config["zhipu_key"]:
        return None
    if not REQUESTS_AVAILABLE:
        return None
    # 连续失败超过阈值，停止调用
    if ZHIPU_CONSECUTIVE_FAILURES >= ZHIPU_MAX_CONSECUTIVE_FAILURES:
        return None

    url = api_config["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['zhipu_key']}",
        "Content-Type": "application/json",
    }
    data = {
        "model": api_config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens or api_config["max_tokens"],
        "temperature": 0.3,
    }

    # 重试机制：最多3次，等待时间递增3/6/10秒
    retry_delays = [3, 6, 10]
    for attempt in range(3):
        try:
            # 超时设置：摘要类15秒，关键词类20秒
            timeout = 15 if (max_tokens or api_config["max_tokens"]) <= 150 else 20
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()
            # 调用成功，重置连续失败计数
            ZHIPU_CONSECUTIVE_FAILURES = 0
            return content
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            # 429 限流，需要重试
            if status_code == 429 and attempt < 2:
                wait_time = retry_delays[attempt]
                print(f"[智谱API] 429限流，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            # 其他HTTP错误，不重试
            print(f"[智谱API] HTTP错误 {status_code}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return None
        except requests.exceptions.Timeout:
            if attempt < 2:
                wait_time = retry_delays[attempt]
                print(f"[智谱API] 请求超时，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            print(f"[智谱API] 请求超时（已重试3次）")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return None
        except requests.exceptions.RequestException as e:
            print(f"[智谱API] 网络错误: {str(e)[:50]}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return None
        except Exception as e:
            print(f"[智谱API] 未知错误: {str(e)[:50]}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return None

    # 所有重试都失败
    ZHIPU_CONSECUTIVE_FAILURES += 1
    return None


def generate_ai_summary(item, api_config):
    """
    为单条热点生成 AI 摘要
    摘要为空或与标题相同时才生成
    优先基于原文，失败则基于标题
    """
    title = item.get("title", "")
    summary = item.get("summary", "")
    # 摘要非空且不等于标题，跳过
    if summary and summary != title and len(summary) > 20:
        return summary

    if not api_config["summary_enabled"]:
        return summary

    link = item.get("link", "")
    article_text = None
    if link:
        article_text = extract_article_text(link, api_config)

    if article_text:
        prompt = f"你是一个环境领域摘要助手。请根据以下文章内容，生成一句不超过50字的中文摘要，直接输出摘要，不要解释。\n\n文章内容：{article_text[:3000]}"
    else:
        prompt = f"你是一个环境领域摘要助手。请根据以下新闻标题，推测并生成一句不超过50字的中文摘要，直接输出摘要，不要解释。\n\n标题：{title}"

    result = call_zhipu_api(prompt, api_config, max_tokens=100)
    if result:
        # 清理可能的引号
        result = result.strip('"').strip("'").strip()
        return result
    return summary


def calculate_weekly_keywords():
    """
    统计近7天实际高频词
    从每日快照文件（docs/data/daily/YYYY-MM-DD.json）中提取 topic_tags
    也从 history.json 中提取关键词作为补充
    返回 [{term, count}, ...]，按出现次数降序排列，取前10个
    """
    from datetime import datetime, timedelta
    keyword_counter = Counter()

    # 方法一：从最近7天的每日快照文件中提取 topic_tags
    today = datetime.now().date()
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        daily_path = os.path.join(DATA_DIR, "daily", f"{date_str}.json")
        if os.path.exists(daily_path):
            try:
                with open(daily_path, "r", encoding="utf-8") as f:
                    daily_data = json.load(f)
                items = daily_data.get("items", [])
                for item in items:
                    tags = item.get("topic_tags", [])
                    for tag in tags:
                        if tag and len(str(tag).strip()) >= 2:
                            keyword_counter[str(tag).strip()] += 1
                    # 也从 matched_keywords 中提取
                    matched = item.get("matched_keywords", [])
                    for kw in matched:
                        if kw and len(str(kw).strip()) >= 2:
                            keyword_counter[str(kw).strip()] += 1
            except Exception:
                continue

    # 方法二：从 history.json 中提取关键词作为补充
    history_path = os.path.join(DATA_DIR, "history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            if isinstance(history, list):
                recent = history[-7:]
                for day in recent:
                    kws = day.get("keywords", [])
                    for kw in kws:
                        if isinstance(kw, dict):
                            term = kw.get("keyword", "") or kw.get("term", "")
                            count = kw.get("count", 1)
                        else:
                            term = str(kw)
                            count = 1
                        if term and len(term.strip()) >= 2:
                            keyword_counter[term.strip()] += count
        except Exception:
            pass

    # 过滤宽泛词
    banned = {"环境", "污染", "保护", "气候变化", "环保", "生态", "可持续发展", "环境领域", "环境保护", "环境问题", "环境科学", "环境工程", "环境动态"}
    for banned_word in banned:
        if banned_word in keyword_counter:
            del keyword_counter[banned_word]

    # 取前10个
    top_keywords = [{"term": term, "count": count} for term, count in keyword_counter.most_common(10)]
    return top_keywords


def generate_weekly_summary(api_config, weekly_keywords=None):
    """
    生成近7天热度总结
    优先使用 AI 生成，失败则使用规则生成
    基于实际高频词（weekly_keywords）生成，而不是预设宽泛词
    写入 latest.json 的 weekly_summary 字段
    """
    # 如果没有传入 weekly_keywords，则计算
    if weekly_keywords is None:
        weekly_keywords = calculate_weekly_keywords()

    if not weekly_keywords:
        return ""

    # 提取前5个高频词
    top_terms = [kw["term"] for kw in weekly_keywords[:5]]
    total_count = sum(kw["count"] for kw in weekly_keywords)

    # AI 生成
    if api_config["summary_enabled"] and top_terms:
        prompt = f"你是一个环境领域分析助手。请根据以下近7天环境领域高频关键词，生成一段不超过80字的中文总结，直接输出总结，不要解释。\n\n高频关键词：{', '.join(top_terms)}\n关键词总出现次数：{total_count}"
        result = call_zhipu_api(prompt, api_config, max_tokens=120)
        if result:
            return result.strip('"').strip("'").strip()

    # 规则生成（降级）
    if top_terms:
        return f"近7天环境领域热点集中在：{'、'.join(top_terms[:3])}，关键词累计出现{total_count}次。"
    return ""


def generate_ai_keywords(items, api_config):
    """
    使用 AI 从热点条目中提取环境领域相关热门关键词
    返回关键词列表 [{term, count}]，失败返回 None
    """
    if not api_config["summary_enabled"] or not items:
        return None

    # 取 Top 20 条以减少 token
    top_items = items[:20]
    text_parts = []
    for item in top_items:
        title = item.get("title", "")
        summary = item.get("summary", "")
        if title:
            text_parts.append(f"标题：{title}")
        if summary and len(summary) > 10:
            text_parts.append(f"摘要：{summary[:200]}")
    combined_text = "\n".join(text_parts)

    prompt = f"""你是一个环境领域关键词提取专家。请从以下新闻标题和摘要中提取与环境领域相关的热门关键词。

要求：
1. 关键词必须与环境领域相关（气候、生态、污染、能源、可持续发展、环境政策、环境健康、技术方法等）
2. 关键词要具体、多样，避免过于宽泛的词（如"环境""污染""保护"），除非原文特别强调
3. 关键词要贴近原文内容，从标题和摘要中提炼，不要凭空生成
4. 如果原文内容与环境领域无关，可返回空数组
5. 直接返回 JSON 数组，格式：[{{"term": "碳中和", "count": 5}}]，不要解释

新闻内容：
{combined_text[:4000]}"""

    result = call_zhipu_api(prompt, api_config, max_tokens=300)
    if not result:
        return None

    # 解析 JSON
    try:
        # 去除可能的 markdown 代码块标记
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[-1]
            if result.endswith("```"):
                result = result[:-3]
        result = result.strip()
        # 找到第一个 [ 和最后一个 ]
        start = result.find("[")
        end = result.rfind("]")
        if start >= 0 and end > start:
            result = result[start:end+1]
        keywords = json.loads(result)
        if isinstance(keywords, list):
            # 验证格式
            valid = []
            for kw in keywords:
                if isinstance(kw, dict) and kw.get("term"):
                    valid.append({
                        "term": str(kw["term"]),
                        "count": int(kw.get("count", 1)),
                    })
            if valid:
                return valid
    except Exception as e:
        print(f"[AI关键词] 解析失败: {str(e)[:60]}")
    return None


def generate_topic_tags(item, api_config):
    """
    为单条热点生成 1-3 个具体话题标签
    优先使用"标题+原文"，原文获取失败则仅使用标题
    失败返回空数组
    """
    if not api_config["summary_enabled"]:
        return []

    title = item.get("title", "")
    summary = item.get("summary", "")
    if not title:
        return []

    # 尝试获取原文，用于生成更准确的标签
    article_text = ""
    link = item.get("link", "")
    if link and api_config.get("reader_enabled", True):
        try:
            extracted = extract_article_text(link, api_config)
            if extracted:
                article_text = extracted[:500]
        except Exception:
            pass

    # 构建输入内容
    if article_text:
        content_text = f"标题：{title}\n原文：{article_text}"
    elif summary and len(summary) > 10:
        content_text = f"标题：{title}\n摘要：{summary[:300]}"
    else:
        content_text = f"标题：{title}"

    prompt = f"""你是一个环境领域话题标签提取助手。请从以下新闻标题和摘要中提取 1-3 个最具体、最能概括内容的关键词或短语。

严格要求：
1. 标签必须具体、贴近内容，禁止使用宽泛词
2. 禁止返回以下宽泛词：环境、污染、保护、气候变化、环保、生态、可持续发展、环境领域、环境保护、环境问题
3. 优先提取具体的事件、地点、物质、技术、政策名称
4. 直接返回 JSON 数组，格式：["标签1","标签2"]，不要解释
5. 如果无法确定具体标签，返回空数组 []

{content_text}"""

    result = call_zhipu_api(prompt, api_config, max_tokens=80)
    if not result:
        return []

    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[-1]
            if result.endswith("```"):
                result = result[:-3]
        result = result.strip()
        start = result.find("[")
        end = result.rfind("]")
        if start >= 0 and end > start:
            result = result[start:end+1]
        tags = json.loads(result)
        if isinstance(tags, list):
            # 过滤宽泛词
            banned = {"环境", "污染", "保护", "气候变化", "环保", "生态", "可持续发展", "环境领域", "环境保护", "环境问题", "环境科学", "环境工程"}
            clean_tags = [str(t).strip() for t in tags if t and len(str(t).strip()) >= 2 and str(t).strip() not in banned]
            return clean_tags[:3]
    except Exception:
        pass
    return []


def extract_tags_from_title(title):
    """
    从标题中提取话题标签作为降级方案
    优先提取最长的连续中文字符串或包含已知关键词的词组
    失败返回 ["环境动态"]
    """
    if not title or len(title) < 4:
        return ["环境动态"]

    # 已知环境领域关键词（具体词）
    specific_keywords = [
        "碳中和", "碳达峰", "碳关税", "碳交易", "碳汇", "碳排放",
        "微塑料", "新污染物", "重金属", "PM2.5", "VOCs", "臭氧",
        "水污染", "大气污染", "土壤污染", "噪声污染", "光污染",
        "生物多样性", "生态修复", "生态系统", "湿地", "荒漠化", "红树林",
        "可再生能源", "清洁能源", "新能源", "光伏", "风电", "氢能",
        "循环经济", "绿色金融", "环保督察", "环评", "垃圾分类",
        "塑料污染", "海洋保护", "富营养化", "酸雨", "臭氧层",
        "水处理", "污水处理", "土壤修复", "固废处理", "环境监测",
        "光催化", "吸附", "膜分离", "高级氧化", "生物降解",
        "联合国", "COP", "巴黎协定", "京都议定书", "蒙特利尔议定书",
        "生态环境部", "环保部", "国家发改委", "国务院",
    ]

    # 从标题中匹配具体关键词
    matched = []
    for kw in specific_keywords:
        if kw in title:
            matched.append(kw)

    if matched:
        # 取前3个匹配的关键词
        return matched[:3]

    # 提取最长的连续中文字符串（长度>=4）
    import re
    chinese_segments = re.findall(r'[\u4e00-\u9fa5]{4,}', title)
    if chinese_segments:
        # 取最长的一段
        longest = max(chinese_segments, key=len)
        if len(longest) <= 15:
            return [longest]
        else:
            # 太长则取前10个字符
            return [longest[:10]]

    # 兜底
    return ["环境动态"]


def generate_batch_summaries(items, api_config):
    """
    批量生成摘要：将所有需要摘要的条目合并成一次 API 请求
    返回修改后的 items 列表（原地修改）
    每天最多调用1次 API，而不是每条调用一次
    """
    global ZHIPU_CONSECUTIVE_FAILURES
    if not api_config["summary_enabled"] or not api_config["zhipu_key"]:
        return items
    if not REQUESTS_AVAILABLE:
        return items
    if ZHIPU_CONSECUTIVE_FAILURES >= ZHIPU_MAX_CONSECUTIVE_FAILURES:
        return items

    # 筛选需要生成摘要的条目（摘要为空、与标题相同、或长度<20）
    need_summary = []
    for idx, item in enumerate(items):
        summary = item.get("summary", "")
        title = item.get("title", "")
        if not summary or summary == title or len(summary) < 20:
            need_summary.append((idx, item))

    if not need_summary:
        print("[AI] 所有条目已有摘要，跳过批量摘要生成")
        return items

    # 构建 prompt
    news_list = []
    for local_idx, (orig_idx, item) in enumerate(need_summary):
        title = item.get("title", "无标题")
        link = item.get("link", "")
        # 尝试获取原文（只取前500字以控制 token）
        article_text = ""
        if link and api_config.get("reader_enabled", True):
            try:
                extracted = extract_article_text(link, api_config)
                if extracted:
                    article_text = extracted[:500]
            except Exception:
                pass
        if article_text:
            news_list.append(f"{local_idx}. 标题：{title}\n内容：{article_text}")
        else:
            news_list.append(f"{local_idx}. 标题：{title}")

    prompt = f"""你是一个环境领域摘要助手。请为以下每条新闻生成一句不超过50字的中文摘要，直接返回JSON数组，格式：[{{"id":0,"summary":"..."}},{{"id":1,"summary":"..."}}]，不要解释。

新闻列表：
{chr(10).join(news_list)}"""

    # 批量请求，重试1-2次，等待5秒、10秒，超时20秒
    retry_delays = [5, 10]
    result_text = None
    for attempt in range(2):
        try:
            url = api_config["base_url"].rstrip("/") + "/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_config['zhipu_key']}",
                "Content-Type": "application/json",
            }
            data = {
                "model": api_config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3,
            }
            resp = requests.post(url, headers=headers, json=data, timeout=20)
            resp.raise_for_status()
            result = resp.json()
            result_text = result["choices"][0]["message"]["content"].strip()
            ZHIPU_CONSECUTIVE_FAILURES = 0
            break
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if status_code == 429 and attempt < 1:
                wait_time = retry_delays[attempt]
                print(f"[AI批量摘要] 429限流，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            print(f"[AI批量摘要] HTTP错误 {status_code}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return items
        except requests.exceptions.Timeout:
            if attempt < 1:
                wait_time = retry_delays[attempt]
                print(f"[AI批量摘要] 请求超时，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            print("[AI批量摘要] 请求超时（已重试）")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return items
        except Exception as e:
            print(f"[AI批量摘要] 调用失败: {str(e)[:60]}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            return items

    if not result_text:
        return items

    # 解析返回的 JSON
    try:
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[-1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
        result_text = result_text.strip()
        start = result_text.find("[")
        end = result_text.rfind("]")
        if start >= 0 and end > start:
            result_text = result_text[start:end+1]
        summaries = json.loads(result_text)
        if isinstance(summaries, list):
            count = 0
            for s in summaries:
                if isinstance(s, dict) and "id" in s and "summary" in s:
                    local_idx = int(s["id"])
                    if 0 <= local_idx < len(need_summary):
                        orig_idx, item = need_summary[local_idx]
                        new_summary = str(s["summary"]).strip().strip('"').strip("'")
                        if new_summary:
                            item["summary"] = new_summary
                            count += 1
            print(f"[AI批量摘要] 成功生成 {count}/{len(need_summary)} 条摘要")
    except Exception as e:
        print(f"[AI批量摘要] 解析返回结果失败: {str(e)[:50]}")

    return items


def generate_batch_topic_tags(items, api_config):
    """
    批量生成话题标签：将所有条目合并成一次 API 请求
    返回修改后的 items 列表（原地修改）
    每天最多调用1次 API
    """
    global ZHIPU_CONSECUTIVE_FAILURES
    if not api_config["summary_enabled"] or not api_config["zhipu_key"]:
        for item in items:
            item["topic_tags"] = []
        return items
    if not REQUESTS_AVAILABLE:
        for item in items:
            item["topic_tags"] = []
        return items
    if ZHIPU_CONSECUTIVE_FAILURES >= ZHIPU_MAX_CONSECUTIVE_FAILURES:
        for item in items:
            item["topic_tags"] = []
        return items

    # 只处理前10条
    target_items = items[:10]
    if not target_items:
        return items

    # 构建 prompt（先翻译英文内容为中文）
    news_list = []
    for idx, item in enumerate(target_items):
        title = item.get("title", "无标题")
        summary = item.get("summary", "")
        # 翻译英文标题和摘要
        title_zh = translate_en_to_zh(title)
        summary_zh = translate_en_to_zh(summary[:200]) if summary else ""
        if summary_zh and len(summary_zh) > 10:
            news_list.append(f"{idx}. 标题：{title_zh}\n摘要：{summary_zh[:200]}")
        else:
            news_list.append(f"{idx}. 标题：{title_zh}")

    prompt = f"""你是一个环境领域标签专家。请为以下每条新闻提取1-3个具体的中文关键词或短语作为话题标签。

严格要求：
1. 标签必须具体、贴近内容，与环境领域相关
2. 禁止返回宽泛词：环境、污染、保护、气候变化、环保、生态、可持续发展、环境领域、环境保护、环境问题
3. 如果看到英文内容，已翻译为中文，请基于中文内容提取
4. 优先提取具体的事件、地点、物质、技术、政策名称
5. 直接返回JSON数组，格式：[{{"id":0,"tags":["气候韧性","微塑料污染"]}},{{"id":1,"tags":["碳关税"]}}]，不要解释

新闻列表：
{chr(10).join(news_list)}"""

    # 批量请求，重试1-2次，等待5秒、10秒，超时20秒
    retry_delays = [5, 10]
    result_text = None
    for attempt in range(2):
        try:
            url = api_config["base_url"].rstrip("/") + "/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_config['zhipu_key']}",
                "Content-Type": "application/json",
            }
            data = {
                "model": api_config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.3,
            }
            resp = requests.post(url, headers=headers, json=data, timeout=20)
            resp.raise_for_status()
            result = resp.json()
            result_text = result["choices"][0]["message"]["content"].strip()
            ZHIPU_CONSECUTIVE_FAILURES = 0
            break
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if status_code == 429 and attempt < 1:
                wait_time = retry_delays[attempt]
                print(f"[AI批量标签] 429限流，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            print(f"[AI批量标签] HTTP错误 {status_code}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            for item in items:
                item["topic_tags"] = []
            return items
        except requests.exceptions.Timeout:
            if attempt < 1:
                wait_time = retry_delays[attempt]
                print(f"[AI批量标签] 请求超时，第{attempt+1}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            print("[AI批量标签] 请求超时（已重试）")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            for item in items:
                item["topic_tags"] = []
            return items
        except Exception as e:
            print(f"[AI批量标签] 调用失败: {str(e)[:60]}")
            ZHIPU_CONSECUTIVE_FAILURES += 1
            for item in items:
                item["topic_tags"] = []
            return items

    if not result_text:
        for item in items:
            item["topic_tags"] = []
        return items

    # 解析返回的 JSON
    try:
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[-1]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
        result_text = result_text.strip()
        start = result_text.find("[")
        end = result_text.rfind("]")
        if start >= 0 and end > start:
            result_text = result_text[start:end+1]
        tags_list = json.loads(result_text)
        if isinstance(tags_list, list):
            count = 0
            for t in tags_list:
                if isinstance(t, dict) and "id" in t and "tags" in t:
                    idx = int(t["id"])
                    if 0 <= idx < len(target_items):
                        tags = t["tags"]
                        if isinstance(tags, list):
                            clean_tags = [str(tag).strip() for tag in tags if tag and len(str(tag).strip()) >= 2][:3]
                            target_items[idx]["topic_tags"] = clean_tags
                            count += 1
            # 为没有返回标签的条目设置空数组
            for item in target_items:
                if "topic_tags" not in item:
                    item["topic_tags"] = []
            print(f"[AI批量标签] 成功生成 {count}/{len(target_items)} 条话题标签")
    except Exception as e:
        print(f"[AI批量标签] 解析返回结果失败: {str(e)[:50]}")
        for item in items:
            item["topic_tags"] = []

    # 为剩余条目设置空 topic_tags
    for item in items[10:]:
        item["topic_tags"] = []

    return items


def enhance_analysis_with_tags(item):
    """根据 topic_tags 优化 analysis 字段"""
    topic_tags = item.get("topic_tags", [])
    if topic_tags:
        topic = topic_tags[0]
    else:
        # 回退到匹配的关键词
        matched = item.get("matched_keywords", [])
        topic = matched[0] if matched else "环境动态"

    # 热度构成分析
    parts = []
    source_weight = item.get("source_weight", 1.0)
    if source_weight >= 2.0:
        parts.append("来源权威性")
    published_dt = item.get("published_dt")
    if published_dt:
        hours_ago = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600
        if hours_ago <= 24:
            parts.append("时间新鲜度")
    matched = item.get("matched_keywords", [])
    if len(matched) >= 2:
        parts.append("主题热度")
    if not parts:
        parts.append("综合因素")

    drive_text = "和".join(parts)
    return f"该条目涉及【{topic}】话题，热度主要由{drive_text}驱动，建议关注。"


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


def generate_personal_knowledge():
    """
    生成/追加个人知识库 personal_knowledge.md
    - 读取 latest.json 获取关键词和 Top10 热点
    - 读取 pending_terms.json 获取候选新词
    - 追加到根目录 personal_knowledge.md
    - 如果当天已存在则替换当天内容，避免重复
    """
    knowledge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personal_knowledge.md")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 读取 latest.json
    latest_path = os.path.join(DATA_DIR, "latest.json")
    latest_data = {}
    if os.path.exists(latest_path):
        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                latest_data = json.load(f)
        except Exception as e:
            print(f"[个人知识库] 读取 latest.json 失败：{e}")
            return

    # 读取 pending_terms.json
    pending_path = os.path.join(DATA_DIR, "pending_terms.json")
    pending_terms = []
    if os.path.exists(pending_path):
        try:
            with open(pending_path, "r", encoding="utf-8") as f:
                pending_terms = json.load(f)
        except Exception:
            pending_terms = []

    # 生成当天内容
    content_lines = []
    content_lines.append(f"## {today}")
    content_lines.append("")

    # 今日高频关键词
    keywords = latest_data.get("keywords", [])
    if keywords:
        top5_keywords = keywords[:5]
        keyword_tags = " ".join([f"`#{kw.get('keyword', kw) if isinstance(kw, dict) else kw}`" for kw in top5_keywords])
        content_lines.append(f"**今日高频关键词**：{keyword_tags}")
        content_lines.append("")

    # 今日 Top10 热点
    items = latest_data.get("items", [])
    if items:
        content_lines.append("**今日 Top10 热点**")
        content_lines.append("")
        for idx, item in enumerate(items[:10], 1):
            title = item.get("title", "无标题")
            source = item.get("source", "未知来源")
            score = item.get("score", item.get("hotness", 0))
            summary = item.get("summary", "")
            analysis = item.get("analysis", "")
            link = item.get("link", "")

            content_lines.append(f"### {idx}. {title}")
            content_lines.append(f"- **来源**：{source}")
            content_lines.append(f"- **热度**：{round(score, 1) if isinstance(score, (int, float)) else score}")
            if link:
                content_lines.append(f"- **链接**：{link}")
            if summary:
                content_lines.append(f"- **摘要**：{summary}")
            if analysis:
                content_lines.append(f"- **分析**：{analysis}")
            content_lines.append("")

    # 今日候选新词
    if pending_terms:
        content_lines.append("**今日自动提取候选新词**")
        content_lines.append("")
        for term in pending_terms:
            if isinstance(term, dict):
                term_name = term.get("term", "")
                count = term.get("count", 0)
                contexts = term.get("contexts", [])
                content_lines.append(f"- **{term_name}**（出现 {count} 次）")
                if contexts:
                    for ctx in contexts[:3]:
                        content_lines.append(f"  - 上下文：{ctx}")
            else:
                content_lines.append(f"- {term}")
        content_lines.append("")

    content_lines.append("---")
    content_lines.append("")
    day_content = "\n".join(content_lines)

    # 读取现有文件内容
    existing_content = ""
    if os.path.exists(knowledge_path):
        try:
            with open(knowledge_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception:
            existing_content = ""

    # 检查当天是否已存在
    day_header = f"## {today}"
    if day_header in existing_content:
        # 替换当天内容：找到当天标题到下一个 ## 标题或文件末尾
        import re
        # 匹配从当天 ## 标题到下一个 ## 标题（非贪婪）
        pattern = re.compile(
            r'## ' + re.escape(today) + r'.*?(?=\n## \d{4}-\d{2}-\d{2}|\Z)',
            re.DOTALL
        )
        if pattern.search(existing_content):
            existing_content = pattern.sub(day_content.rstrip() + "\n\n", existing_content)
            print(f"[个人知识库] 已替换 {today} 的内容")
        else:
            existing_content += "\n" + day_content
            print(f"[个人知识库] 已追加 {today} 的内容")
    else:
        # 文件不存在或当天不存在，追加
        if not existing_content:
            # 新建文件，写入头部说明
            header = "# 个人知识库\n\n"
            header += "> 本文件由 daily_report.py 自动生成，记录每日环境领域热点、关键词和候选新词。\n\n"
            header += "---\n\n"
            existing_content = header
        existing_content += day_content
        print(f"[个人知识库] 已追加 {today} 的内容")

    # 写入文件
    try:
        with open(knowledge_path, "w", encoding="utf-8") as f:
            f.write(existing_content)
        print(f"[个人知识库] 已保存至 {knowledge_path}")
    except Exception as e:
        print(f"[个人知识库] 写入失败：{e}")


def generate_latest_json(items, config, weekly_summary="", weekly_keywords=None):
    """生成 data/latest.json"""
    site_name = config.get("site_name", "环境学子雷达")
    keywords = config.get("keywords", DEFAULT_KEYWORDS)

    # 关键词分析（前10）- 基于配置关键词统计
    all_keywords = []
    for item in items:
        all_keywords.extend(item.get("matched_keywords", []))
    keyword_counter = Counter(all_keywords)
    top_keywords = [{"keyword": kw, "count": cnt} for kw, cnt in keyword_counter.most_common(10)]

    # 如果有 AI 提取的关键词，合并（优先 AI 结果，去重）
    ai_keywords = config.get("_ai_keywords", [])
    if ai_keywords:
        existing_terms = set(k["keyword"] for k in top_keywords)
        for ak in ai_keywords:
            term = ak.get("term", "")
            if term and term not in existing_terms:
                top_keywords.append({"keyword": term, "count": ak.get("count", 1)})
                existing_terms.add(term)
        top_keywords.sort(key=lambda x: x["count"], reverse=True)
        top_keywords = top_keywords[:10]

    # 热点总结
    if top_keywords:
        top5 = "、".join([k["keyword"] for k in top_keywords[:5]])
        summary = f"今日热点围绕{top5}等话题，共聚合{len(items)}条资讯。"
    else:
        summary = f"今日共聚合{len(items)}条资讯。"

    # 构建条目列表（移除内部字段，确保所有值为可序列化的基本类型）
    output_items = []
    for item in items:
        # 生成分析（优先使用 topic_tags 优化）
        analysis = enhance_analysis_with_tags(item)
        item["analysis"] = analysis
        output_items.append({
            "title": sanitize_str(item.get("title")),
            "link": sanitize_str(item.get("link")),
            "source": sanitize_str(item.get("source")),
            "published": sanitize_str(item.get("published")),
            "hotness": float(item.get("hotness", 0)),
            "score": float(item.get("hotness", 0)),
            "score_breakdown": item.get("score_breakdown", {}),
            "summary": sanitize_str(item.get("summary")),
            "analysis": sanitize_str(analysis),
            "topic_tags": item.get("topic_tags", []),
            "matched_keywords": [sanitize_str(kw) for kw in item.get("matched_keywords", [])],
            "keywords": [sanitize_str(kw) for kw in item.get("matched_keywords", [])],
        })

    data = {
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "site_name": sanitize_str(site_name),
        "total_items": len(output_items),
        "items": output_items,
        "keyword_analysis": top_keywords,
        "keywords": top_keywords,
        "hot_summary": sanitize_str(summary),
        "summary": sanitize_str(summary),
        "weekly_summary": sanitize_str(weekly_summary),
        "weekly_keywords": weekly_keywords if weekly_keywords is not None else [],
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

    # AI 处理：批量摘要生成、批量话题标签、关键词提取、近7天总结
    api_config = get_api_config(config)
    if api_config["summary_enabled"]:
        print("[AI] 智谱 GLM 已启用，开始批量生成 AI 摘要和话题标签...")
        # 批量生成摘要（一次API调用，处理所有需要摘要的条目）
        all_items = generate_batch_summaries(all_items, api_config)
        # 批量生成话题标签（一次API调用，处理前10条，英文内容先翻译）
        all_items = generate_batch_topic_tags(all_items, api_config)
        # 为没有 topic_tags 的条目使用标题提取规则降级
        for item in all_items:
            if not item.get("topic_tags"):
                item["topic_tags"] = extract_tags_from_title(item.get("title", ""))
        # AI 关键词提取（只调用一次，输入 Top 20 条标题和摘要）
        ai_keywords = generate_ai_keywords(all_items, api_config)
        if ai_keywords:
            config["_ai_keywords"] = ai_keywords
            print(f"[AI] 提取到 {len(ai_keywords)} 个环境领域关键词")
        print("[AI] 批量处理完成，每天最多调用3次API（摘要+标签+关键词）")
    else:
        print("[AI] 智谱 GLM 未启用，使用规则生成摘要和关键词")
        for item in all_items:
            item["topic_tags"] = extract_tags_from_title(item.get("title", ""))

    # 生成近7天热度总结（基于实际高频词）
    weekly_keywords = calculate_weekly_keywords()
    if weekly_keywords:
        print(f"[统计] 近7天高频词：{', '.join(kw['term'] for kw in weekly_keywords[:5])}")
    weekly_summary = generate_weekly_summary(api_config, weekly_keywords=weekly_keywords)
    if weekly_summary:
        print(f"[AI] 近7天总结: {weekly_summary[:60]}...")

    latest_data = generate_latest_json(all_items, config, weekly_summary=weekly_summary, weekly_keywords=weekly_keywords)
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

    # 12. 生成个人知识库
    print()
    print("--- 第八步：生成个人知识库 ---")
    generate_personal_knowledge()

    print()
    print("=" * 60)
    print("全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
