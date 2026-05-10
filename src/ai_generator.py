import os
import google.generativeai as genai
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 推奨モデル (高速かつ安価なflashモデル、またはproモデル)
MODEL_NAME = "3.1-flash-lite"

def generate_room_post_content(product_data: Dict) -> str:
    """
    商品の情報をもとに、楽天ROOM向けの魅力的な紹介文（ハッシュタグ含む）を生成します。
    
    Args:
        product_data (Dict): research.py で取得した商品データの辞書
        
    Returns:
        str: 楽天ROOM用の紹介文
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEYが.envに設定されていません。")

    title = product_data.get("title", "")
    price = product_data.get("price", 0)
    description = product_data.get("description", "")
    
    prompt = f"""
あなたは優秀な楽天ROOMインフルエンサーです。
以下の商品情報をもとに、ユーザーが思わずクリックしたくなるような、魅力的な紹介文を作成してください。

【商品情報】
商品名: {title}
価格: {price}円
商品説明: {description[:500]}...

【作成ルール】
- 絵文字を適度に使って親しみやすくする
- ターゲット層（例：主婦、ガジェット好き、美容好きなど）に刺さる言葉選びをする
- 短すぎず長すぎない適度な長さ（200文字〜400文字程度）
- 最後に、検索されやすいハッシュタグを3〜5個つける（例: #楽天スーパーSALE #買ってよかった #お買い物マラソン ）
- 「ROOMで詳しく見る」といった誘導は不要（投稿画面の仕様上おかしくなるため）

それでは紹介文を作成してください。
"""

    print(f"[AI Generator] 商品『{title[:15]}...』の紹介文をGeminiで生成中...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        content = response.text.strip()
        print("[AI Generator] 生成完了。")
        return content
    except Exception as e:
        print(f"[AI Generator] AI生成エラーが発生しました: {e}")
        return f"おすすめの商品です！ #おすすめ #楽天ROOM\n\n{title}"

def generate_sns_content(product_data: Dict, platform: str) -> str:
    """
    SNS（XまたはInstagram）向けの投稿文を生成します。
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEYが.envに設定されていません。")

    title = product_data.get("title", "")
    price = product_data.get("price", 0)
    description = product_data.get("description", "")
    
    if platform.lower() == "x":
        prompt = f"""
あなたは楽天アフィリエイトで月100万稼ぐ凄腕のX（Twitter）インフルエンサーです。
以下の商品を紹介する、拡散されやすくクリック率の高いポストを作成してください。

【商品情報】
商品名: {title}
価格: {price}円
商品説明: {description[:300]}...

【作成ルール】
- 140文字以内（必須）
- 冒頭でベネフィットを強調して惹きつける
- 絵文字を1〜2個使い、視認性を高める
- 最後に、トレンドに合わせたハッシュタグを2個つける
- URLを入れる場所を [URL] と記載してください
"""
    elif platform.lower() == "instagram":
        prompt = f"""
あなたはInstagramで大人気のライフスタイル系インスタグラマーです。
以下の商品を紹介する、おしゃれで親しみやすいキャプションを作成してください。

【商品情報】
商品名: {title}
価格: {price}円
商品説明: {description[:300]}...

【作成ルール】
- ユーザーに語りかけるような丁寧な言葉遣い
- 商品の「使い心地」や「生活がどう変わるか」を想像させる内容
- 適度に改行を入れ、読みやすくする
- 最後に、関連性の高いハッシュタグを10個程度つける
"""
    else:
        return generate_room_post_content(product_data)

    print(f"[AI Generator] {platform}向けコンテンツを生成中...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        content = response.text.strip()
        print(f"[AI Generator] {platform}向け生成完了。")
        return content
    except Exception as e:
        print(f"[AI Generator] AI生成エラーが発生しました: {e}")
        return f"おすすめの商品です！\n{title}"

if __name__ == "__main__":
    # テスト実行用
    dummy_data = {
        "title": "【送料無料】無洗米 山形県産 つや姫 10kg(5kg×2袋) 令和5年産",
        "price": 5500,
        "description": "特Aランクのお米。甘みと旨みが特徴のつや姫。無洗米なので洗う手間が省けます。"
    }
    
    print("--- 楽天ROOM ---")
    print(generate_room_post_content(dummy_data))
    
    print("\n--- X (Twitter) ---")
    print(generate_sns_content(dummy_data, "x"))
    
    print("\n--- Instagram ---")
    print(generate_sns_content(dummy_data, "instagram"))
