/// API 配置
/// 小V影像助手后端接口配置
class ApiConfig {
  // ---- 后端地址 ----
  // 本地开发
  static const String localBaseUrl = 'http://10.0.2.2:8000'; // Android 模拟器 → 宿主机
  static const String localBaseUrlIOS = 'http://localhost:8000';

  // 生产环境 (vivo 云测平台 - 复赛开放)
  static const String vivoCloudBaseUrl = 'https://api.vivo.com.cn/imaging-agent/v1';

  // ---- 当前环境 ----
  static String get baseUrl => localBaseUrl;

  // ---- API 端点 ----
  static const String chatEndpoint = '/chat';
  static const String chatWithImageEndpoint = '/chat/image';
  static const String toolStatusEndpoint = '/tools/status';
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
  static const String llmProvider = 'deepseek'; // deepseek / vivo
  static const String llmModel = 'deepseek-chat';

  // ---- 超时 ----
  static const Duration requestTimeout = Duration(seconds: 30);
  static const Duration imageUploadTimeout = Duration(seconds: 60);
}
