# style-still（文风蒸馏所）

![License](https://img.shields.io/badge/License-MIT-blue) ![Skills](https://img.shields.io/badge/Agent%20Skills-开放标准-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-✓-brightgreen) ![Codex](https://img.shields.io/badge/Codex-✓-brightgreen) ![Agents](https://img.shields.io/badge/兼容-40%2B%20Agents-orange)

> _"把一本书的文风，蒸馏成可复用的写作系统。"_

一个双模式 Agent Skill：**蒸馏**任何一本书/一位作者的文风，产出结构化的《文风档案》；再用档案 **spec 式分步写作/润色**——公众号长文、章节、社媒短文、金句，写出来是那个作者的味道，不是 AI 味。

遵循 Agent Skills 开放标准。Claude Code、Codex、QClaw、WorkBuddy 及 40+ 支持 SKILL.md 的 Agent 都能装。

---

## 它能做什么

**模式 A · 蒸馏**：丢给它一本书（txt/md/epub/pdf）、几段节选，或一个书名

- 脚本全量采样：句长分布、对白占比、标点画像、高特征段落（本地运行，0 token）
- 全书小节开场扫描：开场方式的真实占比，不靠抽样印象
- 16 个维度逐维蒸馏，**每条结论必须附原文例句**——没证据就标「不明显」，不编造
- 产出《文风档案》：叙事结构库、干货配比、力量点指纹、禁区清单、金句公式、切入必杀技……
- 强制验证：用档案仿写一段文字并与原文对比，不像就回改档案

**模式 B · 写作**：说一句「用《XXX》的文风写一篇关于 xxx 的文章」

- spec 式分步确认：选材 → 叙事结构（按命题推荐 2-3 种）→ 切入方式（先交 100 字开头给你过目）→ 大纲 → 正文，绝不闷头写全文
- 四层自检：禁区机械扫描 → 风格一致性 → 内容质量 → 活人感终审（登味/AI 味检测）
- **结构指纹防重复**：每篇登记选题/结构/切入/金句/结尾/造名，连续两篇不得雷同——日更也不乏味
- 润色模式：8 种 AI 味病灶的具体修法

## 适合

- 喜欢某本书/某个作者的文风，想让 AI 照着写
- 公众号、小红书等需要**持续日更且风格统一**的创作
- 想把自己的文章「润色掉 AI 味」

## 不适合

- 纯摘要、标题生成（用别的工具）
- 「通用好文笔」——这个 skill 是有立场的，它只忠于档案里的那一个声音
- 想要一键全自动出稿——它刻意保留分步确认，因为核心创意和真实经历必须来自你

## 安装

在支持 Skill 的 Agent 里直接说：

```
帮我安装这个 skill：https://github.com/ghoustghoust/style-still.skill
```

或手动安装：把 `book-style-distill/` 目录复制到 Agent 的 skills 目录（如 `~/.agents/skills/`），或导入发行包 `book-style-distill.skill`。

**环境要求**：Python 3.8+（仅标准库，零依赖）。没有 Python 也能用——蒸馏脚本只是加速器，手工采样同样可走完全流程。

## 怎么调用

Skill 是**语义触发**的，不用记命令：

| 你说 | 触发 |
|------|------|
| 「蒸馏这本书的文风」+ 拖入电子书 | 模式 A |
| 「提取一下樊登的写作风格」 | 模式 A |
| 「用《学好数学并不难》的文风写一篇关于复利的文章」 | 模式 B |
| 「帮我把这篇稿子润色一下，去掉 AI 味」 | 模式 B 润色 |

## 注意事项

1. **第一手经历不可编造**：若档案标注此约束，写第一人称文章时 Agent 会向你索取真实经历——这是特性不是麻烦，AI 编的经历一眼假
2. **文风档案是证据文档**：每条规则都带原文例句，请保留例句，删除后档案会失去校准能力
3. **Token 消耗**：一次完整蒸馏约 4-6 万 token（与书的长度无关，整书不进上下文，只有采样进）；一次写作约 1-3 万
4. **迭代**：档案是活文档。每次觉得「不像」，把不像的点告诉 Agent，它会把教训写进档案的迭代日志——越用越像

## 文件结构

```
book-style-distill/
├── SKILL.md                        # 双模式主流程（精炼版，含执行纪律与 fallback 钩子）
├── scripts/
│   ├── extract_excerpt.py          # 采样与量化统计（txt/md/epub/pdf）
│   └── scan_openings.py            # 全书小节开场方式全量扫描
├── references/
│   ├── analysis-dimensions.md      # 16 维蒸馏清单（前 8 维定味道，后 8 维定细部）
│   └── writing-workflow.md         # spec 式写作流程 + 四层自检 + 防重复
└── assets/
    └── style-profile-template.md   # 《文风档案》输出模板
```

## License

MIT
