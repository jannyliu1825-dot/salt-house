#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_icons.py
------------
產生台南鹽行溫馨套房 PWA 所需的所有圖示 (icons)。

用法:
    python3 gen_icons.py

會在 ./icons 資料夾內產生：
    icon-72.png
    icon-96.png
    icon-128.png
    icon-144.png
    icon-152.png
    icon-180.png   (Apple Touch Icon)
    icon-192.png
    icon-192-maskable.png
    icon-384.png
    icon-512.png
    icon-512-maskable.png
    favicon.ico

需求套件: Pillow (pip install Pillow --break-system-packages)
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# 品牌配色 (與網站 Tailwind amber-500 / gray-900 呼應)
BG_COLOR = "#f59e0b"        # amber-500
BG_COLOR_DARK = "#d97706"   # amber-600 (漸層用)
FG_COLOR = "#ffffff"        # 白色前景 (文字/圖案)
DARK_TEXT_COLOR = "#1f2937"  # gray-800

# 一般用途 (any) 圖示尺寸
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
# Apple Touch Icon 額外尺寸
APPLE_SIZE = 180
# Maskable 圖示尺寸 (需要留安全邊界 safe zone，內容須置中且不超過約 80% 範圍)
MASKABLE_SIZES = [192, 512]

# 嘗試尋找系統上的中文字型 (Noto Sans CJK TC 優先)
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def find_font_path():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


FONT_PATH = find_font_path()


def load_font(size):
    """載入中文字型；若找不到則退回 Pillow 內建字型。"""
    if FONT_PATH:
        try:
            # .ttc 字型集合檔，index 2 通常對應 Noto Sans CJK TC (依系統而定，找不到就用 0)
            for idx in (2, 0):
                try:
                    return ImageFont.truetype(FONT_PATH, size, index=idx)
                except Exception:
                    continue
        except Exception:
            pass
    return ImageFont.load_default()


def draw_rounded_gradient_bg(size, radius_ratio=0.22):
    """畫一個帶圓角、由 amber-500 到 amber-600 對角漸層的背景。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 建立漸層底圖 (簡單對角漸層)
    gradient = Image.new("RGB", (size, size), BG_COLOR)
    top = tuple(int(BG_COLOR[i:i + 2], 16) for i in (1, 3, 5))
    bottom = tuple(int(BG_COLOR_DARK[i:i + 2], 16) for i in (1, 3, 5))
    pixels = gradient.load()
    for y in range(size):
        ratio = y / max(size - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(size):
            pixels[x, y] = (r, g, b)

    # 圓角遮罩
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    radius = int(size * radius_ratio)
    mdraw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    img.paste(gradient, (0, 0), mask)
    return img


def draw_house_glyph(draw, size, color, scale=1.0):
    """
    在畫布中央畫一個簡單的「房子＋床」意象線條圖，
    代表『套房出租』的視覺主題，取代真實照片。
    座標皆以 size 為基準做比例縮放。
    """
    cx, cy = size / 2, size / 2
    s = size * 0.5 * scale  # 房子整體半寬

    # 房子屋頂 (三角形)
    roof = [
        (cx, cy - s * 0.95),
        (cx - s * 0.85, cy - s * 0.15),
        (cx + s * 0.85, cy - s * 0.15),
    ]
    draw.polygon(roof, fill=color)

    # 房子牆身 (矩形)
    wall_left = cx - s * 0.6
    wall_right = cx + s * 0.6
    wall_top = cy - s * 0.2
    wall_bottom = cy + s * 0.75
    draw.rectangle([wall_left, wall_top, wall_right, wall_bottom], fill=color)

    # 挖空門框 (用背景色的洞代表門，讓造型更立體) - 這裡改用簡單的內縮矩形製造門
    door_w = s * 0.42
    door_h = s * 0.55
    door_left = cx - door_w / 2
    door_top = wall_bottom - door_h
    # 用透明挖洞：畫在 RGBA 圖上時，這裡直接用稍淺的顏色表示門
    lighter = tuple(min(255, c + 40) if isinstance(color, tuple) else 255 for c in (color if isinstance(color, tuple) else (255, 255, 255)))
    draw.rectangle([door_left, door_top, door_left + door_w, wall_bottom], fill=BG_COLOR)


def render_icon(size, maskable=False):
    """
    產生單一尺寸圖示。
    maskable=True 時，內容會縮小並置中，保留安全邊界，
    以符合 PWA maskable icon 的規範 (avoid content clipped by OS masks)。
    """
    canvas_size = size
    img = draw_rounded_gradient_bg(canvas_size, radius_ratio=0.0 if maskable else 0.22)
    if maskable:
        # maskable icon 底圖建議不要圓角(讓系統自行裁切形狀)，改用滿版背景色
        img = Image.new("RGBA", (canvas_size, canvas_size), BG_COLOR)
        grad = draw_rounded_gradient_bg(canvas_size, radius_ratio=0.0)
        img.paste(grad, (0, 0))

    draw = ImageDraw.Draw(img)

    # 內容縮放比例：maskable 需要約 80% 安全區，一般圖示可以滿版
    content_scale = 0.62 if maskable else 0.82

    draw_house_glyph(draw, canvas_size, FG_COLOR, scale=content_scale)

    # 加上「鹽」字作為品牌識別，置於房子下方 (只在較大尺寸才加文字，避免小尺寸糊掉)
    if canvas_size >= 96:
        font_size = int(canvas_size * 0.16)
        font = load_font(font_size)
        text = "鹽"
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = font_size, font_size
        tx = (canvas_size - tw) / 2 - bbox[0]
        ty = canvas_size * (0.78 if not maskable else 0.72) - th / 2 - bbox[1]
        draw.text((tx, ty), text, font=font, fill=FG_COLOR)

    return img.convert("RGBA")


def save_favicon(png_path_512, out_path):
    """由 512px PNG 產生多尺寸 favicon.ico"""
    img = Image.open(png_path_512).convert("RGBA")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    img.save(out_path, format="ICO", sizes=sizes)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"輸出資料夾: {OUTPUT_DIR}")
    if FONT_PATH:
        print(f"使用字型: {FONT_PATH}")
    else:
        print("警告: 找不到中文字型，將以預設字型繪製（可能無法顯示中文）。")

    generated = {}

    # 一般 (any) 圖示
    for size in ICON_SIZES:
        icon = render_icon(size, maskable=False)
        out_path = os.path.join(OUTPUT_DIR, f"icon-{size}.png")
        icon.save(out_path, format="PNG")
        generated[size] = out_path
        print(f"已產生: icon-{size}.png")

    # Apple Touch Icon (不需透明背景，蘋果會自動加圓角)
    apple_icon = render_icon(APPLE_SIZE, maskable=False).convert("RGB")
    apple_path = os.path.join(OUTPUT_DIR, f"icon-{APPLE_SIZE}.png")
    apple_icon.save(apple_path, format="PNG")
    print(f"已產生: icon-{APPLE_SIZE}.png (Apple Touch Icon)")

    # Maskable 圖示
    for size in MASKABLE_SIZES:
        icon = render_icon(size, maskable=True)
        out_path = os.path.join(OUTPUT_DIR, f"icon-{size}-maskable.png")
        icon.save(out_path, format="PNG")
        print(f"已產生: icon-{size}-maskable.png")

    # favicon.ico (使用 512 版本縮製多尺寸)
    favicon_path = os.path.join(OUTPUT_DIR, "favicon.ico")
    save_favicon(generated[512], favicon_path)
    print("已產生: favicon.ico")

    print("\n全部圖示產生完成！")


if __name__ == "__main__":
    main()
