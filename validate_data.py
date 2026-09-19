# -*- coding: utf-8 -*-
"""数据文件结构校验（审查报告 C-2 短期项 / K-2 根因防护）

为什么需要它
------------
考研、就业两个窗口的数据（schools.json / careers.json / jobs.json）长期由手工维护，
既没有生成脚本，也没有任何自动校验。于是「字段缺失」「语义漂移」这类问题只有等
用户打开网页才会暴露——K-2 就是典型：一所院校少一个 `tags` 字段，18 所院校全部白屏，
而且错误态被锁死，必须刷新整页才能恢复。

这里把这些约束固化成可执行检查，在 CI 里每次运行后跑一遍：
坏数据在提交之前就被拦住，而不是等评委点开首页。

用法
----
    python validate_data.py            # 校验 docs/data 下全部受管数据文件
    python validate_data.py --data-dir /path/to/docs/data

退出码 0 = 全部通过（可能有警告）；1 = 存在错误。
"""
import argparse
import json
import os
import re
import sys

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")

DISCIPLINE_GRADES = {"", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-"}
DEMAND_LEVELS = {"high", "mid-high", "medium", "low"}
JOB_CATEGORIES = {"技术", "咨询", "体制内", "交叉"}
RECRUIT_TYPES = {"实习", "校招", "社招"}
JOB_TYPES = {"实习", "校招", "社招"}

errors = []
warnings = []
infos = []


def err(f, path, msg):
    errors.append("[%s] %s: %s" % (f, path, msg))


def warn(f, path, msg):
    warnings.append("[%s] %s: %s" % (f, path, msg))


def info(f, msg):
    infos.append("[%s] %s" % (f, msg))


def load(data_dir, name, required):
    path = os.path.join(data_dir, name)
    if not os.path.exists(path):
        if required:
            errors.append("[%s] 文件不存在: %s" % (name, path))
            return None
        infos.append("[%s] 文件不存在（可选，跳过）" % name)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:  # noqa: BLE001 - 校验脚本需要报告任意解析失败
        errors.append("[%s] JSON 解析失败: %s" % (name, e))
        return None


def need_dict(f, obj, path, keys, opt_keys=()):
    """检查 obj 是 dict 且必填键存在、类型与非空符合预期。"""
    if not isinstance(obj, dict):
        err(f, path, "应为对象，实际是 %s" % type(obj).__name__)
        return False
    ok = True
    for k in keys:
        if k not in obj:
            err(f, path, "缺少必填字段 `%s`" % k)
            ok = False
    for k in list(keys) + list(opt_keys):
        if k not in obj:
            continue
        v = obj[k]
        kp = path + "." + k
        if k in ("positions", "tags", "directions", "score_series", "years", "items"):
            if not isinstance(v, list):
                err(f, kp, "应为数组，实际是 %s" % type(v).__name__)
                ok = False
        elif isinstance(v, (list, dict)):
            err(f, kp, "应为标量，实际是 %s" % type(v).__name__)
            ok = False
    return ok


def need_str(f, obj, path, keys, allow_empty=()):
    for k in keys:
        if k not in obj:
            continue
        v = obj[k]
        if not isinstance(v, str):
            err(f, path + "." + k, "应为字符串，实际是 %s" % type(v).__name__)
        elif not v.strip() and k not in allow_empty:
            err(f, path + "." + k, "不应为空")
        elif "\r" in v or "\n" in v and k != "detail":
            # 换行会让 JSON 与前端渲染出现不可预期差异，detail 允许分行
            warn(f, path + "." + k, "含有换行符")


def need_enum(f, obj, path, key, allowed):
    if key in obj and obj[key] not in allowed:
        err(f, path + "." + key, "取值 %r 不在允许集合 %s 内" % (obj[key], sorted(allowed)))


def need_date(f, obj, path, key, allow_empty=True):
    if key not in obj:
        return
    v = obj[key]
    if v == "" and allow_empty:
        return
    if not isinstance(v, str) or not DATE_RE.match(v):
        err(f, path + "." + key, "应为 YYYY-MM-DD，实际是 %r" % (v,))


def need_int_range(f, obj, path, key, lo, hi):
    if key not in obj:
        return
    v = obj[key]
    if isinstance(v, bool) or not isinstance(v, int):
        err(f, path + "." + key, "应为整数，实际是 %s" % type(v).__name__)
    elif not (lo <= v <= hi):
        err(f, path + "." + key, "应在 %d ~ %d 之间，实际是 %d" % (lo, hi, v))


# ------------------------------------------------------------
# schools.json
# ------------------------------------------------------------
def check_schools(data, f="schools.json"):
    if data is None:
        return
    if not isinstance(data, list):
        err(f, "$", "顶层应为数组")
        return
    if not data:
        err(f, "$", "数组为空")
        return
    seen_names = set()
    for i, s in enumerate(data):
        p = "$[%d]" % i
        if not need_dict(f, s, p,
                         ["name", "level", "difficulty_index", "directions", "tags",
                          "exam_subjects", "score_lines", "last_updated",
                          "discipline_grade", "discipline_note", "score_series"],
                         opt_keys=["discipline", "books", "retest", "enrollment"]):
            continue
        need_str(f, s, p, ["name", "level", "exam_subjects", "score_lines", "last_updated"],
                 allow_empty=("score_lines",))
        need_str(f, s, p, ["discipline_grade", "discipline_note"], allow_empty=("discipline_grade", "discipline_note"))
        need_int_range(f, s, p, "difficulty_index", 0, 100)
        need_enum(f, s, p, "discipline_grade", DISCIPLINE_GRADES)

        name = s.get("name")
        if isinstance(name, str):
            if name in seen_names:
                err(f, p + ".name", "院校名重复: %r" % name)
            seen_names.add(name)

        dirs = s.get("directions")
        if isinstance(dirs, list):
            if not dirs:
                err(f, p + ".directions", "不应为空数组（前端按方向渲染）")
            for j, d in enumerate(dirs):
                if not isinstance(d, str) or not d.strip():
                    err(f, "%s.directions[%d]" % (p, j), "应为非空字符串")
        tags = s.get("tags")
        if isinstance(tags, list):
            for j, t in enumerate(tags):
                if not isinstance(t, str) or not t.strip():
                    err(f, "%s.tags[%d]" % (p, j), "应为非空字符串")

        need_date(f, s, p, "last_updated", allow_empty=False)

        # 层次与标签一致性：K-2 / K-8 那一类语义漂移的自动化拦截
        level = s.get("level", "")
        if isinstance(level, str):
            if level == "普通" and any(x in level for x in ("985", "211", "双一流")):
                err(f, p + ".level", "层次为「普通」却含 985/211/双一流")
            if level in ("985", "211", "双一流") and isinstance(tags, list):
                # 层次标签与 tags 里的一致性：985 必然也是 211/双一流，缺了多半是漏填
                for must_tag in ("985", "211", "双一流"):
                    if level == "985" and must_tag not in tags and must_tag != "985":
                        warn(f, p + ".tags", "层次为 985，但标签里缺少「%s」" % must_tag)
                if level == "双一流" and "普通一本" in tags:
                    err(f, p + ".tags", "层次为双一流却带「普通一本」标签")

        # 复试线结构完整性（K-9）
        series = s.get("score_series")
        if isinstance(series, list):
            if not series:
                err(f, p + ".score_series", "为空：前端将只能回退到纯文本字段")
            for gi, g in enumerate(series):
                gp = "%s.score_series[%d]" % (p, gi)
                if not need_dict(f, g, gp, ["label", "years"]):
                    continue
                if not isinstance(g.get("label"), str):
                    err(f, gp + ".label", "应为字符串（可为空串）")
                years = g.get("years")
                if isinstance(years, list):
                    if not years:
                        err(f, gp + ".years", "不应为空数组")
                    for yi, y in enumerate(years):
                        yp = "%s.years[%d]" % (gp, yi)
                        if not need_dict(f, y, yp, ["year", "text"]):
                            continue
                        if not isinstance(y.get("year"), int):
                            err(f, yp + ".year", "应为整数")
                        elif not YEAR_RE.match(str(y["year"])):
                            err(f, yp + ".year", "不像年份: %r" % y["year"])
                        elif y["year"] == 2021:
                            err(f, yp + ".year", "2021 系已知历史残留数据，应清理")
                        if not isinstance(y.get("text"), str) or not y["text"].strip():
                            err(f, yp + ".text", "应为非空字符串")

    # 难度分档覆盖性（K-1 的回归保护）：5 档里至少要能筛出高难度
    hi = [s for s in data if isinstance(s.get("difficulty_index"), int) and s["difficulty_index"] >= 80]
    if not hi:
        warn(f, "$", "没有任何院校难度指数 >= 80，「高难度」筛选将会是空列表")


# ------------------------------------------------------------
# careers.json
# ------------------------------------------------------------
def check_careers(data, f="careers.json"):
    if data is None:
        return
    if not isinstance(data, list) or not data:
        err(f, "$", "顶层应为非空数组")
        return
    seen = set()
    total_positions = 0
    for i, d in enumerate(data):
        p = "$[%d]" % i
        if not need_dict(f, d, p,
                         ["direction", "intro", "positions", "demand", "demand_level",
                          "category", "salary_label", "salary_level", "detail"]):
            continue
        need_str(f, d, p, ["direction", "intro", "demand", "salary_label", "detail"])
        need_enum(f, d, p, "demand_level", DEMAND_LEVELS)
        need_enum(f, d, p, "category", JOB_CATEGORIES)
        need_int_range(f, d, p, "salary_level", 1, 5)
        name = d.get("direction")
        if isinstance(name, str):
            if name in seen:
                err(f, p + ".direction", "方向名重复: %r" % name)
            seen.add(name)
        pos = d.get("positions")
        if isinstance(pos, list):
            total_positions += len(pos)
            if not pos:
                err(f, p + ".positions", "不应为空数组")
            for j, x in enumerate(pos):
                if not isinstance(x, str) or not x.strip():
                    err(f, "%s.positions[%d]" % (p, j), "应为非空字符串")
        else:
            err(f, p + ".positions", "必须是数组（前端按数组渲染岗位名）")
        detail = d.get("detail")
        if isinstance(detail, str) and len(detail) < 30:
            warn(f, p + ".detail", "内容过短（%d 字），可能不是完整介绍" % len(detail))
    info(f, "共 %d 个方向 / %d 个岗位（页头统计由前端按此动态计算，不要硬编码）" % (len(data), total_positions))


# ------------------------------------------------------------
# jobs.json
# ------------------------------------------------------------
def check_jobs(data, f="jobs.json"):
    if data is None:
        return
    if not isinstance(data, list) or not data:
        err(f, "$", "顶层应为非空数组")
        return
    for i, j in enumerate(data):
        p = "$[%d]" % i
        if not need_dict(f, j, p,
                         ["company", "salary", "position", "location", "experience",
                          "tags", "type", "source", "collected_at", "url"]):
            continue
        need_str(f, j, p, ["company", "salary", "position", "location", "experience", "source"])
        need_str(f, j, p, ["url"], allow_empty=("url",))
        need_enum(f, j, p, "type", JOB_TYPES)
        need_date(f, j, p, "collected_at", allow_empty=False)
        tags = j.get("tags")
        if isinstance(tags, list):
            for k, t in enumerate(tags):
                if not isinstance(t, str) or not t.strip():
                    err(f, "%s.tags[%d]" % (p, k), "应为非空字符串")
    student = [j for j in data if j.get("type") in ("实习", "校招")]
    if not student:
        warn(f, "$", "没有任何「实习 / 校招」条目——页面不要宣称覆盖实习/校招"
                     "（审查报告 J-2 就是因为文案宣称了而数据没有）")


# ------------------------------------------------------------
# recruit.json（流水线产出，可选）
# ------------------------------------------------------------
def check_recruit(data, f="recruit.json"):
    if data is None:
        return
    if not need_dict(f, data, "$", ["generated_at", "total", "items"]):
        return
    need_date(f, data, "$", "generated_at", allow_empty=False)
    items = data.get("items")
    if not isinstance(items, list):
        err(f, "$.items", "应为数组")
        return
    if data.get("total") != len(items):
        err(f, "$.total", "与 items 长度不一致：total=%r, len=%d" % (data.get("total"), len(items)))
    for i, it in enumerate(items):
        p = "$.items[%d]" % i
        if not need_dict(f, it, p, ["title", "url", "source", "published_at", "type", "tags"]):
            continue
        need_str(f, it, p, ["title", "source"])
        need_str(f, it, p, ["url"], allow_empty=("url",))
        need_enum(f, it, p, "type", RECRUIT_TYPES)
        need_date(f, it, p, "published_at")
        url = it.get("url")
        if isinstance(url, str) and url and not url.startswith(("http://", "https://")):
            err(f, p + ".url", "必须是 http/https 链接，实际是 %r" % url[:60])
    info(f, "招聘资讯 %d 条（实习 %d / 校招 %d / 社招 %d）"
         % (len(items),
            sum(1 for x in items if x.get("type") == "实习"),
            sum(1 for x in items if x.get("type") == "校招"),
            sum(1 for x in items if x.get("type") == "社招")))


def main():
    ap = argparse.ArgumentParser(description="校验 docs/data 下的受管数据文件")
    ap.add_argument("--data-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "docs", "data"))
    args = ap.parse_args()
    d = args.data_dir

    check_schools(load(d, "schools.json", True))
    check_careers(load(d, "careers.json", True))
    check_jobs(load(d, "jobs.json", True))
    check_recruit(load(d, "recruit.json", False))

    print("=" * 60)
    print("数据文件结构校验 · %s" % d)
    print("=" * 60)
    for line in infos:
        print("  [信息] " + line)
    for line in warnings:
        print("  [警告] " + line)
    for line in errors:
        print("  [错误] " + line)
    print("-" * 60)
    print("错误 %d / 警告 %d" % (len(errors), len(warnings)))
    if errors:
        print("校验未通过：请先修好上面的错误，再提交/发布数据。")
        return 1
    print("校验通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
