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
    プレミアム感のあるSNS用バナー画像を生成します。
    
    Args:
        product_data (Dict): 商品データ (title, price, imageUrl)
        platform (str): 'x' (1200x675) または 'instagram' (1080x1080)
        
    Returns:
        str: 生成された画像の保存パス
    """
    # サイズ設定
    if platform.lower() == "x":
        size = (1200, 675)
    elif platform.lower() == "instagram":
        size = (1080, 1080)
    else:
        size = (1080, 1350) # Portrait

    # 商品画像のダウンロード
    image_url = product_data.get("imageUrl")
    if not image_url:
        print("[Media Generator] 画像URLがないため生成をスキップします。")
        return ""
    
    try:
        product_img = download_image(image_url)
    except Exception as e:
        print(f"[Media Generator] 画像ダウンロードエラー: {e}")
        return ""

    # 背景の作成 (商品画像をぼかして背景にする)
    bg = product_img.resize(size, Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    # 少し暗くする
    overlay = Image.new("RGBA", size, (0, 0, 0, 100))
    bg.paste(overlay, (0, 0), overlay)

    # メイン商品画像の加工 (角丸 + シャドウ)
    # アスペクト比を維持してリサイズ
    max_prod_h = int(size[1] * 0.7)
    prod_w = int(product_img.width * (max_prod_h / product_img.height))
    product_img = product_img.resize((prod_w, max_prod_h), Image.Resampling.LANCZOS)
    
    # 角丸マスク
    radius = 30
    mask = Image.new("L", (prod_w, max_prod_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, prod_w, max_prod_h), radius=radius, fill=255)
    
    # 中央に配置
    pos_x = (size[0] - prod_w) // 2
    pos_y = (size[1] - max_prod_h) // 2 - 20
    bg.paste(product_img, (pos_x, pos_y), mask)

    # テキストの描画
    draw = ImageDraw.Draw(bg)
    font_title = get_japanese_font(40)
    font_price = get_japanese_font(60)
    font_tag = get_japanese_font(30)

    title = product_data.get("itemName", "おすすめ商品")
    if len(title) > 30:
        title = title[:28] + "..."
    
    price = f"¥{product_data.get('itemPrice', 0):,}"
    
    # タイトル表示 (下部中央)
    def draw_text_with_shadow(draw, position, text, font, fill="white", shadow="black"):
        x, y = position
        # 影
        draw.text((x+2, y+2), text, font=font, fill=shadow)
        # 本文
        draw.text((x, y), text, font=font, fill=fill)

    bbox = draw.textbbox((0, 0), title, font=font_title)
    text_w = bbox[2] - bbox[0]
    title_y = size[1] - 160
    draw_text_with_shadow(draw, ((size[0] - text_w) // 2, title_y), title, font=font_title)

    # 価格表示 (アクセントカラーの帯)
    bbox_p = draw.textbbox((0, 0), price, font=font_price)
    pw = bbox_p[2] - bbox_p[0]
    ph = bbox_p[3] - bbox_p[1]
    
    badge_w, badge_h = pw + 60, ph + 40
    badge_x, badge_y = (size[0] - badge_w) // 2, size[1] - 100
    draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=15, fill=(191, 0, 0))
    draw.text((badge_x + 30, badge_y + 10), price, font=font_price, fill="white", weight="bold")

    # トレンドタグ
    draw.text((30, 30), "TRENDING", font=font_tag, fill=(255, 215, 0)) # Gold

    # 保存
    os.makedirs("output/media", exist_ok=True)
    filename = f"output/media/post_{platform}_{product_data.get('itemCode', 'temp')}.png"
    bg = bg.convert("RGB")
    bg.save(filename, quality=95)
    print(f"[Media Generator] 画像を保存しました: {filename}")
    return filename

def create_short_video(image_path: str, output_path: str = None) -> str:
    """静止画から5秒間の動画を生成する"""
    if not image_path or not os.path.exists(image_path):
        return ""
    if not output_path:
        output_path = image_path.replace(".png", ".mp4")
    
    print(f"[Media Generator] 動画を生成中: {output_path}")
    try:
        clip = ImageClip(image_path, duration=5)
        # 背景音楽がない場合は無音、またはBGMを追加可能
        clip.write_videofile(output_path, fps=24, codec="libx264", logger=None)
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
