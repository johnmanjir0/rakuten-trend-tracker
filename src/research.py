import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")
SEARCH_API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"

def search_products(keyword: str = "", genre_id: str = "", hits: int = 5, sort: str = "standard") -> List[Dict]:
    """
    楽天商品検索APIを使用して商品情報を取得します。
    
    Args:
        keyword (str): 検索キーワード
        genre_id (str): ジャンルID
        hits (int): 取得件数 (1-30)
        sort (str): ソート順 (例: 'standard', '+itemPrice', '-itemPrice', '+updateTimestamp')
        
    Returns:
        List[Dict]: 商品データのリスト
    """
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise ValueError("RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が.envに設定されていません。")

    params = {
        "applicationId": RAKUTEN_APP_ID,
        "accessKey": RAKUTEN_ACCESS_KEY,
        "format": "json",
        "hits": hits,
        "sort": sort,
    }
    
    if keyword:
        params["keyword"] = keyword
    if genre_id:
        params["genreId"] = genre_id
    if RAKUTEN_AFFILIATE_ID:
        params["affiliateId"] = RAKUTEN_AFFILIATE_ID

    print(f"[Research] 楽天APIで商品を検索中... (キーワード: '{keyword}', ジャンル: '{genre_id}')")
    
    headers = {
        "Referer": "https://rakuten.co.jp/",
        "Origin": "https://rakuten.co.jp/"
    }

    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        items = []
        if "Items" in data:
            for item in data["Items"]:
                item_data = item["Item"]
                items.append({
                    "title": item_data.get("itemName", ""),
                    "price": item_data.get("itemPrice", 0),
                    "url": item_data.get("affiliateUrl", item_data.get("itemUrl", "")),
                    "image_url": item_data.get("mediumImageUrls", [{"imageUrl": ""}])[0]["imageUrl"],
                    "description": item_data.get("itemCaption", ""),
                    "shop_name": item_data.get("shopName", ""),
                    "review_average": item_data.get("reviewAverage", 0),
                    "review_count": item_data.get("reviewCount", 0),
                })
        print(f"[Research] {len(items)}件の商品が見つかりました。")
        return items

    except Exception as e:
        print(f"[Research] APIエラーが発生しました: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"[Research] 詳細エラー: {response.text}")
        return []

if __name__ == "__main__":
    # テスト実行用
    # .envにAPP_IDを設定してから実行してください
    results = search_products(keyword="ふるさと納税", hits=2)
    for r in results:
        print(f"- {r['title'][:30]}... ({r['price']}円)")
