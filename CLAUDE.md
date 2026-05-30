# Claude 项目记忆文件

> 📌 这个文件用于记录我的项目需求、偏好和上下文，Claude 会在每次对话中自动读取。

---

## 🧑 关于我

- **角色**: 学生 👨‍🎓
- **偏好语言**: 中文为主，代码注释可用英文
- **代码风格**: 注重可读性、重视注释、喜欢先理解原理再动手
- **沟通风格**: 详细解释、循序渐进、多用类比帮助理解

---

## 📋 当前项目：vivo AIGC创新赛 - 小V影像助手 v2.0

- **描述**: 中国高校计算机大赛·AIGC创新赛，赛道"手机AI助手，未来AI影像体验设计"
- **优先级**: 🔴高
- **状态**: ✅ 已完成全部交付物
- **官网**: https://aigc.vivo.com.cn/#/home
- **作品**: 小V影像助手 - 手机端AI影像智能体

### 📁 项目路径
| 位置 | 用途 |
|------|------|
| `D:/git/vivo-ai-imaging-agent/` | 主开发目录（Git 跟踪） |
| `D:/Users/joker/Desktop/小V影像助手_v2.0/` | 分发版（359KB，可打包分享） |
| `D:/git/` | Git 仓库根目录（含 index.html 网站） |
| `D:/claude/` | Claude Code 工作区 |

### 🧠 智能体架构 (v2.0)
```
用户输入 → Think (LLM意图解析) → Plan (Function Calling选工具) 
→ Execute (真实AI工具) → Reflect (LLM生成回复)
```
- **LLM 模式**: DeepSeek Function Calling (`python main.py --llm`)
- **规则引擎模式**: 正则关键词匹配 (`python main.py` / `python main.py --demo`)
- 意图解析: 10种意图类型，17/17测试通过

### 🛠️ 10大AI影像工具
| # | 工具 | 状态 | 实现方式 |
|---|------|------|----------|
| 1 | 📸 photo_enhance | ✅ REAL | PIL ImageEnhance 自适应增强 |
| 2 | 🎨 style_transfer | ✅ REAL | PIL滤镜(7种) + HF API(AI风格) |
| 3 | 📐 composition_guide | ✅ REAL | PIL+numpy 边缘检测+三分法评分 |
| 4 | 🧹 object_remove | 🔲 Demo | 需 SAM+LaMa 云端API |
| 5 | ✨ portrait_beautify | ✅ REAL | PIL 肤色检测+高斯柔焦+美白 |
| 6 | 🔍 scene_recognize | ✅ REAL | HF CLIP API → 传统图像统计回退 |
| 7 | 🎬 color_grading | ✅ REAL | PIL+numpy RGB矩阵变换(9种预设) |
| 8 | ✂️ smart_crop | ✅ REAL | PIL 显著性检测+多比例评分 |
| 9 | 🔲 ai_expand | 🔲 Demo | 需 SD Outpainting 云端API |
| 10 | 🎬 motion_photo | ✅ REAL | PIL 视差3D+波浪扭曲→输出GIF |

**8/10 工具真实实现 (80%)**

### 🚀 运行方式
```bash
cd D:/git/vivo-ai-imaging-agent
python main.py              # 规则引擎交互模式
python main.py --llm        # LLM驱动模式(需 DEEPSEEK_API_KEY)
python main.py --demo       # 演示模式
python main.py --check      # 系统状态检查
python main.py --query "xxx" # 单次查询
python server/api_server.py  # 启动 FastAPI 后端 (http://127.0.0.1:8000)
```

### 📦 交付物
| 产物 | 大小 | 位置 |
|------|------|------|
| 🌐 **GitHub Pages 网站** | - | https://liulujin-joker.github.io/jokergithub/ |
| 📱 **Android APK** | 47MB | `D:/git/vivo-ai-imaging-agent/flutter_app/build/app/outputs/flutter-apk/app-release.apk` |
| 🌐 **Flutter Web** | 31MB | `flutter_app/build/web/` |
| 🖥️ **桌面启动器** | 1KB | `D:/Users/joker/Desktop/小V影像助手_启动.bat` |
| 📦 **分发包** | 359KB | `D:/Users/joker/Desktop/小V影像助手_v2.0/` (含项目+启动器) |

### 📱 APK 模式说明 (2026-05-30 更新)
- **离线 Demo 模式**: 不花 Token！纯本地模拟回复，覆盖全部10个工具
  - 触发条件: 未配置服务器或连接失败
  - 关键词匹配: 增强/风格/构图/消除/美颜/场景/调色/裁剪/扩图/动态
  - 每个工具展示完整 Think→Plan→Execute→Reflect 流程
- **在线模式**: 需要后端服务 + DeepSeek API Key，花 Token
  - 真机需配电脑 IP: 点 ⚙️ → 输入 `http://192.168.x.x:8000`
  - 手机和电脑必须同 WiFi，防火墙放行 8000 端口
- **⚙️ 服务器设置**: AppBar 齿轮按钮 → 输入地址 → 测试连接 → 保存
  - SharedPreferences 持久化，下次自动加载
  - 支持: 模拟器 `10.0.2.2` / 本机 `localhost` / 自定义 IP
- **⚠️ `10.0.2.2` 仅限模拟器**，真机必须用电脑局域网 IP
- Token 花费: deepseek-chat ≈ ¥1/百万 token，日常聊天几毛钱

### 🔧 启动脚本修复 (2026-05-30)
- `>/dev/null` → `>nul` (Windows cmd 不认识 `/dev/null`)
- 服务器改在独立窗口启动 (`start /D`)，不再阻塞
- 新增 3 步检查: Python → 依赖 → API Key
- 依赖修复: requirements.txt 补了 `fastapi`/`uvicorn`/`python-multipart`

### 🌐 GitHub
- **仓库**: https://github.com/liulujin-joker/jokergithub
- **公开网站**: https://liulujin-joker.github.io/jokergithub/
- **Release**: v2.0.0 (APK 下载)
- **Git 路径**: `D:\git`，远程 `git@github.com:liulujin-joker/jokergithub.git` (SSH)
- **网站源码**: `D:/git/index.html` (单文件 HTML+CSS+JS，含完整前端智能体引擎)

### 📂 项目文件结构
```
vivo-ai-imaging-agent/
├── main.py                     # 智能体主入口
├── server/api_server.py        # FastAPI 后端 (端口8000)
├── server/chat.html            # Web 聊天界面
├── desktop_launcher.py         # Python 桌面启动器
├── requirements.txt            # Python 依赖 (chromadb可选)
├── .env.example / .env         # API Key 配置 (DEEPSEEK_API_KEY)
├── flutter_app/                # Flutter 移动端 (Dart/Android/Web)
├── mobile_app/                 # 独立 APK 版 (含连接界面)
├── config/settings.py          # 模型/工具/记忆 全配置
├── src/
│   ├── llm/client.py           # LLM 统一接口 (DeepSeek/vivo/OpenAI)
│   ├── agent/
│   │   ├── llm_planner.py      # LLM 驱动规划器 (Function Calling)
│   │   ├── planner.py          # 规则引擎规划器 (Demo回退)
│   │   ├── executor.py         # 工具执行器
│   │   └── intent_parser.py    # 意图解析器 (正则关键词)
│   ├── tools/
│   │   ├── real_tools.py       # 8个真实工具 (PIL/HF API, 1071行)
│   │   ├── imaging_tools.py    # 10个工具骨架
│   │   └── tool_registry.py    # 插件化注册中心
│   ├── memory/memory_manager.py # 短期+长期双记忆 (纯Python,不依赖chromadb)
│   ├── models/schemas.py       # 数据模型
│   └── utils/                  # 日志/图像工具
└── docs/DESIGN.md              # 完整设计文档
```

### 🔑 环境配置
- **Python**: 3.10.8 (`C:/Program Files/Python310`)
- **DeepSeek API Key**: 需在 `.env` 中配置 `DEEPSEEK_API_KEY`
- **HuggingFace Token**: 可选，用于 CLIP 场景识别 (`HF_API_TOKEN`)
- **Java**: OpenJDK 21.0.6 (Anaconda: `C:/ProgramData/anaconda3/pkgs/openjdk-21.0.6/`)
  - ⚠️ 系统默认 Java 8 太旧，Android SDK 需 Java 17+，用 `export JAVA_HOME=...` 切换

### 📱 Flutter 构建环境
- **Flutter SDK**: 3.38.9 (`D:/flutter/`)，Dart 3.10.8
- **Android SDK**: `D:/Android/` (platforms 34/35/36, build-tools 34/35/36)
- **NDK**: 28.2.13676358 (Side by side)
- **CMake**: 3.22.1
- **构建**: `cd flutter_app && flutter build apk --release` (46.9MB)
- **Web**: `flutter build web` (31MB)
- **已修复 Bug**: `chat_screen.dart` 中 `_QuickChip` 的 `onTap` 参数从位置改为命名参数
- **⚠️ Android 项目文件是老版 Gradle**，需要 `flutter create --platforms android .` 重新生成

### 🔗 GitHub Release 创建
- 通过 GitHub API + token (`gho_...`) 创建 Release 并上传 APK
- Tag: `v2.0.0`, Release ID: 331913122
- 下载: https://github.com/liulujin-joker/jokergithub/releases/download/v2.0.0/XiaoV_v2.0.0.apk
- `index.html` 已更新：Hero 按钮链到 Releases 页面

### ⚠️ Watt Toolkit 问题与教训
- **进程**: Steam++.exe ×2 + Steam++.Accelerator.exe，管理员权限运行，无法代码 kill
- **WFP 规则**: 驱动级网络过滤，仅重启电脑或 Watt Toolkit 正常退出才能清除
- **症状**: 关掉 Watt Toolkit 后 GitHub HTTPS (443) 仍然不通，其他网站正常
- **解决方案**: 重启电脑 / 从托盘正常退出 Watt Toolkit
- **Git 推送**: 当 HTTPS 被挡时，用 SSH (`git@github.com:...`) 替代
- **大文件下载**: 国内用南京大学镜像 `mirrors.nju.edu.cn/flutter/...` 速度更快

---

## 🎯 当前学习目标

- **主攻方向**: [例如：前端开发 / Python 数据分析 / Java 后端 / AI & 机器学习]
- **当前课程**: [例如：数据结构、操作系统、计算机网络]
- **近期考试/DDL**: [日期 + 科目]
- **长期目标**: [例如：准备实习面试 / 参加竞赛 / 发论文]

---

## 📝 常用命令

```bash
# === 小V影像助手 ===
cd D:/git/vivo-ai-imaging-agent
python main.py --llm                          # LLM 驱动交互
python main.py --demo                         # 演示模式
python main.py --check                        # 系统检查
python server/api_server.py                   # 启动 FastAPI (8000)
pip install -r requirements.txt               # 安装依赖

# === Flutter ===
export PATH="/d/flutter/bin:$PATH"
cd flutter_app
flutter build apk --release                   # 打 APK (~47MB)
flutter build web                             # 打 Web (~31MB)
flutter doctor                                # 环境检查

# === Android SDK ===
export JAVA_HOME="/c/ProgramData/anaconda3/pkgs/openjdk-21.0.6-h5da7b33_0/Library"
export ANDROID_HOME=/d/Android
# sdkmanager 需要 Java 17+

# === Git ===
cd D:/git
git push origin master                        # 推送 (SSH)
git tag v2.0.0 -m "..." && git push --tags    # 创建 Release tag

# === GitHub Release (通过 API) ===
curl -X POST -H "Authorization: token $TOKEN" \
  -d '{"tag_name":"v2.0.0","name":"...","body":"..."}' \
  "https://api.github.com/repos/liulujin-joker/jokergithub/releases"
```

---

## ⚙️ 项目规则 / 约束

1. [例如：所有 API 接口需要加上错误处理]
2. [例如：提交前必须通过 lint 检查]
3. [例如：不要修改 /config 目录下的文件]

## 🤖 工作模式：自主执行，不要反复确认

**核心原则：能直接做的事就不要问，直接干。**

- ✅ 我发出指令后，直接理解意图 → 执行 → 汇报结果，不要反问"要不要做这个？"
- ✅ 常规操作（写代码、改文件、Git 提交、装依赖、运行测试）一律直接执行
- ✅ 只有遇到真正需要我决策的岔路口（比如 2 种完全不同的技术方案，影响面都很大），才停下来问我
- ✅ 小决策自己做主：命名、文件组织、代码风格、工具选择
- ✅ 执行前不需要说"我将要做 X"，直接做，做完汇报结果
- ❌ 不要说"你确定要这样做吗？"
- ❌ 不要说"我建议..."然后等我回复
- ❌ 不要列举选项让我选（除非真的有重大分歧）

---

## 🧩 Skill 库（18 个，在 `.claude/skills/` 下）

### 🦸 元技能
| Skill | 用途 |
|-------|------|
| `/superpower` | 解锁深度思考、自我验证、质量门控 |
| `/skill-creator` | 创建和优化新的 Claude Code Skill |

### 🔧 编程类
| Skill | 用途 |
|-------|------|
| `/code-review` | 社区版代码审查——P0 必改/P1 强烈建议/P2 优化 |
| `/write-tests` | 自动生成单元测试，覆盖边界和异常 |
| `/debug` | 系统化调试——定位根因而非修复症状 |
| `/explain-code` | 逐行讲解代码逻辑，生活化类比 |
| `/refactor` | 重构优化——不改变功能，提升质量 |
| `/git-commit` | 生成 Conventional Commits 规范提交信息 |
| `/project-scaffold` | 快速搭建项目脚手架和技术选型 |
| `/frontend-design` | 生成美观、响应式的 UI 组件（8 种状态全覆盖） |

### 🎓 学习类
| Skill | 用途 |
|-------|------|
| `/learn-topic` | 费曼学习法讲解任何概念，附带学习路径 |
| `/note-organizer` | 把零散笔记整理为结构化知识体系 |
| `/essay-writing` | 学术写作——论文/报告/实验报告 |
| `/presentation` | 演示文稿——答辩/汇报 PPT 大纲和演讲稿 |
| `/humanizer-zh` | 中文润色——去翻译腔、加口语节奏、注入温度 |

### 📊 科研 & 效率类
| Skill | 用途 |
|-------|------|
| `/data-analysis` | 数据分析——清洗/可视化/统计检验 |
| `/pdf` | PDF 全能操作——读取/创建/合并/拆分/提取 |
| `/planning-with-files` | 文件化任务规划——PLAN/TASKS/DECISIONS/STATUS |

---

## 🔌 MCP 服务器（6 个已部署）

> 这些 MCP 服务器扩展了 Claude 的能力，全部通过 `claude mcp add` 注册为 stdio 模式，项目级生效。
> 配置文件位置：`C:\Users\joker\.claude.json` [project: D:\claude]

### 🌐 fetch — 网页抓取
- **包**: `markfetch`
- **命令**: `npx -y markfetch`
- **能力**: 抓取任意 URL，返回干净的 Markdown 文本
- **⚠️ SSL 修复**: 因 Watt Toolkit MITM 代理，需环境变量 `NODE_EXTRA_CA_CERTS=D:/claude/watt_cert.pem`（PEM 格式，已在 `.claude.json` 配置）

### 📁 filesystem — 文件系统
- **包**: `@modelcontextprotocol/server-filesystem`
- **命令**: `npx -y @modelcontextprotocol/server-filesystem D:/claude`
- **能力**: 读写 `D:/claude` 目录下的文件（授权范围）
- **注意**: 反斜杠路径在注册时必须写成 `D:/claude`（正斜杠），否则连接失败

### 🧠 sequential-thinking — 深度推理
- **包**: `@modelcontextprotocol/server-sequential-thinking`
- **命令**: `npx -y @modelcontextprotocol/server-sequential-thinking`
- **能力**: 复杂问题的逐步推理链，可中途修正方向

### 💾 memory — 记忆图谱
- **包**: `@modelcontextprotocol/server-memory`
- **命令**: `npx -y @modelcontextprotocol/server-memory`
- **能力**: 基于知识图谱的持久记忆，跨会话保留

### 🌐 browser — 浏览器控制
- **包**: `chrome-devtools-mcp`
- **命令**: `npx -y chrome-devtools-mcp`
- **能力**: 控制 Chrome 浏览器——导航、点击、填表、截图、执行 JS、监控网络请求
- **注意**: 需 Chrome 开启远程调试端口

### 🖥️ desktop — 桌面自动化（自建）
- **脚本**: `D:/claude/mcp-desktop-server.py`
- **命令**: `python D:/claude/mcp-desktop-server.py`
- **基于**: PyAutoGUI + PyGetWindow
- **12 个工具**:
  | 工具 | 功能 |
  |------|------|
  | `desktop_screenshot` | 截屏（全屏/区域）→ base64 PNG |
  | `desktop_click` | 鼠标点击（左/右/中键/双击） |
  | `desktop_type` | 键盘输入文字 |
  | `desktop_press_key` | 按键/组合键（Ctrl+C, Alt+F4, Enter...） |
  | `desktop_move_mouse` | 移动鼠标 |
  | `desktop_scroll` | 滚轮滚动 |
  | `desktop_get_position` | 获取当前鼠标坐标 |
  | `desktop_get_screen_size` | 屏幕分辨率 |
  | `desktop_get_windows` | 列出所有窗口标题及位置 |
  | `desktop_focus_window` | 根据标题聚焦窗口 |
  | `desktop_get_active_window` | 当前活动窗口信息 |
  | `desktop_drag` | 鼠标拖拽 |

### 🚫 失败的尝试（记录备查）
| 包名 | 原因 |
|------|------|
| `@modelcontextprotocol/server-fetch` | npm 不存在此包 → 改用 `markfetch` |
| `@modelcontextprotocol/server-pdf` | HTTP 模式 + 端口 3001 硬编码 + 端口被占用 |
| `openowl` | macOS only（`os: darwin`），Windows 不兼容 |
| `autoui-mcp` | npm 包缺预编译的 `autoui-mcp.exe` 二进制文件 |

### 📝 MCP 管理速查
```bash
claude mcp list                              # 查看所有 MCP 服务器状态
claude mcp get <name>                        # 查看某个服务器详情
claude mcp add <name> -- npx -y <package>    # 添加 stdio MCP
claude mcp add <name> -- <command> [args]    # 添加自定义命令 MCP
claude mcp remove <name>                     # 移除 MCP 服务器
```

---

## 📎 其他备注

- **会话日志**: 见 `session-log.md`——Claude 会在每个任务节点自动追加对话摘要，无需用户手动提醒
- **自动记录规则**: 完成任务/重大决策/对话停顿时，主动写入 session-log.md，新记录追加在文件最上方（最新在前）

<!-- 在这里记录任何需要 Claude 记住的事项 -->
