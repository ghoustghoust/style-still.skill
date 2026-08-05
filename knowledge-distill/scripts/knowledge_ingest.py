#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""knowledge_ingest.py — 模式 C 原料抽取器
把文件夹里的 docx/pptx/xlsx/md/txt/pdf(需 PyMuPDF) 抽取成带页码标记的 .txt，
输出到 <输出目录>/_extract/，并生成 manifest.json。

用法：
  python knowledge_ingest.py <原料文件夹> -o <输出目录>
  python knowledge_ingest.py <原料文件夹> -o <输出目录> --ext docx,pptx

零第三方依赖可跑 md/txt/docx/pptx/xlsx；pdf 需要 pip install pymupdf。
"""
import argparse, json, os, re, sys, zipfile

TEXT_EXT = {".md", ".txt"}
ZIP_EXT = {".docx", ".pptx", ".xlsx"}


def read_text(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def read_pptx(path):
    out = []
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            (n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"(\d+)", n).group(1)),
        )
        for i, name in enumerate(slides, 1):
            xml = z.read(name).decode("utf-8", errors="ignore")
            texts = re.findall(r"<a:t>([^<]*)</a:t>", xml)
            out.append(f"\n=== 幻灯片{i} ===\n" + "\n".join(t for t in texts if t.strip()))
    return "\n".join(out)


def read_xlsx(path):
    out = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            xml = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
            shared = re.findall(r"<t[^>]*>([^<]*)</t>", xml)
        for name in sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)):
            xml = z.read(name).decode("utf-8", errors="ignore")
            out.append(f"\n=== {name} ===")
            for row in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
                cells = []
                for t, v in re.findall(r'<c[^>]*?t="?(\w+)?"?[^>]*>(?:<v>([^<]*)</v>)?', row):
                    if t == "s" and v and v.isdigit() and int(v) < len(shared):
                        cells.append(shared[int(v)])
                    elif v:
                        cells.append(v)
                if cells:
                    out.append(" | ".join(cells))
    return "\n".join(out)


def read_pdf(path):
    try:
        import fitz
    except ImportError:
        return None  # 标记需要 PyMuPDF
    doc = fitz.open(path)
    return "\n".join(f"\n=== 第{i}页 ===\n" + pg.get_text() for i, pg in enumerate(doc, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--ext", help="只处理这些扩展名，逗号分隔，如 docx,pptx")
    args = ap.parse_args()

    exts = set("." + e.strip(".").lower() for e in args.ext.split(",")) if args.ext else TEXT_EXT | ZIP_EXT | {".pdf"}
    ex_dir = os.path.join(args.out, "_extract")
    os.makedirs(ex_dir, exist_ok=True)
    manifest = []

    for root, _, files in os.walk(args.folder):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, args.folder)
            entry = {"file": rel, "ext": ext, "bytes": os.path.getsize(path)}
            try:
                if ext in TEXT_EXT:
                    text = read_text(path)
                elif ext == ".docx":
                    text = read_docx(path)
                elif ext == ".pptx":
                    text = read_pptx(path)
                elif ext == ".xlsx":
                    text = read_xlsx(path)
                elif ext == ".pdf":
                    text = read_pdf(path)
                else:
                    continue
                if text is None:
                    entry["status"] = "skipped: 需要 PyMuPDF（pip install pymupdf）"
                else:
                    chars = len(re.sub(r"\s", "", text))
                    entry["chars"] = chars
                    if chars == 0:
                        entry["status"] = "0文本（纯图片/扫描件，待 OCR）"
                    else:
                        out_name = re.sub(r'[\\/:*?"<>|]', "_", rel) + ".txt"
                        with open(os.path.join(ex_dir, out_name), "w", encoding="utf-8") as f:
                            f.write(f"# 来源: {rel}\n" + text)
                        entry["status"] = "ok"
            except Exception as e:
                entry["status"] = f"fail: {type(e).__name__}"
            manifest.append(entry)

    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    ok = sum(1 for e in manifest if e.get("status") == "ok")
    zero = sum(1 for e in manifest if "0文本" in e.get("status", ""))
    fail = len(manifest) - ok - zero
    print(f"处理 {len(manifest)} 个文件：成功 {ok}，0文本待OCR {zero}，跳过/失败 {fail}")
    print(f"抽取结果: {ex_dir}  清单: {os.path.join(args.out, 'manifest.json')}")


if __name__ == "__main__":
    main()
