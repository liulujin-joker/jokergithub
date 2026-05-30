import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/chat_provider.dart';
import '../config/api_config.dart';
import '../services/agent_service.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/tool_card.dart';
import '../widgets/capability_grid.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _pickImage() async {
    final XFile? image = await _imagePicker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 90,
    );
    if (image != null) {
      context.read<ChatProvider>().setImage(image.path);
    }
  }

  Future<void> _takePhoto() async {
    final XFile? photo = await _imagePicker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 90,
    );
    if (photo != null) {
      context.read<ChatProvider>().setImage(photo.path);
    }
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    context.read<ChatProvider>().sendMessage(text);
    _textController.clear();
    _scrollToBottom();
  }

  void _quickAsk(String text) {
    context.read<ChatProvider>().sendMessage(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text('🤖 小V影像助手', style: TextStyle(fontSize: 18)),
            SizedBox(width: 10),
            _StatusBadge(),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: '服务器设置',
            onPressed: () => _showServerSettings(context),
          ),
          IconButton(
            icon: const Icon(Icons.grid_view_rounded),
            tooltip: '能力清单',
            onPressed: () => _showCapabilities(context),
          ),
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: '关于',
            onPressed: () => _showAbout(context),
          ),
        ],
      ),
      body: Column(
        children: [
          // 消息列表
          Expanded(
            child: Consumer<ChatProvider>(
              builder: (context, chat, _) {
                if (chat.messages.isEmpty) {
                  return _buildWelcomeScreen();
                }
                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  itemCount: chat.messages.length + (chat.isLoading ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == chat.messages.length) {
                      return const _LoadingIndicator();
                    }
                    final msg = chat.messages[index];
                    return Column(
                      crossAxisAlignment: msg.isUser
                          ? CrossAxisAlignment.end
                          : CrossAxisAlignment.start,
                      children: [
                        ChatBubble(message: msg),
                        // 展示工具调用
                        if (msg.hasToolCalls)
                          ...msg.toolCalls.map((tc) => ToolCard(toolCall: tc)),
                        const SizedBox(height: 4),
                      ],
                    );
                  },
                );
              },
            ),
          ),

          // 图片预览条
          Consumer<ChatProvider>(
            builder: (context, chat, _) {
              if (chat.selectedImagePath == null) return const SizedBox.shrink();
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(
                        File(chat.selectedImagePath!),
                        width: 60,
                        height: 60,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text('📎 已选择图片', style: TextStyle(fontSize: 13)),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => chat.clearImage(),
                    ),
                  ],
                ),
              );
            },
          ),

          // 快捷按钮
          Consumer<ChatProvider>(
            builder: (context, chat, _) {
              if (chat.messages.isNotEmpty) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _QuickChip('📸 变清晰', onTap: () => _quickAsk('帮我把照片变清晰')),
                    _QuickChip('🎨 动漫风格', onTap: () => _quickAsk('转换成动漫风格')),
                    _QuickChip('🧹 去路人', onTap: () => _quickAsk('消除照片里的路人')),
                    _QuickChip('✨ 美颜', onTap: () => _quickAsk('帮我美颜要自然一点')),
                    _QuickChip('📐 看构图', onTap: () => _quickAsk('帮我看看构图怎么样')),
                    _QuickChip('🔍 识场景', onTap: () => _quickAsk('看看这是什么场景')),
                    _QuickChip('🎬 调色', onTap: () => _quickAsk('调成电影感的色调')),
                    _QuickChip('✂️ 裁剪', onTap: () => _quickAsk('裁剪成16:9')),
                  ],
                ),
              );
            },
          ),

          // 输入区域
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildWelcomeScreen() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('🤖', style: TextStyle(fontSize: 56)),
            const SizedBox(height: 16),
            const Text(
              '小V影像助手',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              '从"用户操作工具"到"AI理解意图并主动服务"',
              style: TextStyle(fontSize: 14, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.green.withOpacity(0.3)),
                color: Colors.green.withOpacity(0.05),
              ),
              child: const Text(
                '🆕 v2.0 · LLM驱动 · 8/10工具真实实现',
                style: TextStyle(fontSize: 12, color: Colors.green),
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              '试试对我说：',
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            ...['"帮我把照片变清晰"', '"转换成动漫风格"', '"帮我看看构图"', '"消除照片里的路人"', '"帮我美颜一下"'].map(
              (text) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text(text, style: const TextStyle(color: Color(0xFFA5B4FC))),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.05))),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline, color: Colors.grey),
            onPressed: () => _showImageSourceDialog(context),
          ),
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration(
                hintText: '描述你想对照片做什么...',
                hintStyle: TextStyle(color: Colors.grey),
              ),
              style: const TextStyle(fontSize: 15),
              maxLines: null,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 8),
          Consumer<ChatProvider>(
            builder: (context, chat, _) {
              return IconButton(
                icon: Icon(
                  Icons.send_rounded,
                  color: chat.isLoading ? Colors.grey : const Color(0xFF6366F1),
                ),
                onPressed: chat.isLoading ? null : _sendMessage,
              );
            },
          ),
        ],
      ),
    );
  }

  void _showImageSourceDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A25),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library, color: Color(0xFF6366F1)),
              title: const Text('从相册选择'),
              onTap: () { Navigator.pop(ctx); _pickImage(); },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt, color: Color(0xFF6366F1)),
              title: const Text('拍照'),
              onTap: () { Navigator.pop(ctx); _takePhoto(); },
            ),
          ],
        ),
      ),
    );
  }

  void _showServerSettings(BuildContext context) {
    final config = ApiConfig();
    final controller = TextEditingController(text: config.baseUrl);
    final focusNode = FocusNode();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF1A1A25),
            title: const Row(
              children: [
                Icon(Icons.dns, color: Color(0xFF6366F1), size: 22),
                SizedBox(width: 8),
                Text('服务器设置', style: TextStyle(fontSize: 18)),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '输入后端服务器地址:',
                  style: TextStyle(fontSize: 13, color: Colors.grey),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: controller,
                  focusNode: focusNode,
                  style: const TextStyle(fontSize: 14, fontFamily: 'monospace'),
                  decoration: InputDecoration(
                    hintText: 'http://192.168.1.100:8000',
                    hintStyle: const TextStyle(fontSize: 13, color: Colors.grey),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.clear, size: 18),
                      onPressed: () {
                        controller.clear();
                        setDialogState(() {});
                      },
                    ),
                  ),
                  onChanged: (_) => setDialogState(() {}),
                ),
                const SizedBox(height: 12),
                // Preset buttons
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _PresetChip('模拟器', ApiConfig.emulatorUrl, controller, () => setDialogState(() {})),
                    _PresetChip('本机', ApiConfig.localhostUrl, controller, () => setDialogState(() {})),
                  ],
                ),
                const SizedBox(height: 12),
                // Test connection button
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.wifi_find, size: 18),
                    label: const Text('测试连接', style: TextStyle(fontSize: 13)),
                    onPressed: () async {
                      final testUrl = controller.text.trim();
                      if (testUrl.isEmpty) return;

                      // 保存原始地址，测试时临时切换
                      final originalUrl = config.baseUrl;
                      config.baseUrl = testUrl;

                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('⏳ 正在测试连接...'),
                          duration: Duration(seconds: 1),
                        ),
                      );

                      final service = AgentService();
                      final ok = await service.testConnection();

                      // 恢复原始地址 (用户需点"保存"才会正式修改)
                      config.baseUrl = originalUrl;

                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(ok
                                ? '✅ 连接成功！点击"保存"即可使用此地址'
                                : '❌ 连接失败，请检查地址和网络'),
                            duration: const Duration(seconds: 3),
                          ),
                        );
                      }
                    },
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  config.isCustomUrl
                      ? '✅ 当前使用自定义地址'
                      : '⚠️ 使用默认地址 (${ApiConfig.emulatorUrl})\n  真机请改为电脑 IP',
                  style: TextStyle(
                    fontSize: 11,
                    color: config.isCustomUrl ? Colors.green : Colors.orange,
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () async {
                  await config.reset();
                  if (context.mounted) Navigator.pop(ctx);
                },
                child: const Text('重置默认', style: TextStyle(color: Colors.grey)),
              ),
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('取消', style: TextStyle(color: Colors.grey)),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6366F1),
                ),
                onPressed: () {
                  final url = controller.text.trim();
                  if (url.isNotEmpty) {
                    config.baseUrl = url;
                  }
                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('✅ 服务器地址已更新: ${config.baseUrl}'),
                      duration: const Duration(seconds: 2),
                    ),
                  );
                },
                child: const Text('保存'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showCapabilities(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A25),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => const CapabilityGrid(),
    );
  }

  void _showAbout(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A25),
        title: const Text('关于 小V影像助手'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🏆 中国高校计算机大赛 · AIGC创新赛'),
            SizedBox(height: 8),
            Text('📱 赛道: 手机AI助手，未来AI影像体验设计'),
            SizedBox(height: 8),
            Text('📦 版本: v2.0'),
            Text('🧠 驱动: DeepSeek LLM + Function Calling'),
            Text('🛠️ 工具: 8/10 真实实现'),
            SizedBox(height: 8),
            Text('💡 后端: python main.py --llm'),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('确定')),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.green.withOpacity(0.1),
        border: Border.all(color: Colors.green.withOpacity(0.3)),
      ),
      child: const Text('v2.0 LLM', style: TextStyle(fontSize: 10, color: Colors.green)),
    );
  }
}

class _LoadingIndicator extends StatelessWidget {
  const _LoadingIndicator();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Text('🤖', style: TextStyle(fontSize: 20)),
          SizedBox(width: 12),
          Text('小V思考中...', style: TextStyle(color: Colors.grey, fontSize: 14)),
        ],
      ),
    );
  }
}

class _QuickChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _QuickChip(this.label, {required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 12)),
      onPressed: onTap,
      backgroundColor: const Color(0xFF1E1E30),
      side: const BorderSide(color: Color(0xFF2A2A40)),
      padding: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class _PresetChip extends StatelessWidget {
  final String label;
  final String url;
  final TextEditingController controller;
  final VoidCallback onChanged;

  const _PresetChip(this.label, this.url, this.controller, this.onChanged);

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 11)),
      onPressed: () {
        controller.text = url;
        onChanged();
      },
      backgroundColor: controller.text == url
          ? const Color(0xFF6366F1).withOpacity(0.15)
          : const Color(0xFF1E1E30),
      side: BorderSide(
        color: controller.text == url
            ? const Color(0xFF6366F1)
            : const Color(0xFF2A2A40),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 8),
    );
  }
}
