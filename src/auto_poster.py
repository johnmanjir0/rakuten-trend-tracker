import os
import time
from typing import Dict
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, expect

load_dotenv()

RAKUTEN_LOGIN_ID = os.getenv("RAKUTEN_LOGIN_ID")
RAKUTEN_PASSWORD = os.getenv("RAKUTEN_PASSWORD")

def login_to_rakuten(page: Page):
    """楽天にログインする"""
    if not RAKUTEN_LOGIN_ID or not RAKUTEN_PASSWORD:
        raise ValueError("ログイン情報が.envに設定されていません。")

    # ここでの事前ログインは廃止し、ROOM遷移後にログインを求められた場合に対応します。
    pass

def post_to_room(page: Page, product_url: str, comment: str):
    """
    指定した商品のURLにアクセスし、楽天ROOMに投稿する
    """
    print(f"[Auto Poster] 商品ページへ移動します: {product_url}")
    page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
    
    # 「ROOMに投稿する」ボタンを探す
    print("[Auto Poster] ROOM投稿ボタンを探しています...")
    try:
        # 楽天の仕様変更により href="room.rakuten.co.jp/mix" になっています
        page.wait_for_selector('a[href*="room.rakuten.co.jp/mix"]', timeout=15000)
        room_button = page.locator('a[href*="room.rakuten.co.jp/mix"]').first
            
        if room_button.is_visible():
            room_href = room_button.get_attribute("href")
            print(f"[Auto Poster] ROOM投稿リンクを取得しました。移動します...")
            
            # 新しいタブが開くかどうかの挙動を回避するため、直接hrefのURLへ移動する
            if not room_href.startswith("http"):
                room_href = "https://room.rakuten.co.jp" + room_href
                
            page.goto(room_href, wait_until="domcontentloaded", timeout=60000)
            
            # ROOM投稿画面か、ログイン画面のどちらかに飛ぶため判定
            time.sleep(3)
            current_url = page.url
            if "login.account.rakuten.com" in current_url or "id.rakuten.co.jp" in current_url or page.locator("input#user_id, input[name='u']").is_visible():
                print("[Auto Poster] ログインを求められました。ユーザー情報を入力します...")
                
                # ユーザーIDの入力
                page.wait_for_selector("input#user_id, input[name='username'], input[name='u']", timeout=10000)
                page.fill("input#user_id, input[name='username'], input[name='u']", RAKUTEN_LOGIN_ID)
                
                # 「次へ」ボタンがある場合はクリックしてパスワード画面へ進む（新デザイン対応）
                next_button = page.locator("button:has-text('次へ'), input[value='次へ'], text=次へ").first
                if next_button.is_visible():
                    next_button.click()
                    page.wait_for_timeout(2000)
                    
                # パスワードの入力
                page.wait_for_selector("input[type='password'], input[name='password'], input[name='p']", timeout=10000)
                page.fill("input[type='password'], input[name='password'], input[name='p']", RAKUTEN_PASSWORD)
                
                # 「ログイン」ボタンをクリック
                login_button = page.locator("button:has-text('ログイン'), input[value='ログイン'], input[type='submit']").first
                login_button.click()
                
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(3)
                
            print("[Auto Poster] ROOMの投稿画面を待機しています...")
            
            # コメント入力欄を探す (textarea)
            page.wait_for_selector("textarea", timeout=20000)
            textarea = page.locator("textarea").first
            textarea.fill(comment)
            
            # 「完了」または「投稿」ボタンを探してクリック
            submit_button = page.locator("button:has-text('完了'), button:has-text('投稿'), text=完了, text=投稿").first
            # submit_button.click() # ★安全のため初回はコメントアウトし、手動確認を推奨します。
            
            print("[Auto Poster] 投稿情報を入力しました。(※テストのため実際の投稿クリックは保留中)")
            time.sleep(3)
        else:
            print("[Auto Poster] ページ内にROOM投稿ボタンが見つかりませんでした。")
            page.screenshot(path="debug_no_room_button.png")
            
    except Exception as e:
        print(f"[Auto Poster] 投稿処理中にエラーが発生しました: {e}")
        page.screenshot(path="debug_error.png")

def auto_post_pipeline(product_data: Dict, comment: str):
    """
    ブラウザを立ち上げて一連の処理を行うエントリーポイント
    """
    print("[Auto Poster] Playwrightを起動します...")
    with sync_playwright() as p:
        # headless=False にすると実際のブラウザの動きを目視できます
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            # ログイン状態を保持する場合は storage_state="auth.json" などを活用します
        )
        page = context.new_page()
        
        try:
            login_to_rakuten(page)
            # 商品URLがある場合のみ投稿処理
            product_url = product_data.get("url")
            if product_url:
                post_to_room(page, product_url, comment)
            else:
                print("[Auto Poster] 商品URLがないため投稿をスキップします。")
                
        finally:
            print("[Auto Poster] ブラウザを終了します。")
            browser.close()

if __name__ == "__main__":
    # テスト実行用
    dummy_data = {
        "url": "https://item.rakuten.co.jp/rakuten24/4901301366115/" # 例: メリーズおむつ
    }
    dummy_comment = "テスト投稿です！ #楽天ROOMテスト"
    auto_post_pipeline(dummy_data, dummy_comment)
