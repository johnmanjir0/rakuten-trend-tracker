import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from typing import Dict, Tuple
from io import BytesIO
from moviepy import ImageClip, VideoClip
import moviepy.video.fx as vfx

def download_image(url: str) -> Image.Image:
    """URLから画像をダウンロードしてPIL Imageオブジェクトを返す"""
    print(f"[Media Generator] 画像をダウンロード中: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")

def get_japanese_font(size: int):
    """環境に応じた日本語フォントを取得する"""
    font_paths = [
        # Linux (Streamlit Cloud)
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        # macOS
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/AppleGothic.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception as e:
                print(f"[Media Generator] フォント読み込み失敗 ({path}): {e}")
                continue
    print("[Media Generator] 日本語フォントが見つかりません。デフォルトフォントを使用します。")
    return ImageFont.load_default()

def create_premium_banner(product_data: Dict, platform: str = "x", info: Dict = None) -> str:
    """
    スタジオ撮影のような高品質でシンプルなバナーを生成。
    商品の見やすさを最優先する。
    """
    if platform.lower() == "x": size = (1200, 675)
    else: size = (1080, 1080)

    image_url = product_data.get("imageUrl")
    if not image_url: return ""
    try: product_img = download_image(image_url)
    except: return ""

    # 1. シンプルでモダンなスタジオ背景（白または淡いグレーのグラデーション）
    bg = Image.new("RGBA", size, (250, 250, 250, 255))
    draw = ImageDraw.Draw(bg)
    
    # 柔らかなライティング
    for r in range(size[0], 0, -20):
        alpha = int(20 * (1 - r / size[0]))
        draw.ellipse([(size[0]//2 - r, size[1] - r), (size[0]//2 + r, size[1] + r)], 
                     fill=(0, 0, 0, alpha))

    # 2. 商品の見やすさを最大化
    max_h = int(size[1] * 0.65)
    product_img.thumbnail((size[0], max_h), Image.Resampling.LANCZOS)
    p_w, p_h = product_img.size
    
    # 柔らかなドロップシャドウ（商品の存在感を出す）
    shadow = Image.new("RGBA", (p_w + 40, p_h + 40), (0,0,0,0))
    ImageDraw.Draw(shadow).ellipse([10, 10, p_w+30, p_h+30], fill=(0,0,0,40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
    
    pos_x, pos_y = (size[0]-p_w)//2, (size[1]-p_h)//2 - 50
    bg.paste(shadow, (pos_x-10, pos_y+10), shadow)
    bg.paste(product_img, (pos_x, pos_y), product_img if product_img.mode == 'RGBA' else None)

    # 3. シンプルかつ洗練されたタイポグラフィ
    font_main = get_japanese_font(35)
    font_bold = get_japanese_font(60)
    
    # キャッチコピー（もしあれば）
    hook = info.get("hook", "Special Pick") if info else "Recommended"
    draw.text((size[0]//2, size[1]-150), hook.upper(), font=font_main, fill=(100, 100, 100), anchor="mm")
    
    # 価格
    price = f"¥{product_data.get('itemPrice', 0):,}"
    draw.text((size[0]//2, size[1]-80), price, font=font_bold, fill=(191, 0, 0), anchor="mm")

    # 保存
    os.makedirs("output/media", exist_ok=True)
    filename = f"output/media/post_{platform}_{product_data.get('itemCode', 'temp')}.png"
    bg.convert("RGB").save(filename, quality=100)
    return filename

def create_short_video(image_path: str, product_data: Dict, info: Dict) -> str:
    """
    商品のベネフィット情報をテロップとして差し込む、プロ仕様のショート動画広告を生成。
    """
    if not image_path or not os.path.exists(image_path): return ""
    output_path = image_path.replace(".png", ".mp4")
    
    from moviepy import CompositeVideoClip
    import numpy as np

    print(f"[Media Generator] プロ品質動画を生成中: {output_path}")
    try:
        # 背景（ズームする商品画像）
        bg_clip = ImageClip(image_path, duration=6)
        
        # ズーム効果
        def zoom_effect(get_frame, t):
            frame = get_frame(t)
            zoom = 1 + (0.1 * t / 6)
            img = Image.fromarray(frame)
            w, h = img.size
            new_w, new_h = int(w * zoom), int(h * zoom)
            img_zoomed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left, top = (new_w - w) // 2, (new_h - h) // 2
            return np.array(img_zoomed.crop((left, top, left + w, top + h)))

        bg_clip = bg_clip.transform(zoom_effect)

        # テロップ生成関数
        def create_telop(text, start, duration, y_pos, color="white", bg_color=(191, 0, 0)):
            t_font = get_japanese_font(40)
            img = Image.new("RGBA", (800, 80), (0,0,0,0))
            d = ImageDraw.Draw(img)
            bbox = d.textbbox((0,0), text, font=t_font)
            tw = bbox[2]-bbox[0]
            d.rounded_rectangle(((800-tw)//2 - 20, 10, (800+tw)//2 + 20, 70), radius=10, fill=bg_color)
            d.text((400, 40), text, font=t_font, fill=color, anchor="mm")
            return ImageClip(np.array(img), duration=duration).with_start(start).with_position(("center", y_pos))

        # AIが生成した情報を差し込む
        t1 = create_telop(info.get("hook", "今、売れてます！"), 0.5, 2.0, 100)
        t2 = create_telop(info.get("benefit1", "圧倒的な満足度"), 2.0, 2.0, 200)
        t3 = create_telop(info.get("benefit2", "生活が変わる逸品"), 3.5, 2.5, 300)

        final_clip = CompositeVideoClip([bg_clip, t1, t2, t3])
        final_clip.write_videofile(output_path, fps=30, codec="libx264", audio=False, logger=None, preset="medium")
        return output_path
    except Exception as e:
        print(f"[Media Generator] 動画生成エラー: {e}")
        return ""

if __name__ == "__main__":
    # テスト
    dummy_product = {
        "itemName": "テスト用のおしゃれな商品タイトル",
        "itemPrice": 2980,
        "imageUrl": "https://picsum.photos/800/800",
        "itemCode": "test_placeholder"
    }
    create_premium_banner(dummy_product, "x")
    create_premium_banner(dummy_product, "instagram")
