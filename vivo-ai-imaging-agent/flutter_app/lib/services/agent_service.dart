import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/message.dart';

/// Agent API 服务
class AgentService {
  final http.Client _client = http.Client();

  /// 测试服务器连接
  Future<bool> testConnection() async {
    try {
      final response = await _client.get(
        Uri.parse('${ApiConfig().baseUrl}${ApiConfig.healthEndpoint}'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// 发送文字消息
  Future<ChatMessage> sendMessage(String content) async {
    try {
      final response = await _client.post(
        Uri.parse('${ApiConfig().baseUrl}${ApiConfig.chatEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'content': content}),
      ).timeout(ApiConfig.requestTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return _parseResponse(data);
      }
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        role: MessageRole.assistant,
        content: '服务暂时不可用 (${response.statusCode})',
      );
    } on SocketException {
      return _connectionFailedMessage();
    } catch (e) {
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection refused') ||
          e.toString().contains('Connection timed out')) {
        return _connectionFailedMessage();
      }
      return _localFallback(content);
    }
  }

  ChatMessage _connectionFailedMessage() {
    final url = ApiConfig().baseUrl;
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: MessageRole.assistant,
      content: '⚠️ 无法连接到服务器\n\n'
          '当前地址: $url\n\n'
          '📱 真机使用请确认:\n'
          '1️⃣ 手机和电脑在同一 WiFi\n'
          '2️⃣ 电脑防火墙允许 8000 端口\n'
          '3️⃣ 服务器地址已设为电脑 IP\n'
          '   例: http://192.168.x.x:8000\n\n'
          '💡 点击右上角 ⚙️ 修改服务器地址\n'
          '💡 也可以在离线模式下体验 Demo',
    );
  }

  /// 发送带图片的消息
  Future<ChatMessage> sendMessageWithImage(
    String content,
    File imageFile,
  ) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig().baseUrl}${ApiConfig.chatWithImageEndpoint}'),
      );
      request.fields['content'] = content;
      request.files.add(
        await http.MultipartFile.fromPath('image', imageFile.path),
      );

      final response = await request.send().timeout(ApiConfig.imageUploadTimeout);
      final body = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final data = jsonDecode(body);
        return _parseResponse(data);
      }
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        role: MessageRole.assistant,
        content: '图片处理失败 (${response.statusCode})',
      );
    } on SocketException {
      return _connectionFailedMessage();
    } catch (e) {
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection refused')) {
        return _connectionFailedMessage();
      }
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        role: MessageRole.assistant,
        content: '⚠️ 网络连接失败\n\n💡 点击右上角 ⚙️ 设置服务器地址，或体验离线 Demo 模式',
      );
    }
  }

  /// 解析后端响应
  ChatMessage _parseResponse(Map<String, dynamic> data) {
    final toolCalls = (data['tool_calls'] as List?)
        ?.map((t) => ToolCall.fromJson(t))
        .toList() ?? [];

    return ChatMessage(
      id: data['id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
      role: MessageRole.assistant,
      content: data['content'] ?? '',
      toolCalls: toolCalls,
    );
  }

  /// 离线 Demo 回复 — 展示智能体完整交互流程
  ChatMessage _localFallback(String query) {
    final q = query.toLowerCase();
    String reply;
    List<ToolCall> toolCalls = [];

    if (q.contains('增强') || q.contains('清晰') || q.contains('模糊')) {
      toolCalls = [ToolCall(id: 'photo_enhance', toolName: 'photo_enhance', status: 'demo')];
      reply = '📸 **[Demo] 画质增强**\n\n'
          '✅ 已分析图像特征:\n'
          '• 清晰度评分: 62/100 → 提升至 88/100\n'
          '• 锐度: +35% | 对比度: +20% | 降噪: 已应用\n\n'
          '🎯 这是离线 Demo 模式。连接后端后可真正处理你的照片！';
    } else if (q.contains('风格') || q.contains('动漫') || q.contains('油画') || q.contains('滤镜')) {
      toolCalls = [ToolCall(id: 'style_transfer', toolName: 'style_transfer', status: 'demo')];
      reply = '🎨 **[Demo] 风格迁移**\n\n'
          '✅ 可用风格 (共7种):\n'
          '🎭 动漫 | 🖼️ 油画 | 🎬 老电影 | ✏️ 素描\n'
          '🌈 复古 | 🔮 赛博朋克 | 📷 日系清新\n\n'
          '💡 连接后端后可一键转换！';
    } else if (q.contains('构图')) {
      toolCalls = [ToolCall(id: 'composition_guide', toolName: 'composition_guide', status: 'demo')];
      reply = '📐 **[Demo] 构图分析**\n\n'
          '✅ 三分法评分: 78/100\n'
          '• 水平线: 居中 (建议偏移至 1/3 处)\n'
          '• 主体位置: 偏左 (符合三分法)\n'
          '• 视觉引导线: 检测到2条 → 指向主体\n\n'
          '📊 综合评分: ⭐⭐⭐⭐ (良)';
    } else if (q.contains('消除') || q.contains('路人') || q.contains('去除')) {
      toolCalls = [ToolCall(id: 'object_remove', toolName: 'object_remove', status: 'demo')];
      reply = '🧹 **[Demo] 物体消除**\n\n'
          '⚠️ 此功能需要云端 AI 模型 (SAM+LaMa)\n'
          '离线模式无法真正执行。\n\n'
          '✅ 工作流程:\n'
          '1. SAM 分割目标物体\n'
          '2. LaMa 填充背景\n'
          '3. 边缘融合 → 自然无痕\n\n'
          '💡 完整功能需连接后端。';
    } else if (q.contains('美颜') || q.contains('美白') || q.contains('磨皮')) {
      toolCalls = [ToolCall(id: 'portrait_beautify', toolName: 'portrait_beautify', status: 'demo')];
      reply = '✨ **[Demo] 人像美化**\n\n'
          '✅ 处理流程:\n'
          '• 肤色检测 → 亚洲肤色范围\n'
          '• 高斯柔焦 → 半径3px (自然磨皮)\n'
          '• 美白增强 → +12% 亮度\n'
          '• 饱和度微调 → 唇色保真\n\n'
          '👤 参数: 自然模式 (可调: 自然/精致/网红)';
    } else if (q.contains('场景') || q.contains('识别')) {
      toolCalls = [ToolCall(id: 'scene_recognize', toolName: 'scene_recognize', status: 'demo')];
      reply = '🔍 **[Demo] 场景识别**\n\n'
          '✅ 分析结果 (模拟CLIP):\n'
          '🏙️ 城市街景 — 置信度 92%\n'
          '🌆 黄昏时分 — 置信度 78%\n'
          '👤 含人物(2人) — 置信度 85%\n\n'
          '📊 建议拍摄模式: 人像/街拍\n'
          '💡 连接后端可使用 CLIP AI 模型真实识别！';
    } else if (q.contains('调色') || q.contains('色彩') || q.contains('电影') || q.contains('色调')) {
      toolCalls = [ToolCall(id: 'color_grading', toolName: 'color_grading', status: 'demo')];
      reply = '🎬 **[Demo] 色彩调校**\n\n'
          '✅ 9种预设风格可选:\n'
          '🎬 电影感 | 🌅 日系清新 | 🖤 黑白纪实\n'
          '🔥 暖色胶片 | ❄️ 冷色蓝调 | 📸 复古褪色\n'
          '🌈 鲜艳饱和 | 🌙 暗调氛围 | 💚 青橙色调\n\n'
          '💡 连接后端可实时预览效果！';
    } else if (q.contains('裁剪') || q.contains('crop') || q.contains('比例')) {
      toolCalls = [ToolCall(id: 'smart_crop', toolName: 'smart_crop', status: 'demo')];
      reply = '✂️ **[Demo] 智能裁剪**\n\n'
          '✅ 显著性检测结果:\n'
          '• 主体区域: (120, 80) ~ (680, 540)\n'
          '• 推荐比例: 4:3 (评分 92)\n'
          '• 备选比例: 16:9 (评分 78), 1:1 (评分 71)\n\n'
          '💡 连接后端可自动裁剪输出！';
    } else if (q.contains('扩图') || q.contains('扩展') || q.contains('扩展')) {
      toolCalls = [ToolCall(id: 'ai_expand', toolName: 'ai_expand', status: 'demo')];
      reply = '🔲 **[Demo] AI扩图**\n\n'
          '⚠️ 此功能需要 Stable Diffusion Outpainting\n'
          '离线模式无法真正执行。\n\n'
          '✅ 工作原理: 根据画面内容 → AI生成周边区域\n'
          '💡 完整功能需连接后端。';
    } else if (q.contains('动态') || q.contains('gif') || q.contains('动画')) {
      toolCalls = [ToolCall(id: 'motion_photo', toolName: 'motion_photo', status: 'demo')];
      reply = '🎬 **[Demo] 动态照片**\n\n'
          '✅ 效果说明:\n'
          '• 视差3D效果 — 前景/背景分层移动\n'
          '• 波浪扭曲 — 水面/烟雾动态\n'
          '• 输出格式 — GIF 动画\n\n'
          '💡 连接后端可生成真正的动态照片 GIF！';
    } else if (q.contains('你好') || q.contains('hi') || q.contains('hello') || q.contains('帮助')) {
      reply = '🤖 你好！我是**小V影像助手 v2.0** 👋\n\n'
          '🏆 中国高校计算机大赛 · AIGC创新赛作品\n\n'
          '📱 **10大AI影像能力**:\n'
          '📸 画质增强 | 🎨 风格迁移 | 📐 构图指导\n'
          '✨ 人像美化 | 🔍 场景识别 | 🎬 色彩调校\n'
          '✂️ 智能裁剪 | 🎬 动态照片 | 🧹 物体消除 | 🔲 AI扩图\n\n'
          '⚡ 当前为 **离线 Demo 模式**，展示完整交互流程。\n'
          '连接后端后可真正处理你的照片！\n\n'
          '💡 试试: "帮我把照片变清晰" "转换成动漫风格"';
    } else {
      reply = '🤖 收到！我是小V影像助手 🎯\n\n'
          '当前处于 **离线 Demo 模式**，展示智能体的交互流程。\n\n'
          '💬 你可以试试:\n'
          '• "帮我把照片变清晰" → 📸 画质增强\n'
          '• "转换成动漫风格" → 🎨 风格迁移\n'
          '• "帮我看看构图怎么样" → 📐 构图指导\n'
          '• "消除照片里的路人" → 🧹 物体消除\n'
          '• "帮我美颜一下" → ✨ 人像美化\n'
          '• "看看这是什么场景" → 🔍 场景识别\n\n'
          '🔌 想使用真实 AI 功能？\n'
          '1️⃣ 电脑端启动后端服务\n'
          '2️⃣ 点击右上角 ⚙️ 设置服务器地址';
    }

    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: MessageRole.assistant,
      content: reply,
      toolCalls: toolCalls,
    );
  }

  void dispose() {
    _client.close();
  }
}
