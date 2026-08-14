# style-still Roadmap

**Current focus**: v1.0 已发布（GitHub: ghoustghoust/style-still.skill），下一阶段做真机兼容性验证与存量档案校准

## Milestones

- [x] v1.0：双模式 skill + 两份实战档案（孙亮朝 v4、樊登 v2）+ README + GitHub 发布
- [ ] 真机验证：Claude Code / QClaw / WorkBuddy / Codex 各装一次，确认触发与执行
- [ ] 孙亮朝档案开场校准：补跑 `scan_openings.py`，更新其「切入必杀技库」占比
- [ ] 增量迭代：写作实战反馈 → 档案迭代日志 → skill 打包 → 推送更新

## Open Questions

1. QClaw / WorkBuddy 对语义触发的实际支持程度未知——若某平台不触发，需要补平台专属安装说明。
2. 历史迁移：v1.0 开发过程的四轮迭代教训是否做 selective_migrate（目前散落在对话中，档案内的迭代日志已各存一份）？
