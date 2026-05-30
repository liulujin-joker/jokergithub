import 'package:flutter/material.dart';
import '../models/message.dart';

class ToolCard extends StatelessWidget {
  final ToolCall toolCall;

  const ToolCard({super.key, required this.toolCall});

  @override
  Widget build(BuildContext context) {
    final emojiMap = {
      'photo_enhance': '📸', 'style_transfer': '🎨',
      'composition_guide': '📐', 'object_remove': '🧹',
      'portrait_beautify': '✨', 'scene_recognize': '🔍',
      'color_grading': '🎬', 'smart_crop': '✂️',
      'ai_expand': '🔲', 'motion_photo': '🎬',
    };

    final labelMap = {
      'photo_enhance': '画质增强', 'style_transfer': '风格迁移',
      'composition_guide': '构图分析', 'object_remove': '物体消除',
      'portrait_beautify': '人像美化', 'scene_recognize': '场景识别',
      'color_grading': '色彩调校', 'smart_crop': '智能裁剪',
      'ai_expand': 'AI扩图', 'motion_photo': '动态照片',
    };

    final isDone = toolCall.status == 'done';
    final isRunning = toolCall.status == 'running';
    final isError = toolCall.status == 'error';

    return Padding(
      padding: const EdgeInsets.only(left: 36, top: 2, bottom: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A25),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isDone
                ? Colors.green.withOpacity(0.3)
                : isError
                    ? Colors.red.withOpacity(0.3)
                    : const Color(0xFF6366F1).withOpacity(0.3),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emojiMap[toolCall.toolName] ?? '🔧', style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 6),
            Text(
              labelMap[toolCall.toolName] ?? toolCall.toolName,
              style: const TextStyle(fontSize: 12, color: Color(0xFFA5B4FC)),
            ),
            const SizedBox(width: 6),
            Icon(
              isDone ? Icons.check_circle : isError ? Icons.error : Icons.hourglass_top,
              size: 14,
              color: isDone ? Colors.green : isError ? Colors.red : Colors.orange,
            ),
          ],
        ),
      ),
    );
  }
}
