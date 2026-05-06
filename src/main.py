import sys
import time
from src.research import search_products
from src.ai_generator import generate_room_post_content
from src.auto_poster import auto_post_pipeline

def run_automation(keyword: str = "ふるさと納税", hits: int = 3):
    print("========================================")
    print("楽天ROOM 自動化プロセスを開始します")
    print("========================================")
    
    # 1. 商品リサーチ
    print("\n【ステップ1】商品リサーチ")
    try:
        products = search_products(keyword=keyword, hits=hits)
        if not products:
            print("対象商品が見つかりませんでした。処理を終了します。")
            return
    except Exception as e:
        print(f"リサーチ処理でエラーが発生しました: {e}")
        return

    # 2 & 3. 順次処理 (AI生成 -> 自動投稿)
    for i, product in enumerate(products):
        print(f"\n--- 商品 {i+1}/{len(products)} ---")
        print(f"対象: {product['title'][:30]}...")
        
        try:
            # 2. AIによるテキスト生成
            print("【ステップ2】AI紹介文生成")
            comment = generate_room_post_content(product)
            print(f"生成されたコメント:\n{comment}\n")
            
            # 3. 自動投稿 (Playwright)
            print("【ステップ3】楽天ROOMへ自動投稿")
            # 実際のブラウザ操作を呼び出す
            auto_post_pipeline(product, comment)
            
            # 投稿間隔を空ける (BAN対策)
            if i < len(products) - 1:
                wait_time = 15
                print(f"{wait_time}秒待機します...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"商品 {i+1} の処理中にエラーが発生しました: {e}")
            continue

    print("\n========================================")
    print("すべての処理が完了しました")
    print("========================================")

if __name__ == "__main__":
    # コマンド引数からキーワードを取得（オプション）
    target_keyword = "母の日 ギフト"
    if len(sys.argv) > 1:
        target_keyword = sys.argv[1]
        
    run_automation(keyword=target_keyword, hits=2)
