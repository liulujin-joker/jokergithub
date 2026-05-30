import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/message.dart';

/// Agent API 服务
/// 与小V影像助手后端通信（Python FastAPI 或 vivo 云测平台）
class AgentService {
  final http.Client _client = http.Client();

  /// 发送文字消息
  Future<ChatMessage> sendMessage(String content) async {
    try {
      final response = await _client.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.chatEndpoint}'),
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
        content: '抱歉，服务暂时不可用 (${response.statusCode})',
      );
    } catch (e) {
      // 离线回退：返回本地模拟回复
      return _localFallback(content);
    }
  }

  /// 发送带图片的消息
  Future<ChatMessage> sendMessageWithImage(
    String content,
    File imageFile,
  ) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.chatWithImageEndpoint}'),
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
    } catch (e) {
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        role: MessageRole.assistant,
        content: '网络连接失败，请检查后端服务是否启动。\n\n💡 本地运行: python main.py --llm',
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

  /// 本地回退 (无后端时的模拟回复)
  ChatMessage _localFallback(String query) {
    String reply;
    if (query.contains('场景') || query.contains('什么模式')) {
      reply = '🔍 需要连接后端服务进行场景识别。\n\n💡 请启动后端: python main.py --llm';
    } else if (query.contains('构图')) {
      reply = '📐 构图分析需要后端支持。\n\n💡 请启动后端: python main.py --llm';
    } else if (query.contains('增强') || query.contains('清晰')) {
      reply = '📸 画质增强需要后端支持。\n\n💡 请启动后端: python main.py --llm';
    } else {
      reply = '你好！我是小V影像助手 👋\n\n'
          '我可以通过 AI 帮你处理照片、提供拍摄建议。\n\n'
          '当前为离线模式，连接后端后可获得完整 AI 能力。\n\n'
          '💡 启动后端: python main.py --llm';
    }
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: MessageRole.assistant,
      content: reply,
    );
  }

  void dispose() {
    _client.close();
  }
}
