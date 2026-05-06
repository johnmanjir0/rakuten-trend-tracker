import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# 新しいGemini SDK
from google import genai
from google.genai import types

load_dotenv()

# 設定情報
SEARCH_API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"

def search_trending_products(keyword: str, hits: int = 10) -> list:
    """楽天APIを利用して、指定キーワードでレビュー数の多い（売れている）商品を取得する"""
    print(f"[Trend Tracker] 楽天で '{keyword}' のトレンド商品を検索中... (レビュー数順)")
    
    app_id = os.getenv("RAKUTEN_APP_ID")
    access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    
    if not app_id or not access_key:
        raise ValueError("RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が設定されていません。StreamlitのSecrets設定を確認してください。")

    params = {
        "applicationId": app_id,
        "accessKey": access_key,
        "keyword": keyword,
        "format": "json",
        "hits": hits,
        "sort": "-reviewCount"  # レビュー数が多い順（売れ筋の証拠）
    }
    
    headers = {
        "Referer": "https://rakuten.co.jp/",
        "Origin": "https://rakuten.co.jp/"
    }

    response = requests.get(SEARCH_API_URL, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    products = []
    for item in data.get("Items", []):
        i = item["Item"]
        
        # 画像URLの取得
        image_urls = i.get('mediumImageUrls', [])
        image_url = image_urls[0]['imageUrl'] if image_urls else None
        
        # アフィリエイトURLの生成（IDがある場合）
        item_url = i.get('itemUrl')
        affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
        if affiliate_id:
            item_url = f"https://hb.afl.rakuten.co.jp/hgc/{affiliate_id}/?pc={item_url}"
            
        products.append({
            "itemName": i.get('itemName'),
            "itemPrice": i.get('itemPrice'),
            "reviewCount": i.get('reviewCount'),
            "reviewAverage": i.get('reviewAverage'),
            "itemUrl": item_url,
            "imageUrl": image_url
        })
    return products

def discover_trends_with_ai(category: str) -> list:
    """GeminiとGoogle検索機能を利用して、カテゴリに応じたリアルタイムのトレンドキーワードを3つ抽出する"""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("[AI Error] GEMINI_API_KEYが設定されていません。")
        return []
        
    client = genai.Client(api_key=gemini_key)
    
    # カテゴリに応じたプロンプトの設定
    if category == "seasonal":
        prompt = "現在の季節や今月の行事・イベントを考慮して、今まさにEコマース（楽天市場など）で爆発的に売れている季節系商品のキーワードを3つ教えてください。"
    elif category == "cosmetics":
        prompt = "今、日本のSNSやWeb上で話題になっている最新のトレンドコスメや美容アイテムの具体的な商品キーワードを3つ教えてください。"
    elif category == "daily_goods":
        prompt = "現在、日本のSNSや主婦層の間で「生活が便利になる」「時短になる」と話題になっている最新の役立つ日用品や便利グッズの具体的な商品キーワードを3つ教えてください。"
    elif category == "global":
        prompt = "今現在、日本のWeb上やニュース、SNSで急激に話題になっている最新の流行・トレンドアイテム（ジャンル問わず、家電、ホビー、食品など）のキーワードを3つ教えてください。独自解析として最新のGoogle検索結果を反映させてください。"
    else:
        prompt = "今Eコマースで売れている商品のキーワードを3つ教えてください。"
        
    prompt += "\n※出力は必ず「キーワード1, キーワード2, キーワード3」のように、カンマ区切りのキーワードのみを返してください。それ以外の解説は一切不要です。"
    
    print(f"[Trend Tracker] AIが '{category}' のトレンドを独自解析中...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}] # Google検索を有効化（Search Grounding）
            )
        )
        
        # カンマ区切りのテキストをリストに変換
        text = response.text.strip()
        # 不要な記号などを取り除く
        keywords = [k.strip() for k in text.split(",") if k.strip()]
        return keywords[:3]
    except Exception as e:
        print(f"[AI Error] トレンド抽出に失敗しました: {e}")
        return []

def analyze_trend_with_ai(product_name: str, price: int, review_count: int, review_avg: float) -> str:
    """Geminiを使って商品がなぜ売れているのかを分析・解説する"""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return "AI分析スキップ（APIキー未設定）"
        
    client = genai.Client(api_key=gemini_key)
    
    prompt = f"""
あなたは凄腕のEコマースマーケターであり、アフィリエイターです。
以下の商品は、現在楽天市場で非常に多くのレビューを集めている大ヒット商品です。

【商品情報】
- 商品名: {product_name}
- 価格: {price}円
- レビュー数: {review_count}件
- レビュー平均: {review_avg}点 (5点満点)

この商品が「なぜこれほど売れているのか（トレンドの理由）」と「どのようなターゲットに刺さるのか」、
さらに「SNSで紹介する際におすすめのハッシュタグ（3〜5個）」を、合計200文字程度で簡潔に分析してください。
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[AI Error] {e}")
        return "分析エラー"

def generate_trend_report(keywords: list):
    """複数のキーワードでトレンド商品を検索し、レポートとしてCSV出力する"""
    print("========================================")
    print("楽天 Trend Tracker を開始します")
    print("========================================\n")
    
    all_results = []
    
    for keyword in keywords:
        try:
            products = search_trending_products(keyword=keyword, hits=5)
            for rank, product in enumerate(products, 1):
                print(f"[{keyword} - {rank}位] {product['itemName'][:30]}... ({product['reviewCount']}レビュー)")
                
                # AI分析
                analysis = analyze_trend_with_ai(
                    product['itemName'], 
                    product['itemPrice'], 
                    product['reviewCount'], 
                    product['reviewAverage']
                )
                
                all_results.append({
                    "Keyword": keyword,
                    "Rank": rank,
                    "Product Name": product['itemName'],
                    "Price (Yen)": product['itemPrice'],
                    "Review Count": product['reviewCount'],
                    "Review Average": product['reviewAverage'],
                    "AI Trend Analysis": analysis,
                    "Affiliate URL": product['itemUrl']
                })
                
                time.sleep(1) # API制限とAIレートリミット回避
                
        except Exception as e:
            print(f"キーワード '{keyword}' の検索中にエラーが発生しました: {e}")
            
    # レポートの保存
    if all_results:
        os.makedirs("reports", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"reports/rakuten_trend_report_{timestamp}.csv"
        
        df = pd.DataFrame(all_results)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        
        print("\n========================================")
        print(f"分析完了！レポートを保存しました: {output_file}")
        print("========================================")
        return df
    else:
        print("出力するデータがありませんでした。")
        return pd.DataFrame()

if __name__ == "__main__":
    # トレンドを調査したいキーワードのリスト
    target_keywords = ["母の日 ギフト", "韓国コスメ", "ダイエット 置き換え"]
    generate_trend_report(target_keywords)
