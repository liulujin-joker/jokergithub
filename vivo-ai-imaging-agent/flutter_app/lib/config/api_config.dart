import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// API 配置
/// 小V影像助手后端接口配置
class ApiConfig extends ChangeNotifier {
  static final ApiConfig _instance = ApiConfig._();
  factory ApiConfig() => _instance;
  ApiConfig._();

  // ---- SharedPreferences key ----
  static const String _keyServerUrl = 'server_url';

  // ---- 预设地址 ----
  static const String emulatorUrl = 'http://10.0.2.2:8000'; // Android 模拟器专用
  static const String localhostUrl = 'http://localhost:8000'; // iOS 模拟器 / Web
  static const String vivoCloudUrl = 'https://api.vivo.com.cn/imaging-agent/v1';

  // ---- 当前服务器地址 ----
  String? _customUrl; // null = 使用默认
  bool _initialized = false;

  /// 当前 baseUrl
  String get baseUrl {
    if (_customUrl != null && _customUrl!.isNotEmpty) return _customUrl!;
    // 真机默认用 emulatorUrl (会失败, 提示用户配置)
    // iOS 模拟器可用 localhost
    return emulatorUrl;
  }

  set baseUrl(String url) {
    _customUrl = url;
    notifyListeners();
    _save();
  }

  bool get isCustomUrl => _customUrl != null && _customUrl!.isNotEmpty;

  /// 从 SharedPreferences 加载已保存的地址
  Future<void> init() async {
    if (_initialized) return;
    final prefs = await SharedPreferences.getInstance();
    _customUrl = prefs.getString(_keyServerUrl);
    _initialized = true;
    notifyListeners();
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    if (_customUrl != null && _customUrl!.isNotEmpty) {
      await prefs.setString(_keyServerUrl, _customUrl!);
    } else {
      await prefs.remove(_keyServerUrl);
    }
  }

  /// 重置为默认地址
  Future<void> reset() async {
    _customUrl = null;
    notifyListeners();
    await _save();
  }

  // ---- API 端点 ----
  static const String chatEndpoint = '/chat';
  static const String chatWithImageEndpoint = '/chat/image';
  static const String healthEndpoint = '/health';
  static const String capabilitiesEndpoint = '/capabilities';

  // ---- 工具列表 (端侧可用) ----
  static const List<Map<String, String>> availableTools = [
    {'name': 'photo_enhance', 'emoji': '📸', 'label': '画质增强', 'status': 'real'},
    {'name': 'style_transfer', 'emoji': '🎨', 'label': '风格迁移', 'status': 'real'},
    {'name': 'composition_guide', 'emoji': '📐', 'label': '构图指导', 'status': 'real'},
    {'name': 'object_remove', 'emoji': '🧹', 'label': '物体消除', 'status': 'demo'},
    {'name': 'portrait_beautify', 'emoji': '✨', 'label': '人像美化', 'status': 'real'},
    {'name': 'scene_recognize', 'emoji': '🔍', 'label': '场景识别', 'status': 'real'},
    {'name': 'color_grading', 'emoji': '🎬', 'label': '色彩调校', 'status': 'real'},
    {'name': 'smart_crop', 'emoji': '✂️', 'label': '智能裁剪', 'status': 'real'},
    {'name': 'ai_expand', 'emoji': '🔲', 'label': 'AI扩图', 'status': 'demo'},
    {'name': 'motion_photo', 'emoji': '🎬', 'label': '动态照片', 'status': 'real'},
  ];

  // ---- LLM 配置 ----
  static const String llmProvider = 'deepseek';
  static const String llmModel = 'deepseek-chat';

  // ---- 超时 ----
  static const Duration requestTimeout = Duration(seconds: 30);
  static const Duration imageUploadTimeout = Duration(seconds: 60);
}
