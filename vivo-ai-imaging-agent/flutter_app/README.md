# 小V影像助手 - Flutter 客户端

vivo AI 影像智能体的移动端 Flutter 应用。

## 架构

```
lib/
├── main.dart              # 应用入口 + 主题配置
├── config/
│   └── api_config.dart    # API 配置 + 工具列表
├── models/
│   └── message.dart       # 消息/工具调用/结果模型
├── services/
│   └── agent_service.dart # Agent API 通信 + 离线回退
├── providers/
│   └── chat_provider.dart # 聊天状态管理 (Provider)
├── screens/
│   └── chat_screen.dart   # 主聊天界面
└── widgets/
    ├── chat_bubble.dart   # 聊天气泡
    ├── tool_card.dart     # 工具调用卡片
    └── capability_grid.dart # 能力清单网格
```

## 运行

```bash
# 1. 安装 Flutter SDK
# https://flutter.dev/docs/get-started/install

# 2. 安装依赖
cd flutter_app
flutter pub get

# 3. 启动后端 (另一个终端)
cd ..
python main.py --llm

# 4. 运行 Flutter 应用
flutter run
```

## 功能

- ✅ 文字/图片多模态输入
- ✅ 聊天式交互界面
- ✅ 工具调用实时展示
- ✅ 8/10 真实 AI 影像工具
- ✅ DeepSeek LLM 驱动
- ✅ 离线回退模式
- 🔜 vivo 蓝心端侧大模型 (复赛)
- 🔜 图片实时预览 (待接入后端图传)
