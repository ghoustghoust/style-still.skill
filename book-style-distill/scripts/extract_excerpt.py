#!/usr/bin/env python3
"""extract_excerpt.py — 从书籍文件中提取代表性采样与量化统计，供文风蒸馏使用。

支持格式：txt / md / epub（纯标准库）。pdf 需安装 pypdf（pip install pypdf）。

用法：
    python extract_excerpt.py <书籍文件> [--out 输出目录] [--samples 采样段数] [--chars 每段字数]

输出（默认写到 ./style-distill-<书名>/）：
    stats.md     量化统计报告（句长、段长、对白占比、标点画像等）
    samples.md   代表性采样（开头/中间/结尾 + 均匀分布采样 + 高特征段落）
"""
import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter
from html import unescape


def read_txt(path):
    for enc in ("utf-8", "gb18030", "utf-16", "big5"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    sys.exit(f"无法解码文件：{path}")


def read_epub(path):
    """epub 是 zip 包，提取所有 xhtml/html 正文并去标签。"""
    texts = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist()
                 if re.search(r"\.(x?html?|xml)$", n, re.I) and "toc" not in n.lower()]
        # 按文件名排序近似章节顺序
        for name in sorted(names):
            raw = z.read(name).decode("utf-8", errors="ignore")
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
            raw = re.sub(r"<[^>]+>", "\n", raw)
            texts.append(unescape(raw))
    return "\n".join(texts)


def read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("PDF 支持需要 pypdf：pip install pypdf（建议装在虚拟环境中）")
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        return read_txt(path)
    if ext == ".epub":
        return read_epub(path)
    if ext == ".pdf":
        return read_pdf(path)
    sys.exit(f"不支持的格式：{ext}（支持 txt/md/epub/pdf）")


def clean(text):
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text):
    parts = re.split(r"(?<=[。．！？；…!?;])", text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    return sorted_vals[f] if f + 1 >= len(sorted_vals) else \
        sorted_vals[f] + (sorted_vals[f + 1] - sorted_vals[f]) * (k - f)


def compute_stats(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if len(p.strip()) >= 5]
    sents = split_sentences(text)
    sent_lens = sorted(len(s) for s in sents)
    para_lens = sorted(len(p) for p in paras)

    dialogue_chars = sum(len(m) for m in re.findall(r"[「『“\"](.*?)[」』”\"]", text, flags=re.S))
    puncts = Counter(c for c in text if c in "。．，、！？；：…—「」『』“”‘’!?;:,.")

    n = len(text)
    stats = {
        "总字数": n,
        "段落数": len(paras),
        "句子数": len(sents),
        "句长_均值": round(sum(sent_lens) / max(len(sent_lens), 1), 1),
        "句长_中位数": round(percentile(sent_lens, 0.5), 1),
        "句长_P90": round(percentile(sent_lens, 0.9), 1),
        "句长_P10": round(percentile(sent_lens, 0.1), 1),
        "段长_均值": round(sum(para_lens) / max(len(para_lens), 1), 1),
        "段长_中位数": round(percentile(para_lens, 0.5), 1),
        "对白占比%": round(100 * dialogue_chars / max(n, 1), 1),
        "每千字标点": {k: round(1000 * v / max(n, 1), 1) for k, v in puncts.most_common()},
    }
    # 短句占比（<=10字）与长句占比（>=50字）
    stats["短句占比%(<=10字)"] = round(100 * sum(1 for s in sent_lens if s <= 10) / max(len(sent_lens), 1), 1)
    stats["长句占比%(>=50字)"] = round(100 * sum(1 for s in sent_lens if s >= 50) / max(len(sent_lens), 1), 1)
    return stats


def sample_passages(text, n_samples, chars):
    """开头/中间/结尾各一段 + 其余均匀采样。"""
    L = len(text)
    if L <= chars * (n_samples + 1):
        return [("全文（较短）", text)]
    # 跳过前置垃圾（目录/版权页）：从第一个 >=200 字的正文段落开始算“开头”
    start = 0
    for m in re.finditer(r"\n\s*\n", text):
        seg = text[start:m.start()]
        if len(seg.strip()) >= 200:
            break
        start = m.end()
    else:
        start = 0
    picks = [("开头", start), ("结尾", L - chars)]
    mid_slots = max(n_samples - 2, 1)
    for i in range(mid_slots):
        pos = int(L * (i + 1) / (mid_slots + 1))
        picks.append((f"中部采样{i + 1}（约{100 * pos // L}%处）", pos))
    out = []
    for label, pos in picks:
        seg = text[pos:pos + chars]
        # 对齐到段落边界
        first_nl = seg.find("\n")
        if 0 < first_nl < 100:
            seg = seg[first_nl + 1:]
        out.append((label, seg.strip()))
    return out


def find_signature_passages(paras_limit=3, text=""):
    """找特征最强的段落：含对白最多的、金句密度高的（短句密集+感叹/反问）。"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if 50 <= len(p.strip()) <= 800]
    if not paras:
        return []
    def score(p):
        s = 0
        s += 3 * len(re.findall(r"[「『“]", p))          # 对白
        s += 2 * len(re.findall(r"[！？!?]", p))           # 感叹/反问
        short = len([x for x in split_sentences(p) if len(x) <= 12])
        s += short                                          # 短句密度
        return s
    top = sorted(paras, key=score, reverse=True)[:paras_limit]
    return [(f"高特征段落{i + 1}", p) for i, p in enumerate(top)]


def main():
    ap = argparse.ArgumentParser(description="书籍文风蒸馏：采样与统计")
    ap.add_argument("file", help="书籍文件路径（txt/md/epub/pdf）")
    ap.add_argument("--out", help="输出目录（默认 ./style-distill-<书名>）")
    ap.add_argument("--samples", type=int, default=8, help="采样段数（默认8）")
    ap.add_argument("--chars", type=int, default=1500, help="每段采样字数（默认1500）")
    args = ap.parse_args()

    raw = load_text(args.file)
    text = clean(raw)
    if len(text) < 2000:
        sys.exit("文本过短（<2000字），无法进行有效蒸馏。请提供更完整的文本。")

    title = os.path.splitext(os.path.basename(args.file))[0]
    out_dir = args.out or f"style-distill-{title}"
    os.makedirs(out_dir, exist_ok=True)

    stats = compute_stats(text)
    samples = sample_passages(text, args.samples, args.chars)
    signatures = find_signature_passages(text=text)

    with open(os.path.join(out_dir, "stats.md"), "w", encoding="utf-8") as f:
        f.write(f"# 《{title}》量化统计\n\n")
        f.write("| 指标 | 数值 |\n|------|------|\n")
        for k, v in stats.items():
            if k != "每千字标点":
                f.write(f"| {k} | {v} |\n")
        f.write("\n## 标点画像（每千字出现次数）\n\n")
        for k, v in stats["每千字标点"].items():
            f.write(f"- `{k}`：{v}\n")

    with open(os.path.join(out_dir, "samples.md"), "w", encoding="utf-8") as f:
        f.write(f"# 《{title}》代表性采样\n\n")
        f.write("> 用法：通读全部采样，逐维度做文风分析。每个结论必须引用此处的原文例句作为证据。\n\n")
        for label, seg in samples + signatures:
            f.write(f"\n## {label}\n\n```\n{seg}\n```\n")

    with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"✅ 采样完成：{out_dir}/")
    print(f"   总字数 {stats['总字数']:,} | 句子 {stats['句子数']:,} | 句长中位数 {stats['句长_中位数']}")
    print(f"   对白占比 {stats['对白占比%']}% | 短句占比 {stats['短句占比%(<=10字)']}%")
    print("下一步：通读 samples.md，对照 references/analysis-dimensions.md 逐维度蒸馏。")


if __name__ == "__main__":
    main()
