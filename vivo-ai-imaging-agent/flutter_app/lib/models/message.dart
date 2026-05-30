/// 消息模型
enum MessageRole { user, assistant, system, tool }

class ChatMessage {
  final String id;
  final MessageRole role;
  final String content;
  final String? imageBase64;
  final String? imagePath;
  final List<ToolCall> toolCalls;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    this.imageBase64,
    this.imagePath,
    this.toolCalls = const [],
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  bool get isUser => role == MessageRole.user;
  bool get isAssistant => role == MessageRole.assistant;
  bool get hasImage => imageBase64 != null || imagePath != null;
  bool get hasToolCalls => toolCalls.isNotEmpty;

  Map<String, dynamic> toJson() => {
    'id': id,
    'role': role.name,
    'content': content,
    'image_base64': imageBase64,
    'tool_calls': toolCalls.map((t) => t.toJson()).toList(),
    'timestamp': timestamp.toIso8601String(),
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] ?? '',
      role: MessageRole.values.firstWhere((r) => r.name == json['role']),
      content: json['content'] ?? '',
      imageBase64: json['image_base64'],
      toolCalls: (json['tool_calls'] as List?)
          ?.map((t) => ToolCall.fromJson(t))
          .toList() ?? [],
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'])
          : null,
    );
  }
}

class ToolCall {
  final String id;
  final String toolName;
  final Map<String, dynamic> parameters;
  final String status; // pending / running / done / error
  final ToolResult? result;

  ToolCall({
    required this.id,
    required this.toolName,
    this.parameters = const {},
    this.status = 'pending',
    this.result,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'tool_name': toolName,
    'parameters': parameters,
    'status': status,
  };

  factory ToolCall.fromJson(Map<String, dynamic> json) {
    return ToolCall(
      id: json['id'] ?? '',
      toolName: json['tool_name'] ?? '',
      parameters: Map<String, dynamic>.from(json['parameters'] ?? {}),
      status: json['status'] ?? 'pending',
    );
  }
}

class ToolResult {
  final String callId;
  final bool success;
  final String message;
  final String? previewUrl;

  ToolResult({
    required this.callId,
    required this.success,
    required this.message,
    this.previewUrl,
  });

  factory ToolResult.fromJson(Map<String, dynamic> json) {
    return ToolResult(
      callId: json['call_id'] ?? '',
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      previewUrl: json['preview_url'],
    );
  }
}
