import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from typing import Dict, Tuple
from io import BytesIO
from moviepy import ImageClip

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

def create_premium_banner(product_data: Dict, platform: str = "x") -> str:
    """
    超高品質なSNS用バナー画像を生成します。
    """
    # サイズ設定
    if platform.lower() == "x":
        size = (1200, 675)
    elif platform.lower() == "instagram":
        size = (1080, 1080)
    else:
        size = (1080, 1350)

    # 商品画像のダウンロード
    image_url = product_data.get("imageUrl")
    if not image_url: return ""
    
    try:
        product_img = download_image(image_url)
    except: return ""

    # 1. 洗練されたグラデーション背景の作成
    bg = Image.new("RGBA", size, (20, 20, 30, 255))
    draw = ImageDraw.Draw(bg)
    
    # 放射状グラデーション（ライティング効果）
    for r in range(max(size), 0, -10):
        alpha = int(150 * (1 - r / max(size)))
        draw.ellipse([(size[0]//2 - r, size[1]//2 - r), (size[0]//2 + r, size[1]//2 + r)], 
                     fill=(80, 50, 120, alpha))

    # 2. メイン商品の加工（ドロップシャドウ + 柔らかな角丸）
    max_prod_h = int(size[1] * 0.6)
    prod_w = int(product_img.width * (max_prod_h / product_img.height))
    product_img = product_img.resize((prod_w, max_prod_h), Image.Resampling.LANCZOS)
    
    # シャドウ用キャンバス
    shadow_offset = 20
    shadow = Image.new("RGBA", (prod_w + 60, max_prod_h + 60), (0,0,0,0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle((20, 20, prod_w+20, max_prod_h+20), radius=40, fill=(0,0,0,120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
    
    # 中央に配置
    pos_x = (size[0] - prod_w) // 2
    pos_y = (size[1] - max_prod_h) // 2 - 40
    bg.paste(shadow, (pos_x - 10, pos_y - 10), shadow)
    
    # 商品本体
    mask = Image.new("L", (prod_w, max_prod_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, prod_w, max_prod_h), radius=40, fill=255)
    bg.paste(product_img, (pos_x, pos_y), mask)

    # 3. 高級感のあるテキストデザイン
    draw = ImageDraw.Draw(bg)
    font_title = get_japanese_font(45)
    font_price = get_japanese_font(80)
    font_tag = get_japanese_font(25)

    title = product_data.get("itemName", "RECOMMENDED")
    if len(title) > 25: title = title[:23] + "..."
    price = f"¥{product_data.get('itemPrice', 0):,}"

    # タイトル（中央揃え）
    t_bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((size[0] - (t_bbox[2]-t_bbox[0]))//2, size[1] - 180), title, font=font_title, fill="white")

    # 価格（ダイナミックな表示）
    p_bbox = draw.textbbox((0, 0), price, font=font_price)
    p_w, p_h = p_bbox[2]-p_bbox[0], p_bbox[3]-p_bbox[1]
    draw.text(((size[0]-p_w)//2, size[1]-110), price, font=font_price, fill=(255, 230, 100)) # 金色に近い黄色

    # 4. 装飾（アクセントライン）
    line_y = size[1] - 125
    draw.line([(size[0]//2 - 150, line_y), (size[0]//2 + 150, line_y)], fill=(255,255,255,100), width=2)

    # トレンドバッジ
    draw.rounded_rectangle((30, 30, 200, 70), radius=10, fill=(255, 200, 0))
    draw.text((50, 35), "★ TREND", font=font_tag, fill="black")

    # 保存
    os.makedirs("output/media", exist_ok=True)
    filename = f"output/media/post_{platform}_{product_data.get('itemCode', 'temp')}.png"
    bg.convert("RGB").save(filename, quality=95)
    return filename

def create_short_video(image_path: str, output_path: str = None) -> str:
    """ズームアニメーション付きの高品質な動画を生成する"""
    if not image_path or not os.path.exists(image_path): return ""
    if not output_path: output_path = image_path.replace(".png", ".mp4")
    
    print(f"[Media Generator] 高品質動画を生成中: {output_path}")
    try:
        # ケンバーンズ効果（ゆっくりズーム）を適用
        clip = ImageClip(image_path, duration=5)
        clip = clip.resize(lambda t: 1 + 0.05 * t) # 5秒間で5%ズーム
        clip = clip.set_position(('center', 'center'))
        
        clip.write_videofile(output_path, fps=30, codec="libx264", audio=False, logger=None)
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
