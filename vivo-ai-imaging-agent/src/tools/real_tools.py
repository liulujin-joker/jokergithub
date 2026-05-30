"""
真实 AI 影像工具实现

与 imaging_tools.py 的假工具不同，这里的工具会调用真实的 AI 模型/API。
实现策略：
- 有免费 API 的 → 直接接入（HuggingFace Inference API）
- 需要本地模型 → 提供基于 Pillow/numpy 的基础实现
- 需要 GPU 的 → 提供 API 接入点，标注 "需云端支持"

每个工具遵循同样的接口：execute(**kwargs) -> Dict[str, Any]

优先级 (按可行性排列):
1. scene_recognize   - HuggingFace CLIP (免费API) + 传统分析回退
2. composition_guide - PIL + numpy (纯本地计算)
3. photo_enhance     - PIL ImageEnhance (纯本地)
4. color_grading     - PIL ImageEnhance (纯本地)
5. smart_crop        - PIL (纯本地)
6. style_transfer    - 需云端 API
7. object_remove     - 需云端 API
8. ai_expand         - 需云端 API
9. motion_photo      - 需云端 API
10. portrait_beautify - 需云端 API
"""

import os
import io
import base64
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 工具函数
# ============================================================

def _b64_to_pil(b64_str: str) -> Optional[Image.Image]:
    """base64 to PIL Image"""
    try:
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        print(f"[real_tools] base64 decode failed: {e}")
        return None


def _pil_to_b64(img: Image.Image, fmt: str = "JPEG", quality: int = 90) -> str:
    """PIL Image to base64 string"""
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ============================================================
# 场景标签与配置
# ============================================================

SCENE_LABELS_CN = [
    "人像", "风景", "城市夜景", "日落", "海滩", "山脉", "森林",
    "美食", "建筑", "街道", "花卉", "动物", "雪景", "室内",
    "舞台", "运动场", "水面", "天空", "微距", "文档",
    "烟花", "星轨", "极光", "沙漠", "草原", "瀑布",
    "咖啡馆", "图书馆", "市场", "游乐场", "车流", "夜景人像",
]

SCENE_CONFIGS = {
    "人像": {"mode": "人像模式", "filters": ["自然", "清新", "复古"], "iso": "100-400"},
    "风景": {"mode": "风景模式", "filters": ["鲜艳", "HDR风景", "自然"], "iso": "100-200"},
    "城市夜景": {"mode": "夜景模式", "filters": ["赛博朋克", "夜景增强", "冷暖对比"], "iso": "400-800"},
    "日落": {"mode": "日落模式", "filters": ["暖阳", "逆光HDR", "黄昏"], "iso": "100-400"},
    "海滩": {"mode": "海滩模式", "filters": ["清凉", "高调", "夏日"], "iso": "100-200"},
    "山脉": {"mode": "风景模式", "filters": ["壮丽", "HDR风景", "黑白"], "iso": "100-200"},
    "森林": {"mode": "风景模式", "filters": ["翠绿", "森系", "自然"], "iso": "200-400"},
    "美食": {"mode": "美食模式", "filters": ["暖食", "鲜艳", "柔光"], "iso": "200-400"},
    "建筑": {"mode": "建筑模式", "filters": ["几何", "黑白", "HDR"], "iso": "100-200"},
    "街道": {"mode": "街拍模式", "filters": ["胶片", "黑白", "电影感"], "iso": "200-800"},
    "花卉": {"mode": "微距模式", "filters": ["鲜艳", "柔美", "自然"], "iso": "100-200"},
    "动物": {"mode": "运动模式", "filters": ["自然", "生动", "柔光"], "iso": "200-800"},
    "雪景": {"mode": "雪景模式", "filters": ["纯净", "高调", "冷白"], "iso": "100-200"},
    "室内": {"mode": "室内模式", "filters": ["暖调", "自然", "柔光"], "iso": "400-800"},
}


# ============================================================
# 工具 1: 场景识别
# ============================================================

def _analyze_image_traditional(img_b64: str) -> Dict[str, Any]:
    """
    传统图像分析方法 (不依赖外部API)
    基于图像统计特征做启发式场景判断
    """
    img = _b64_to_pil(img_b64)
    if img is None:
        return {"error": "cannot decode image"}

    img.thumbnail((512, 512))
    arr = np.array(img).astype(np.float32)

    brightness = arr.mean()
    r, g, b = arr[:, :, 0].mean(), arr[:, :, 1].mean(), arr[:, :, 2].mean()
    saturation = np.std([r, g, b])
    warmth = (r - b) / 255.0

    # heuristic scene detection
    if brightness < 80:
        scene = "城市夜景"
        confidence = min(0.9, 1.0 - brightness / 160)
    elif brightness > 200 and saturation < 20:
        scene = "雪景"
        confidence = 0.7
    elif warmth > 0.15:
        scene = "日落"
        confidence = min(0.85, warmth * 2)
    elif saturation > 40:
        scene = "花卉"
        confidence = min(0.8, saturation / 100)
    elif brightness < 120:
        scene = "室内"
        confidence = 0.65
    else:
        scene = "风景"
        confidence = 0.6

    config = SCENE_CONFIGS.get(scene, SCENE_CONFIGS["风景"])

    return {
        "primary_scene": scene,
        "confidence": round(confidence, 2),
        "lighting": "低光" if brightness < 100 else "正常" if brightness < 180 else "高亮",
        "brightness_level": round(brightness, 1),
        "warmth": "暖调" if warmth > 0.1 else "冷调" if warmth < -0.1 else "中性",
        "suggested_mode": config["mode"],
        "recommended_filters": config["filters"],
        "recommended_params": {"iso": config["iso"]},
        "analysis_method": "traditional (image statistics)",
    }


def scene_recognize_real(image_base64: str, return_suggestions: bool = True) -> Dict[str, Any]:
    """
    场景识别 - 真实实现
    
    策略:
    1. 先尝试 HuggingFace CLIP API (需要 HF_API_TOKEN)
    2. 失败则回退到传统图像分析
    """
    # 快速验证图片
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    # 尝试 HF CLIP API
    hf_result = None
    token = os.getenv("HF_API_TOKEN", "")

    if token:
        try:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            img_bytes = buf.getvalue()

            api_url = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
            payload = json.dumps({
                "inputs": {
                    "image": base64.b64encode(img_bytes).decode("utf-8"),
                },
                "parameters": {
                    "candidate_labels": SCENE_LABELS_CN,
                },
            }).encode("utf-8")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(api_url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())

            if isinstance(result, dict) and "labels" in result:
                best_label = result["labels"][0]
                best_score = result["scores"][0]
                hf_result = {
                    "primary_scene": best_label,
                    "confidence": round(best_score, 2),
                    "top3": [
                        {"label": result["labels"][i], "score": round(result["scores"][i], 2)}
                        for i in range(min(3, len(result["labels"])))
                    ],
                }
        except Exception as e:
            print(f"[real_tools] CLIP API failed, fallback to traditional: {e}")

    # 使用 CLIP 结果或回退
    if hf_result:
        scene = hf_result["primary_scene"]
        confidence = hf_result["confidence"]
    else:
        trad = _analyze_image_traditional(image_base64)
        if "error" in trad:
            return {"success": False, "error": trad["error"]}
        scene = trad["primary_scene"]
        confidence = trad["confidence"]
        hf_result = trad

    config = SCENE_CONFIGS.get(scene, SCENE_CONFIGS["风景"])

    result = {
        "success": True,
        "message": f"scene: {scene} (confidence: {confidence:.0%})",
        "scene_analysis": {
            "primary_scene": scene,
            "confidence": confidence,
            "suggested_mode": config["mode"],
            "recommended_params": {"iso": config["iso"]},
            "recommended_filters": config["filters"],
        },
    }

    if return_suggestions:
        result["scene_analysis"]["shooting_tips"] = [
            f"Use {config['mode']}",
            f"ISO range: {config['iso']}",
            f"Recommended filters: {', '.join(config['filters'][:2])}",
        ]

    if hf_result and "top3" in hf_result:
        result["scene_analysis"]["top3_predictions"] = hf_result["top3"]

    return result


# ============================================================
# 工具 2: 构图指导 (纯本地)
# ============================================================

def _detect_edges(arr: np.ndarray) -> np.ndarray:
    """Simple edge detection (Sobel-like)"""
    gray = np.mean(arr, axis=2)
    gy = np.abs(np.diff(gray, axis=0, append=gray[-1:, :]))
    gx = np.abs(np.diff(gray, axis=1, append=gray[:, -1:]))
    return np.sqrt(gx ** 2 + gy ** 2)


def _find_salient_region(arr: np.ndarray):
    """Find most salient region via edge density in 3x3 grid"""
    h, w = arr.shape[:2]
    edges = _detect_edges(arr)

    grid_h, grid_w = h // 3, w // 3
    best_density = 0
    best_gy, best_gx = 0, 0

    for gy in range(3):
        for gx in range(3):
            y1, y2 = gy * grid_h, min((gy + 1) * grid_h, h)
            x1, x2 = gx * grid_w, min((gx + 1) * grid_w, w)
            density = edges[y1:y2, x1:x2].mean()
            if density > best_density:
                best_density = density
                best_gy, best_gx = gy, gx

    cy = (best_gy + 0.5) / 3.0
    cx = (best_gx + 0.5) / 3.0
    return cx, cy, float(best_density)


def composition_guide_real(image_base64: str, scene_type: str = "auto",
                           detailed_feedback: bool = True) -> Dict[str, Any]:
    """
    构图指导 - 真实实现
    
    基于边缘检测 + 显著性分析:
    1. 定位主体
    2. 检查三分法对齐
    3. 检查水平
    4. 给出调整建议
    """
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    img.thumbnail((800, 800))
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]

    # 1. Find salient region
    cx, cy, saliency = _find_salient_region(arr)

    # 2. Rule of thirds check
    thirds = [1/3, 2/3]
    dist_x = min(abs(cx - t) for t in thirds)
    dist_y = min(abs(cy - t) for t in thirds)

    # 3. Centered check
    is_centered = abs(cx - 0.5) < 0.1 and abs(cy - 0.5) < 0.1

    # 4. Horizon check
    edges = _detect_edges(arr)
    top_edges = edges[:h//3, :].mean()
    bottom_edges = edges[2*h//3:, :].mean()
    horizon_tilt = abs(top_edges - bottom_edges) / max(edges.mean(), 1)

    # 5. Scores
    scores = []
    suggestions = []

    third_score = max(0, 100 - (dist_x + dist_y) * 200)
    scores.append({
        "rule": "三分法 (Rule of Thirds)",
        "score": round(third_score),
        "detail": f"subject offset: dx={dist_x:.2f}, dy={dist_y:.2f}"
    })

    if third_score < 70:
        if cx > 2/3:
            suggestions.append("Move subject left towards left 1/3 line")
        elif cx < 1/3:
            suggestions.append("Move subject right towards right 1/3 line")
        if cy > 2/3:
            suggestions.append("Move subject up towards upper 1/3 line")
        elif cy < 1/3:
            suggestions.append("Move subject down towards lower 1/3 line")
    else:
        suggestions.append("Rule of thirds looks good")

    sym_score = 85 if is_centered else 50
    scores.append({"rule": "对称 (Symmetry)", "score": sym_score})
    if is_centered:
        suggestions.append("Subject centered, good for symmetry")

    level_score = max(0, 100 - horizon_tilt * 200)
    scores.append({"rule": "水平 (Level)", "score": round(level_score)})
    if horizon_tilt > 0.3:
        suggestions.append("Image may be tilted, check horizon")

    overall = round(sum(s["score"] for s in scores) / len(scores))

    # 6. Adjustment tips
    adjustment_tips = []
    if third_score < 60:
        if cx < 0.4:
            adjustment_tips.append(f"Move camera right ~{int((0.5-cx)*100)}% frame width")
        elif cx > 0.6:
            adjustment_tips.append(f"Move camera left ~{int((cx-0.5)*100)}% frame width")
    if horizon_tilt > 0.3:
        adjustment_tips.append("Check level indicator, ensure horizon is level")
    if cy > 0.6:
        adjustment_tips.append("Lower camera, let subject rise to upper 1/3")
    elif cy < 0.4:
        adjustment_tips.append("Raise camera, let subject drop to lower 1/3")

    if not adjustment_tips:
        adjustment_tips = ["Composition looks good, ready to shoot!"]

    return {
        "success": True,
        "message": f"Composition analysis complete (overall: {overall}/100)",
        "composition_score": overall,
        "subject_position": {
            "x_ratio": round(cx, 3),
            "y_ratio": round(cy, 3),
            "description": (
                "centered" if is_centered
                else f"{'right' if cx > 0.55 else 'left' if cx < 0.45 else 'center'}-"
                     f"{'bottom' if cy > 0.55 else 'top' if cy < 0.45 else 'middle'}"
            ),
        },
        "scores": scores,
        "suggestions": suggestions,
        "adjustment_tips": adjustment_tips,
    }


# ============================================================
# 工具 3: 基础画质增强 (纯本地 Pillow)
# ============================================================

def photo_enhance_real(image_base64: str, enhance_level: str = "medium",
                       denoise: bool = True, sharpen: bool = True,
                       hdr_enhance: bool = True) -> Dict[str, Any]:
    """基础画质增强 - Pillow implementation"""
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    level_map = {"light": 1.15, "medium": 1.3, "strong": 1.5}
    factor = level_map.get(enhance_level, 1.3)

    original_size = img.size
    arr = np.array(img).astype(np.float32)
    mean_brightness = arr.mean()

    # Adaptive brightness
    if mean_brightness < 100:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(min(2.0, factor * 1.2))
    elif mean_brightness > 200:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(max(0.5, 1.0 / factor))

    # Contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(factor)

    # Sharpen
    if sharpen:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(factor * 1.2)

    # Color
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(min(1.5, factor * 0.9))

    enhanced_b64 = _pil_to_b64(img)

    return {
        "success": True,
        "message": f"增强完成 (level: {enhance_level})",
        "preview_url": f"data:image/jpeg;base64,{enhanced_b64}",
        "metrics": {
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "enhance_level": enhance_level,
            "brightness_adjusted": mean_brightness < 100 or mean_brightness > 200,
            "contrast_enhanced": True,
            "sharpened": sharpen,
            "color_boosted": True,
        },
        "note": "Basic enhancement (Pillow). Super-resolution/HDR denoising requires cloud GPU.",
    }


# ============================================================
# 工具 4: 色彩调校 (纯本地 Pillow)
# ============================================================

def color_grading_real(image_base64: str, color_preset: str = "auto",
                       temperature: int = 0, saturation: int = 0) -> Dict[str, Any]:
    """色彩调校 - Pillow + numpy implementation"""
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    arr = np.array(img).astype(np.float32)

    preset_params = {
        "auto": {"temp": 0, "sat": 1.1},
        "cinematic": {"temp": -5, "sat": 0.85},
        "spring": {"temp": 10, "sat": 1.2},
        "summer": {"temp": 5, "sat": 1.15},
        "autumn": {"temp": 15, "sat": 0.9},
        "winter": {"temp": -10, "sat": 0.8},
        "moody": {"temp": -8, "sat": 0.75},
        "vintage": {"temp": 12, "sat": 0.7},
        "futuristic": {"temp": -15, "sat": 1.3},
    }

    preset = preset_params.get(color_preset, preset_params["auto"])
    temp_adj = preset["temp"] + temperature * 0.2
    sat_adj = preset["sat"] + saturation * 0.01

    # Apply temperature (R-B shift)
    r_adj = 1.0 + temp_adj * 0.01
    b_adj = 1.0 - temp_adj * 0.01
    arr[:, :, 0] = np.clip(arr[:, :, 0] * r_adj, 0, 255)  # R
    arr[:, :, 2] = np.clip(arr[:, :, 2] * b_adj, 0, 255)  # B

    img = Image.fromarray(arr.astype(np.uint8))

    # Apply saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(np.clip(sat_adj, 0.1, 3.0))

    result_b64 = _pil_to_b64(img)

    preset_names = {
        "auto": "自动", "cinematic": "电影级", "spring": "春日",
        "summer": "夏日", "autumn": "秋日", "winter": "冬日",
        "moody": "情绪", "vintage": "复古", "futuristic": "未来感",
    }

    return {
        "success": True,
        "message": f"color grading: {preset_names.get(color_preset, color_preset)}",
        "preview_url": f"data:image/jpeg;base64,{result_b64}",
    }


# ============================================================
# 工具 5: 智能裁剪 (纯本地 PIL)
# ============================================================

# Aspect ratios with their common use cases
CROP_RATIOS = {
    "auto": None,
    "1:1": (1, 1, "方形 - Instagram/社交分享"),
    "4:3": (4, 3, "标准照片比例"),
    "16:9": (16, 9, "电影感/横屏壁纸"),
    "3:4": (3, 4, "竖屏人像"),
    "9:16": (9, 16, "手机壁纸/Story"),
}


def _score_crop(cx: float, cy: float, crop_w: int, crop_h: int,
                img_w: int, img_h: int) -> float:
    """
    Score a crop based on:
    - How centered the subject is in the crop
    - Rule of thirds alignment
    - Coverage (how much of the image is used)
    """
    # Subject position in crop coordinates (0-1)
    crop_cx = cx * img_w / crop_w
    crop_cy = cy * img_h / crop_h

    # Centering score (0-1): closer to 0.5 is better
    center_score = 1.0 - abs(crop_cx - 0.5) * 2

    # Rule of thirds score: subject near 1/3 or 2/3 intersections
    thirds = [1/3, 2/3]
    third_score = max(0.0, 1.0 - min(
        abs(crop_cx - t) + abs(crop_cy - u) for t in thirds for u in thirds
    ))

    # Coverage score
    coverage = (crop_w * crop_h) / (img_w * img_h)
    coverage_score = min(1.0, coverage * 2)

    return center_score * 0.3 + third_score * 0.4 + coverage_score * 0.3


def smart_crop_real(image_base64: str, target_ratio: str = "auto",
                    focus_subject: str = "") -> Dict[str, Any]:
    """
    智能裁剪 - 基于显著性检测

    1. 定位主体
    2. 为每个目标比例生成候选裁剪框
    3. 评分选出最佳裁剪
    """
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    w, h = img.size

    # Find salient region
    img_small = img.copy()
    img_small.thumbnail((800, 800))
    arr = np.array(img_small).astype(np.float32)
    cx, cy, saliency = _find_salient_region(arr)

    # Generate candidates
    candidates = []
    ratios_to_try = list(CROP_RATIOS.keys()) if target_ratio == "auto" else [target_ratio]

    for ratio_key in ratios_to_try:
        if ratio_key == "auto":
            continue

        ratio_info = CROP_RATIOS[ratio_key]
        rw, rh = ratio_info[0], ratio_info[1]
        ratio_desc = ratio_info[2]

        # Calculate crop dimensions within original image bounds
        if w / h >= rw / rh:
            # Image is wider than target ratio
            crop_h = h
            crop_w = int(h * rw / rh)
        else:
            # Image is taller than target ratio
            crop_w = w
            crop_h = int(w * rh / rw)

        # Center crop on subject
        crop_x = int(cx * w - crop_w / 2)
        crop_y = int(cy * h - crop_h / 2)

        # Clamp to image bounds
        crop_x = max(0, min(crop_x, w - crop_w))
        crop_y = max(0, min(crop_y, h - crop_h))

        # Score this crop
        score = _score_crop(cx, cy, crop_w, crop_h, w, h)

        candidates.append({
            "ratio": ratio_key,
            "description": ratio_desc,
            "crop_box": [crop_x, crop_y, crop_x + crop_w, crop_y + crop_h],
            "dimensions": f"{crop_w}x{crop_h}",
            "score": round(score * 100),
        })

    # Sort by score
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Generate preview of best crop
    best = candidates[0]
    crop_box = best["crop_box"]
    cropped = img.crop(crop_box)
    preview_b64 = _pil_to_b64(cropped)

    return {
        "success": True,
        "message": f"smart crop: {best['ratio']} ({best['dimensions']})",
        "preview_url": f"data:image/jpeg;base64,{preview_b64}",
        "candidates": candidates[:3],
        "best_crop": best,
        "subject_position": {"x": round(cx, 2), "y": round(cy, 2)},
    }


# ============================================================
# 工具 6: 人像美化 (纯本地 PIL)
# ============================================================

def _estimate_skin_mask(arr: np.ndarray) -> np.ndarray:
    """
    Estimate skin regions using simple color thresholds.
    Returns a mask (0-1 float) where higher values = more likely skin.
    """
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Skin color heuristics in RGB
    skin = (
        (r > 95) & (g > 40) & (b > 20) &
        (r > g) & (r > b) &
        (np.abs(r - g) > 15) &
        (r - np.minimum(g, b) > 15)
    )

    mask = skin.astype(np.float32)

    # Soften mask with blur
    from scipy.ndimage import gaussian_filter
    try:
        mask = gaussian_filter(mask, sigma=5)
    except ImportError:
        # Fallback: simple box blur with numpy
        kernel_size = 7
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size ** 2)
        h, w = mask.shape
        pad = kernel_size // 2
        padded = np.pad(mask, pad, mode='edge')
        for y in range(h):
            for x in range(w):
                mask[y, x] = np.sum(padded[y:y+kernel_size, x:x+kernel_size] * kernel)

    return np.clip(mask, 0, 1)


def portrait_beautify_real(image_base64: str, beauty_level: str = "natural",
                           skin_smoothing: int = 30, face_slimming: int = 0,
                           eye_enhance: int = 0, whitening: int = 25,
                           makeup_style: str = "fresh") -> Dict[str, Any]:
    """
    人像美化 - 基础版 (PIL + numpy)

    实现：
    1. 肤色检测 + 柔焦磨皮
    2. 肤色美白
    3. 对比度微调
    """
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    arr = np.array(img).astype(np.float32)

    # Level-based parameters
    level_params = {
        "natural": {"smooth": 0.3, "white": 0.15, "contrast": 1.05},
        "moderate": {"smooth": 0.5, "white": 0.3, "contrast": 1.1},
        "glamour": {"smooth": 0.7, "white": 0.45, "contrast": 1.15},
    }
    params = level_params.get(beauty_level, level_params["natural"])

    # Override with explicit params
    smooth_strength = (params["smooth"] + skin_smoothing / 100) / 2
    white_strength = (params["white"] + whitening / 100) / 2

    # Estimate skin mask
    skin_mask = _estimate_skin_mask(arr)

    # 1. Skin smoothing via Gaussian blur + blend
    if smooth_strength > 0:
        blurred = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=3)))
        blur_factor = smooth_strength * 0.6
        for c in range(3):
            arr[:, :, c] = arr[:, :, c] * (1 - blur_factor * skin_mask) + \
                           blurred[:, :, c] * (blur_factor * skin_mask)

    # 2. Whitening
    if white_strength > 0:
        whiten = white_strength * 0.4
        for c in range(3):
            arr[:, :, c] = np.clip(
                arr[:, :, c] * (1 - whiten * skin_mask) + 255 * whiten * skin_mask,
                0, 255
            )

    img = Image.fromarray(arr.astype(np.uint8))

    # 3. Contrast boost
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(params["contrast"])

    # 4. Slight color warming for "fresh" look
    if makeup_style in ("fresh", "korean"):
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.85)  # slightly desaturated for Korean look

    result_b64 = _pil_to_b64(img)

    return {
        "success": True,
        "message": f"portrait beautify: {beauty_level}",
        "preview_url": f"data:image/jpeg;base64,{result_b64}",
        "params": {
            "beauty_level": beauty_level,
            "skin_smoothing": round(smooth_strength * 100),
            "whitening": round(white_strength * 100),
            "texture_preservation": "basic (PIL)",
        },
        "note": "Basic beautification. AI-powered face landmark detection needs MediaPipe cloud API.",
    }


# ============================================================
# 工具 7: 风格迁移 (PIL 本地 + HF API)
# ============================================================

# Styles that can be done locally with PIL
LOCAL_STYLES = {
    "minimal_bw": "极简黑白",
    "film_retro": "胶片复古",
    "oil_painting": "油画效果",
    "watercolor": "水彩效果",
    "sketch": "素描",
    "emboss": "浮雕",
}

# Styles that need AI API
AI_STYLES = {
    "anime": "动漫风格",
    "cyberpunk": "赛博朋克",
    "chinese_ink": "中国水墨",
    "vivo_signature": "vivo标志性风格",
    "pixel_art": "像素艺术",
    "clay_style": "粘土风格",
    "pop_art": "波普艺术",
}


def _apply_local_style(img: Image.Image, style: str, strength: float) -> Image.Image:
    """Apply local PIL-based style transfer"""
    arr = np.array(img).astype(np.float32)

    if style == "minimal_bw":
        # Convert to grayscale
        gray = np.mean(arr, axis=2)
        for c in range(3):
            arr[:, :, c] = gray
        img = Image.fromarray(arr.astype(np.uint8))
        # Boost contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)

    elif style == "film_retro":
        # Warm color shift + slight desaturation + vignette
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15, 0, 255)  # R boost
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.85, 0, 255)  # B reduce
        img = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.7)
        # Add vignette (darken corners)
        h, w = arr.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        vignette = 1.0 - 0.4 * (dist / max_dist) ** 2
        vignette = np.clip(vignette, 0.6, 1.0)
        arr2 = np.array(img).astype(np.float32)
        for c in range(3):
            arr2[:, :, c] *= vignette
        img = Image.fromarray(arr2.astype(np.uint8))

    elif style == "oil_painting":
        # Oil painting effect: heavy smoothing + edge enhancement
        img = img.filter(ImageFilter.ModeFilter(size=5))
        img = img.filter(ImageFilter.SMOOTH_MORE)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)
        # Apply unsharp mask
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    elif style == "watercolor":
        # Soft blur + light color boost
        img = img.filter(ImageFilter.SMOOTH_MORE)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.85)

    elif style == "sketch":
        # Pencil sketch: edge detection + invert
        gray = np.mean(arr, axis=2)
        # Simple edge detection
        blurred = np.array(Image.fromarray(gray.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=3)))
        edges = np.abs(gray - blurred)
        # Invert for sketch look
        sketch = 255 - np.clip(edges * 3, 0, 255)
        # Mix with original
        result = sketch * 0.7 + gray * 0.3
        # Expand to 3 channels
        arr_sketch = np.stack([result, result, result], axis=2).astype(np.uint8)
        img = Image.fromarray(arr_sketch)

    elif style == "emboss":
        img = img.filter(ImageFilter.EMBOSS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)

    else:
        # Unknown style, just boost color + contrast
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)

    return img


def _hf_style_transfer(img_bytes: bytes, style: str) -> Optional[bytes]:
    """
    Try HuggingFace API for AI style transfer.
    Uses different models for different styles.
    """
    token = os.getenv("HF_API_TOKEN", "")
    if not token:
        return None

    try:
        if style == "anime":
            # Use animeganv2 for anime style
            api_url = "https://api-inference.huggingface.co/models/Ojimi/anime-kawai-diffusion"
        elif style == "cyberpunk":
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
        else:
            # General style transfer
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        }
        req = urllib.request.Request(api_url, data=img_bytes, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        print(f"[real_tools] HF style transfer failed: {e}")
        return None


def style_transfer_real(image_base64: str, style: str = "anime",
                        strength: float = 0.7, preserve_face: bool = True) -> Dict[str, Any]:
    """
    风格迁移 - 混合实现

    简单风格（黑白/复古/油画/水彩/素描）→ PIL 本地处理
    AI 风格（动漫/赛博朋克/水墨）→ HF API → PIL 回退
    """
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    all_styles = {**LOCAL_STYLES, **AI_STYLES}
    style_name = all_styles.get(style, style)

    original_size = img.size

    # Try HF API first for AI styles
    hf_result = None
    if style in AI_STYLES:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        hf_result = _hf_style_transfer(buf.getvalue(), style)
        if hf_result:
            try:
                img = Image.open(io.BytesIO(hf_result)).convert("RGB")
                img = img.resize(original_size)
            except Exception:
                hf_result = None

    # Fallback to local PIL style
    if hf_result is None:
        img = _apply_local_style(img, style, strength)

    result_b64 = _pil_to_b64(img)

    method = "HF API" if hf_result else ("PIL local" if style in LOCAL_STYLES else "PIL fallback")

    return {
        "success": True,
        "message": f"style transfer: {style_name} ({method})",
        "preview_url": f"data:image/jpeg;base64,{result_b64}",
        "style_applied": style,
        "method": method,
        "note": (
            "AI-powered style transfer (HF API)." if hf_result
            else "Local PIL style processing. For AI styles, set HF_API_TOKEN."
        ),
    }


# ============================================================
# 工具 8: 动态照片 (纯本地 PIL - 视差 3D)
# ============================================================

def motion_photo_real(image_base64: str, motion_type: str = "parallax_3d",
                      duration_seconds: float = 3.0) -> Dict[str, Any]:
    """
    动态照片 - 视差 3D 效果

    实现方式：生成多层偏移图像模拟 3D 视差
    实际产出是多个偏移帧的 base64 列表（可合成 GIF/视频）
    """
    img = _b64_to_pil(image_base64)
    if img is None:
        return {"success": False, "error": "cannot decode image"}

    w, h = img.size

    if motion_type == "parallax_3d":
        # Create depth illusion with offset layers
        frames = []
        num_frames = max(3, int(duration_seconds * 8))  # ~8fps

        for i in range(num_frames):
            # Sinusoidal offset for smooth back-and-forth motion
            t = i / max(1, num_frames - 1)
            offset_x = int(np.sin(t * np.pi * 2) * w * 0.03)
            offset_y = int(np.cos(t * np.pi * 2) * h * 0.02)

            # Crop and offset
            crop_box = (
                max(0, -offset_x),
                max(0, -offset_y),
                min(w, w - offset_x),
                min(h, h - offset_y),
            )
            paste_pos = (max(0, offset_x), max(0, offset_y))

            frame = Image.new("RGB", (w, h), (0, 0, 0))
            cropped = img.crop(crop_box)
            frame.paste(cropped, paste_pos)

            frames.append(_pil_to_b64(frame, quality=85))

        # Build animated GIF preview
        gif_buf = io.BytesIO()
        frames_pil = [Image.open(io.BytesIO(base64.b64decode(f))) for f in frames]
        frames_pil[0].save(
            gif_buf,
            format="GIF",
            save_all=True,
            append_images=frames_pil[1:],
            duration=int(duration_seconds * 1000 / num_frames),
            loop=0,
        )
        gif_b64 = base64.b64encode(gif_buf.getvalue()).decode()

        return {
            "success": True,
            "message": f"motion photo: parallax 3D ({num_frames} frames, {duration_seconds}s)",
            "preview_url": f"data:image/gif;base64,{gif_b64}",
            "frames": len(frames),
            "duration_seconds": duration_seconds,
            "note": "Simple parallax effect (PIL). Advanced effects (cinemagraph, flowing) need cloud AI.",
        }

    elif motion_type == "gentle_breeze":
        # Simulate wind effect with horizontal wave distortion
        arr = np.array(img).astype(np.float32)
        h, w = arr.shape[:2]
        frames = []
        num_frames = max(3, int(duration_seconds * 6))

        for i in range(num_frames):
            t = i / max(1, num_frames - 1)
            offset = np.sin(t * np.pi * 2) * 5
            frame_arr = arr.copy()
            for y in range(h):
                wave = int(np.sin(y / 30.0 + t * 10) * offset)
                frame_arr[y] = np.roll(frame_arr[y], wave, axis=0)
            frame_img = Image.fromarray(frame_arr.astype(np.uint8))
            frames.append(_pil_to_b64(frame_img, quality=85))

        gif_buf = io.BytesIO()
        frames_pil = [Image.open(io.BytesIO(base64.b64decode(f))) for f in frames]
        frames_pil[0].save(
            gif_buf, format="GIF", save_all=True,
            append_images=frames_pil[1:],
            duration=int(duration_seconds * 1000 / num_frames), loop=0,
        )
        gif_b64 = base64.b64encode(gif_buf.getvalue()).decode()

        return {
            "success": True,
            "message": f"motion photo: gentle breeze ({num_frames} frames)",
            "preview_url": f"data:image/gif;base64,{gif_b64}",
            "frames": len(frames),
            "note": "Basic wave distortion. Cinemagraph needs cloud AI.",
        }

    else:
        return {
            "success": False,
            "error": f"Motion type '{motion_type}' requires cloud AI (depth estimation model)."
        }


# ============================================================
# 工具注册
# ============================================================

REAL_TOOL_MAP = {
    "scene_recognize": scene_recognize_real,
    "composition_guide": composition_guide_real,
    "photo_enhance": photo_enhance_real,
    "color_grading": color_grading_real,
    "smart_crop": smart_crop_real,
    "portrait_beautify": portrait_beautify_real,
    "style_transfer": style_transfer_real,
    "motion_photo": motion_photo_real,
    # not yet implemented (need cloud AI):
    # "object_remove" - needs SAM + LaMa inpainting
    # "ai_expand" - needs SD Outpainting
}


def has_real_implementation(tool_name: str) -> bool:
    """Check if tool has real implementation"""
    return tool_name in REAL_TOOL_MAP


def execute_real_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a real tool by name"""
    func = REAL_TOOL_MAP.get(tool_name)
    if func is None:
        return {"success": False, "error": f"Tool '{tool_name}' not yet implemented"}
    return func(**kwargs)
