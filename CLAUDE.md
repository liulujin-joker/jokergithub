# 项目记忆 - CLAUDE.md

## 我参加的竞赛
- **名称**: 中国高校计算机大赛 · AIGC创新赛 (vivo主办)
- **官网**: https://aigc.vivo.com.cn/#/home
- **赛道**: 手机AI助手，未来AI影像体验设计
- **作品**: 小V影像助手 - 手机端AI影像智能体

## 核心作品：vivo-ai-imaging-agent
- **位置**: `D:/git/vivo-ai-imaging-agent/` （也在 `D:/Users/joker/Desktop/vivo-ai-imaging-agent/`）
- **智能体主体**: `main.py` 中的 `VivoImagingAgent` 类
- **架构**: Think → Plan → Execute → Reflect 四阶段认知链路
- **工具**: 10个AI影像工具（增强/风格/构图/消除/美颜/识别/调色/裁剪/扩图/动态）
- **意图解析**: 10种意图类型，17/17测试通过
- **记忆**: 短期+长期双记忆系统

## GitHub
- **仓库**: https://github.com/liulujin-joker/jokergithub
- **公开网站**: https://liulujin-joker.github.io/jokergithub/
- **网站功能**: 静态展示 + 前端智能体交互引擎（JavaScript实现的完整Think-Plan-Execute流程）

## Git 本地路径
- **仓库目录**: `D:\git`
- **远程**: `https://github.com/liulujin-joker/jokergithub.git`

## 运行方式
```bash
cd D:/git/vivo-ai-imaging-agent
python main.py --demo     # 演示模式
python main.py             # 交互对话
python main.py --query "xxx"
```

## 项目关键文件
- `main.py` - 智能体主入口
- `src/agent/planner.py` - 规划器
- `src/agent/intent_parser.py` - 意图解析器
- `src/agent/executor.py` - 工具执行器
- `src/tools/imaging_tools.py` - 10个AI影像工具
- `src/memory/memory_manager.py` - 双记忆系统
- `docs/DESIGN.md` - 完整设计文档
- `index.html` - 公开网站（含前端交互引擎）
