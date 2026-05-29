"""
意图解析器 - 智能体的大脑，理解用户想对影像做什么

设计理念：
- 从自然语言中精准提取影像操作意图
- 支持多意图识别（一句话可能包含多个操作需求）
- 置信度评分与歧义消解
- 结合用户偏好做个性化意图推断
"""

import re
from typing import List, Optional, Dict, Any
from ..models.schemas import ImageIntent, IntentType


class IntentParser:
    """意图解析器"""

    # 意图关键词映射
    INTENT_PATTERNS = {
        IntentType.ENHANCE: [
            "增强", "优化", "提升画质", "更清晰", "清晰度", "降噪",
            "超分", "高清", "HDR", "去雾", "锐化", "修复", "还原"
        ],
        IntentType.STYLE: [
            "风格", "转换", "变成", "改成", "油画", "水彩", "动漫",
            "卡通", "赛博", "胶片", "复古", "黑白", "水墨", "素描",
            "像素", "波普", "粘土", "手绘"
        ],
        IntentType.COMPOSE: [
            "构图", "取景", "怎么拍", "角度", "位置", "框架",
            "前景", "背景", "三分", "引导线", "对称", "黄金",
            "拍摄建议", "怎么构图", "拍得", "画面"
        ],
        IntentType.REMOVE: [
            "消除", "去掉", "删除", "移除", "抹掉", "擦除", "抠掉",
            "消掉", "弄掉", "路人", "杂物", "水印", "马赛克", "打码",
            "不要", "碍眼"
        ],
        IntentType.BEAUTIFY: [
            "美颜", "美妆", "瘦脸", "大眼", "美白", "磨皮",
            "祛痘", "修容", "化妆", "美容", "P图", "修图",
            "美化", "好看一点", "漂亮", "美图", "P一下"
        ],
        IntentType.CROP: [
            "裁剪", "截图", "切图", "裁切", "比例", "尺寸",
            "竖屏", "横屏", "正方形"
        ],
        IntentType.COLOR: [
            "调色", "滤镜", "色温", "色调", "饱和度", "白平衡",
            "冷暖", "鲜艳", "淡雅", "电影色", "季节", "胶片感"
        ],
        IntentType.EXPAND: [
            "扩图", "扩展", "补全", "延伸", "拉远", "外扩",
            "画布", "填充边缘"
        ],
        IntentType.MOTION: [
            "动态", "动起来", "动画", "视频", "视差", "循环",
            "流动", "飘动", "cinemagraph"
        ],
        IntentType.SCENE: [
            "这是什么场景", "这是啥场景", "识别", "检测", "分析", "判断",
            "什么模式", "怎么设置参数", "啥场景", "什么场景"
        ],
    }

    # 每个意图类型的权重（基础置信度加成）
    INTENT_WEIGHTS = {
        IntentType.ENHANCE: 1.0,
        IntentType.STYLE: 1.1,
        IntentType.COMPOSE: 0.85,
        IntentType.REMOVE: 1.1,
        IntentType.BEAUTIFY: 1.0,
        IntentType.SCENE: 1.0,
        IntentType.CROP: 0.9,
        IntentType.COLOR: 1.0,
        IntentType.EXPAND: 1.0,
        IntentType.MOTION: 1.0,
        IntentType.GENERAL: 0.3,
    }

    # 高优先级关键词：当这些词出现时，对应的意图获得额外加权
    HIGH_PRIORITY_KEYWORDS = {
        "滤镜": IntentType.COLOR,
        "调色": IntentType.COLOR,
        "色调": IntentType.COLOR,
        "变成": IntentType.STYLE,
        "转换": IntentType.STYLE,
        "风格": IntentType.STYLE,
        "消除": IntentType.REMOVE,
        "去掉": IntentType.REMOVE,
        "美颜": IntentType.BEAUTIFY,
        "瘦脸": IntentType.BEAUTIFY,
        "构图": IntentType.COMPOSE,
        "增强": IntentType.ENHANCE,
        "高清": IntentType.ENHANCE,
        "扩图": IntentType.EXPAND,
        "裁剪": IntentType.CROP,
        "动起来": IntentType.MOTION,
    }

    def parse(self, query: str, has_image: bool = False) -> List[ImageIntent]:
        """
        解析用户意图
        返回按置信度排序的意图列表
        """
        intents = []

        for intent_type, keywords in self.INTENT_PATTERNS.items():
            matched = []
            for kw in keywords:
                if kw in query:
                    matched.append(kw)

            if matched:
                # 改进的置信度计算
                match_ratio = len(matched) / max(1, len(keywords))
                base_confidence = 0.4 + match_ratio * 0.5
                confidence = base_confidence * self.INTENT_WEIGHTS.get(intent_type, 1.0)

                # 高优先级关键词加成
                for hk, hk_intent in self.HIGH_PRIORITY_KEYWORDS.items():
                    if hk in query and hk_intent == intent_type:
                        confidence = min(0.95, confidence + 0.2)
                        break

                confidence = min(0.95, confidence)

                # 如果有图片，图像相关意图置信度更高
                if has_image and intent_type not in [IntentType.GENERAL, IntentType.COMPOSE]:
                    confidence = min(0.98, confidence + 0.15)

                # 提取参数
                parameters = self._extract_parameters(query, intent_type)

                intents.append(ImageIntent(
                    intent_type=intent_type,
                    confidence=confidence,
                    target_description=query,
                    parameters=parameters,
                    raw_query=query
                ))

        # 按置信度排序
        intents.sort(key=lambda x: x.confidence, reverse=True)

        # 如果没有识别到具体意图，返回通用意图
        if not intents:
            intents.append(ImageIntent(
                intent_type=IntentType.GENERAL,
                confidence=0.5,
                target_description=query,
                raw_query=query
            ))

        return intents

    def _extract_parameters(self, query: str, intent_type: IntentType) -> Dict[str, Any]:
        """从文本中提取操作参数"""
        params = {}

        # 提取风格参数
        style_map = {
            "油画": "oil_painting", "水彩": "watercolor", "动漫": "anime",
            "卡通": "anime", "赛博": "cyberpunk", "赛博朋克": "cyberpunk",
            "胶片": "film_retro", "复古": "film_retro", "黑白": "minimal_bw",
            "水墨": "chinese_ink", "素描": "sketch", "像素": "pixel_art",
            "粘土": "clay_style", "波普": "pop_art"
        }
        for cn, en in style_map.items():
            if cn in query:
                params["style"] = en
                break

        # 提取增强强度
        if "强" in query or "很大" in query or "超级" in query:
            params["enhance_level"] = "strong"
        elif "轻" in query or "微" in query or "一点" in query:
            params["enhance_level"] = "light"
        else:
            params["enhance_level"] = "medium"

        # 提取美颜程度
        if "自然" in query:
            params["beauty_level"] = "natural"
        elif "精致" in query or "重度" in query:
            params["beauty_level"] = "glamour"

        # 提取比例
        ratio_patterns = {
            "16:9": r"(?:16[:：]9|十六比九|横屏|电影)",
            "1:1": r"(?:1[:：]1|一比一|方形|正方形)",
            "4:3": r"(?:4[:：]3|四比三)",
            "9:16": r"(?:9[:：]16|九比十六|竖屏)",
            "3:4": r"(?:3[:：]4|三比四)"
        }
        for ratio, pattern in ratio_patterns.items():
            if re.search(pattern, query):
                params["target_ratio"] = ratio
                break

        # 提取运动类型
        if "视差" in query or "3D" in query or "3d" in query:
            params["motion_type"] = "parallax_3d"
        elif "局部" in query or "循环" in query:
            params["motion_type"] = "cinemagraph"

        return params

    def get_top_intent(self, query: str, has_image: bool = False) -> ImageIntent:
        """获取最可能的意图"""
        intents = self.parse(query, has_image)
        return intents[0] if intents else ImageIntent(
            intent_type=IntentType.GENERAL,
            confidence=0.0,
            target_description=query,
            raw_query=query
        )
