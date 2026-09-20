# -*- coding: utf-8 -*-
"""
RSS 源可达性探针（GitHub Actions 专用）

为什么需要它：本项目在国内开发，而流水线跑在 GitHub Actions 的 ubuntu-latest
（Azure 境外 IP）。国内能打开的源，海外 IP 可能被地域封锁或反爬拦截，反之亦然。
本地测出来的结论对 Actions **不成立**，必须用真实 runner 环境跑一次。

用法：
    python tools/probe_sources.py              # 只测 tools/source_candidates.txt 里的候选源
    python tools/probe_sources.py --with-config # 顺带把 config.yaml 里在用的源也测一遍

结果写到 stdout、tools/probe_result.json，并追加到 GitHub Actions 的 Job Summary。
"""
import io
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone

import feedparser
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAND_FILE = os.path.join(HERE, "source_candidates.txt")
RESULT_FILE = os.path.join(HERE, "probe_result.json")

# 与 daily_report.py 的 fetch_all_feeds 保持一致：同样的 UA、同样的超时、同样的解析器。
# 探针的意义就在于「复现流水线的抓取方式」，任何差异都会让结论失真。
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SOCKET_TIMEOUT = 20


def load_candidates():
    """读取候选源清单：每行 `源名称<TAB>URL`，# 开头为注释。"""
    items = []
    if not os.path.exists(CAND_FILE):
        return items
    with io.open(CAND_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split(None, 1)
            if len(parts) != 2:
                continue
            items.append((parts[0].strip(), parts[1].strip()))
    return items


def load_config_feeds():
    """复用流水线的配置读取，拿到 config.yaml 里在用的源。"""
    try:
        sys.path.insert(0, ROOT)
        import daily_report as dr
        cfg = dr.load_config()
        return list((cfg.get("rss_feeds") or {}).items())
    except Exception as e:  # 配置读取失败不应影响候选源探测
        print("[warn] 读取 config.yaml 失败: %s: %s" % (type(e).__name__, e))
        return []


def probe(name, url):
    """单源探测：记录状态码、字节数、解析出的条目数、耗时。"""
    start = time.time()
    rec = {"name": name, "url": url, "http_code": None, "bytes": 0,
           "entries": 0, "feed_title": "", "elapsed": 0.0, "error": "", "ok": False}
    try:
        resp = requests.get(url, timeout=(10, 20), headers={"User-Agent": UA})
        rec["http_code"] = resp.status_code
        rec["bytes"] = len(resp.content)
        if resp.ok and resp.content:
            feed = feedparser.parse(resp.content)
            rec["entries"] = len(feed.entries)
            rec["feed_title"] = (feed.feed.get("title") or "")[:60]
            if feed.bozo and not feed.entries:
                rec["error"] = "解析失败：%s" % str(feed.bozo_exception)[:80]
            else:
                rec["ok"] = True
    except Exception as e:
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:100])
    rec["elapsed"] = round(time.time() - start, 2)
    return rec


def main():
    socket.setdefaulttimeout(SOCKET_TIMEOUT)

    targets = load_candidates()
    if "--with-config" in sys.argv:
        existing = set(u for _, u in targets)
        for n, u in load_config_feeds():
            if u not in existing:
                targets.append((n, u))

    if not targets:
        print("没有待测目标：请检查 tools/source_candidates.txt")
        return 1

    print("=" * 72)
    print("RSS 源可达性探针（GitHub Actions 真实环境）")
    print("时间：%s" % datetime.now(timezone.utc).isoformat())
    print("目标数：%d" % len(targets))
    print("=" * 72)

    results = []
    for name, url in targets:
        rec = probe(name, url)
        results.append(rec)
        flag = "OK  " if rec["ok"] else "FAIL"
        print("[%s] %-34s %s/%dB/%d条 %.1fs %s" % (
            flag, name, rec["http_code"], rec["bytes"], rec["entries"], rec["elapsed"], rec["error"]))

    ok = sum(1 for r in results if r["ok"])
    summary = ["# RSS 源可达性探测结果（GitHub Actions）", "",
               "- 运行环境：%s / runner IP 见下方" % os.environ.get("RUNNER_OS", "?"),
               "- 探测时间（UTC）：%s" % datetime.now(timezone.utc).isoformat(),
               "- 结果：**%d/%d 可用**" % (ok, len(results)), "",
               "| 源 | HTTP | 字节 | 条目 | 耗时 | 判定 | 备注 |",
               "|---|---|---|---|---|---|---|"]
    for r in results:
        summary.append("| %s | %s | %d | %d | %.1fs | %s | %s |" % (
            r["name"], r["http_code"], r["bytes"], r["entries"], r["elapsed"],
            "可用" if r["ok"] else "**不可用**", (r["error"] or r["feed_title"])[:60]))

    md = "\n".join(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with io.open(step_summary, "a", encoding="utf-8") as f:
            f.write(md + "\n")

    with io.open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                   "runner_os": os.environ.get("RUNNER_OS", ""),
                   "total": len(results), "ok": ok, "results": results},
                  f, ensure_ascii=False, indent=2)

    print("\n" + md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
