import 'dart:io';
import 'package:flutter/material.dart';
import '../models/message.dart';
import '../services/agent_service.dart';

/// 聊天状态管理
class ChatProvider extends ChangeNotifier {
  final AgentService _agentService = AgentService();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String? _selectedImagePath;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  String? get selectedImagePath => _selectedImagePath;

  /// 发送文字消息
  Future<void> sendMessage(String content) async {
    if (content.trim().isEmpty) return;

    // 添加用户消息
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: MessageRole.user,
      content: content,
      imagePath: _selectedImagePath,
    );
    _messages.add(userMsg);
    _isLoading = true;
    notifyListeners();

    // 调用 Agent
    ChatMessage reply;
    if (_selectedImagePath != null) {
      reply = await _agentService.sendMessageWithImage(
        content,
        File(_selectedImagePath!),
      );
      _selectedImagePath = null;
    } else {
      reply = await _agentService.sendMessage(content);
    }

    _messages.add(reply);
    _isLoading = false;
    notifyListeners();
  }

  /// 选择图片
  void setImage(String path) {
    _selectedImagePath = path;
    notifyListeners();
  }

  /// 清除图片选择
  void clearImage() {
    _selectedImagePath = null;
    notifyListeners();
  }

  /// 清空对话
  void clearChat() {
    _messages.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _agentService.dispose();
    super.dispose();
  }
}
