#!/usr/bin/env python3
"""scan_openings.py — 扫描全书所有小节的「开场第一段」，统计开场方式分布。

用途：修正抽样偏差。蒸馏时读十几段采样容易产生「作者爱用案例开场」之类的
错觉；本脚本把所有小节标题 + 紧随其后的一段正文全部列出，让开场分布一目了然。

用法：
    python scan_openings.py <书籍文件> [--min-len 40]

输出：终端打印每个小节标题及其开场段前 60 字，供归纳开场方式分布。
"""
import argparse
import re
import sys
import zipfile
from html import unescape


def load_text(path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext in ("txt", "md"):
        for enc in ("utf-8", "gb18030"):
            try:
                with open(path, encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        sys.exit("无法解码文件")
    if ext == "epub":
        texts = []
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist()
                     if re.search(r"\.(x?html?)$", n, re.I) and "toc" not in n.lower()]
            for name in sorted(names):
                raw = z.read(name).decode("utf-8", errors="ignore")
                raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
                raw = re.sub(r"<[^>]+>", "\n", raw)
                texts.append(unescape(raw))
        return "\n".join(texts)
    sys.exit("仅支持 txt/md/epub")


def main():
    ap = argparse.ArgumentParser(description="扫描小节开场方式分布")
    ap.add_argument("file")
    ap.add_argument("--min-len", type=int, default=40, help="正文段最小字数（默认40）")
    args = ap.parse_args()

    text = load_text(args.file)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 小节标题特征：短行、无句末标点、非图表/章节号，且下一行是正文
    results = []
    for i, l in enumerate(lines[:-1]):
        if 3 <= len(l) <= 18 and not re.search(r'[。，”“：？！…）]$', l) \
                and not l.startswith(("第", "图", "《", "Cover")):
            nxt = lines[i + 1]
            if len(nxt) >= args.min_len:
                results.append((l, nxt))

    print(f"共识别 {len(results)} 个小节\n")
    for title, first in results:
        print(f"【{title}】")
        print(f"  开场：{first[:60]}")
    print("\n下一步：人工归纳开场方式占比（议论/定义/承接/引证/设问/案例/互动指令），写入文风档案的「开头切入方式库」。")


if __name__ == "__main__":
    main()
