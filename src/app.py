import streamlit as st
import pandas as pd
import os
import glob
from trend_tracker import search_trending_products, analyze_trend_with_ai, discover_trends_with_ai
from ai_generator import generate_sns_content, generate_video_scripts
from media_generator import create_premium_banner, create_short_video

# 設定
st.set_page_config(page_title="Rakuten Trend Tracker", page_icon="🛍️", layout="wide")

# カスタムCSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛍️ Rakuten Trend Dashboard")
st.markdown("楽天市場のトレンド商品を自動検索し、AIが「売れる理由」と「ハッシュタグ」を分析します。")

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 連携設定")
    enable_truereview = st.checkbox("TrueReview AIと連携する", value=True)
    truereview_url = st.text_input("レビューサイトURL", value="https://truereview-ai.vercel.app/beauty")
    st.info("💡 連携をONにすると、ROOM投稿用テキストの最後にレビューサイトへの案内リンクが自動で追加されます。")


# タブの作成
tab1, tab2, tab3 = st.tabs(["🔍 新規リサーチ実行", "📂 過去のレポート履歴", "📱 SNSオートメーション"])

with tab1:
    st.header("新しいトレンドを検索")
    
    st.subheader("🤖 AIおまかせ自動リサーチ")
    st.markdown("Gemini AIがWebの最新動向を解析し、自動でトレンドキーワードを選定してリサーチします！")
    
    col1, col2, col3, col4 = st.columns(4)
    
    auto_keywords = []
    if col1.button("🌸 季節の売れ筋", use_container_width=True):
        with st.spinner("AIが今月の季節キーワードを解析中..."):
            auto_keywords = discover_trends_with_ai("seasonal")
            if auto_keywords:
                st.success(f"選定キーワード: {', '.join(auto_keywords)}")
    
    if col2.button("💄 流行りのコスメ", use_container_width=True):
        with st.spinner("AIが最新のコスメトレンドを解析中..."):
            auto_keywords = discover_trends_with_ai("cosmetics")
            if auto_keywords:
                st.success(f"選定キーワード: {', '.join(auto_keywords)}")
                
    if col3.button("🧽 役立つ日用品", use_container_width=True):
        with st.spinner("AIが話題の便利グッズを解析中..."):
            auto_keywords = discover_trends_with_ai("daily_goods")
            if auto_keywords:
                st.success(f"選定キーワード: {', '.join(auto_keywords)}")
                
    if col4.button("🌍 最新トレンド(独自解析)", use_container_width=True):
        with st.spinner("AIがGoogle検索と連動して最新の流行を解析中..."):
            auto_keywords = discover_trends_with_ai("global")
            if auto_keywords:
                st.success(f"選定キーワード: {', '.join(auto_keywords)}")
    
    st.divider()
    st.subheader("✏️ 手動でキーワードを指定してリサーチ")
    with st.form("research_form"):
        keyword_input = st.text_input("検索キーワードを入力してください (カンマ区切りで複数可)", "母の日 ギフト, 韓国コスメ")
        hits_count = st.slider("1キーワードあたりの取得件数", 1, 10, 5)
        submit_button = st.form_submit_button("🚀 入力したキーワードでリサーチ開始", type="primary")
        
    # リサーチ実行フラグ（自動または手動）
    should_run = False
    keywords_to_run = []
    
    if auto_keywords:
        should_run = True
        keywords_to_run = auto_keywords
        hits_count = 5 # 自動の場合は5件固定
        
    if submit_button:
        keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
        if not keywords:
            st.error("キーワードを入力してください。")
        else:
            should_run = True
            keywords_to_run = keywords

    if should_run:
        all_results = []
        
        # プログレスバー
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(keywords_to_run) * hits_count
        current_step = 0
        
        st.subheader("💡 分析結果")
        
        for keyword in keywords_to_run:
            st.markdown(f"### 🔎 キーワード: `{keyword}`")
            try:
                status_text.text(f"楽天APIから '{keyword}' の上位商品を取得中...")
                products = search_trending_products(keyword, hits=hits_count)
                
                if not products:
                    st.warning(f"'{keyword}' に該当する商品が見つかりませんでした。")
                    continue
                    
                for rank, product in enumerate(products, 1):
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
                    status_text.text(f"AIが {rank}位の商品 を分析中... ({product['itemName'][:20]}...)")
                    
                    # AI分析
                    analysis = analyze_trend_with_ai(
                        product['itemName'], 
                        product['itemPrice'], 
                        product['reviewCount'], 
                        product['reviewAverage']
                    )
                    
                    # サイト連携
                    if enable_truereview and truereview_url:
                        analysis += f"\n\n✨詳細なAI成分・口コミ解析はこちら👇\n{truereview_url}"

                    
                    # 保存用データ
                    all_results.append({
                        "Keyword": keyword,
                        "Rank": rank,
                        "Product Name": product['itemName'],
                        "Price (Yen)": product['itemPrice'],
                        "Review Count": product['reviewCount'],
                        "Review Average": product['reviewAverage'],
                        "AI Trend Analysis": analysis,
                        "Affiliate URL": product['itemUrl'],
                        "Image URL": product.get('imageUrl', '')
                    })
                    
                    # UI表示
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if product.get('imageUrl'):
                                st.image(product['imageUrl'], use_container_width=True)
                            else:
                                st.write("画像なし")
                            st.metric("ランキング", f"👑 {rank}位")
                        with col2:
                            st.markdown(f"**{product['itemName']}**")
                            st.write(f"💰 **価格:** ¥{product['itemPrice']:,} | ⭐ **レビュー:** {product['reviewAverage']} ({product['reviewCount']:,}件)")
                            
                            st.markdown("**🤖 ROOM投稿用テキスト（右上のボタンで1クリックコピー）:**")
                            st.code(analysis, language="text")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                st.link_button("🛒 楽天商品ページを開く (ここからROOMへ投稿)", product['itemUrl'], use_container_width=True)
                            with c2:
                                st.text_input("🔗 直接のアフィリエイトURL", value=product['itemUrl'], key=f"url_{keyword}_{rank}")
                        st.divider()
            except Exception as e:
                st.error(f"エラーが発生しました ({keyword}): {e}")
        
        status_text.text("すべての分析が完了しました！")
        progress_bar.progress(1.0)
        
        # CSV保存
        if all_results:
            import time
            os.makedirs("reports", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"reports/rakuten_trend_report_{timestamp}.csv"
            df = pd.DataFrame(all_results)
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            st.success(f"結果を保存しました！ `📂 過去のレポート履歴` タブからいつでも確認できます。")
            
            # CSVダウンロードボタン
            with open(output_file, "rb") as file:
                st.download_button(
                    label="📥 CSVをダウンロード",
                    data=file,
                    file_name=f"rakuten_trend_{timestamp}.csv",
                    mime="text/csv",
                )

with tab2:
    st.header("過去のレポート履歴")
    report_files = sorted(glob.glob("reports/*.csv"), reverse=True)
    
    if not report_files:
        st.info("過去のレポートはまだありません。")
    else:
        selected_report = st.selectbox("確認したいレポートを選択してください", report_files)
        
        if selected_report:
            df = pd.read_csv(selected_report)
            st.write(f"📊 **データ件数:** {len(df)}件")
            
            # データの簡易表示
            st.dataframe(
                df[["Keyword", "Rank", "Price (Yen)", "Review Count", "Product Name", "AI Trend Analysis"]],
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            st.subheader("🖼️ 画像付き詳細ビュー")
            
            for idx, row in df.iterrows():
                col1, col2 = st.columns([1, 4])
                with col1:
                    if pd.notna(row.get('Image URL')) and row['Image URL']:
                        st.image(row['Image URL'], use_container_width=True)
                    st.metric(f"【{row['Keyword']}】", f"👑 {row['Rank']}位")
                with col2:
                    st.markdown(f"**{row['Product Name']}**")
                    st.write(f"💰 **価格:** ¥{row['Price (Yen)']:,} | 📝 **レビュー:** {row['Review Count']:,}件")
                    st.markdown("**🤖 ROOM投稿用テキスト:**")
                    st.code(row['AI Trend Analysis'], language="text")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("🛒 楽天商品ページを開く (ここからROOMへ投稿)", row['Affiliate URL'], use_container_width=True)
                    with c2:
                        st.text_input("🔗 アフィリエイトURL", value=row['Affiliate URL'], key=f"hist_url_{idx}")
                st.divider()
with tab3:
    st.header("📱 SNS投稿用コンテンツ生成")
    st.markdown("トレンド商品をもとに、XやInstagramにそのまま投稿できる画像と文章を自動作成します。")
    
    report_files = sorted(glob.glob("reports/*.csv"), reverse=True)
    if not report_files:
        st.info("まずはリサーチを実行してレポートを作成してください。")
    else:
        selected_report_sns = st.selectbox("リサーチ結果を選択", report_files, key="sns_report_select")
        df_sns = pd.read_csv(selected_report_sns)
        
        selected_product_idx = st.selectbox(
            "対象の商品を選択してください", 
            range(len(df_sns)), 
            format_func=lambda x: f"{df_sns.iloc[x]['Product Name'][:50]}..."
        )
        
        product = df_sns.iloc[selected_product_idx]
        
        col_gen1, col_gen2 = st.columns(2)
        
        with col_gen1:
            st.subheader("🐦 X (Twitter) 用")
            if st.button("X用の投稿を生成", use_container_width=True):
                with st.spinner("AIが最新の商品ベネフィットを調査中..."):
                    product_data = {
                        "title": product["Product Name"],
                        "price": product["Price (Yen)"],
                        "description": product["AI Trend Analysis"],
                        "itemName": product["Product Name"],
                        "itemPrice": product["Price (Yen)"],
                        "imageUrl": product["Image URL"],
                        "itemCode": f"x_{selected_product_idx}"
                    }
                    # 1. AIによるスクリプト生成（ウェブ検索活用）
                    video_info = generate_video_scripts(product_data)
                    st.session_state[f"video_info_{selected_product_idx}"] = video_info
                    
                    # 2. テキスト生成
                    x_text = generate_sns_content(product_data, "x")
                    st.session_state[f"x_text_{selected_product_idx}"] = x_text
                    
                    # 3. 画像生成（スタジオ品質）
                    x_img_path = create_premium_banner(product_data, "x", info=video_info)
                    st.session_state[f"x_img_{selected_product_idx}"] = x_img_path

            if f"x_text_{selected_product_idx}" in st.session_state:
                st.code(st.session_state[f"x_text_{selected_product_idx}"], language="text")
                if f"x_img_{selected_product_idx}" in st.session_state:
                    st.image(st.session_state[f"x_img_{selected_product_idx}"], use_container_width=True)
                    with open(st.session_state[f"x_img_{selected_product_idx}"], "rb") as f:
                        st.download_button("📥 画像をダウンロード", f, file_name="x_post.png", mime="image/png", key=f"x_dl_img_{selected_product_idx}")
                
                if st.button("🎬 X用のプロ品質動画を生成", key=f"x_vid_btn_{selected_product_idx}"):
                    with st.spinner("AIテロップ付き動画を生成中..."):
                        # 商品データを再定義（NameError回避）
                        product_data_vid = {
                            "title": product["Product Name"],
                            "price": product["Price (Yen)"],
                            "itemName": product["Product Name"],
                            "itemPrice": product["Price (Yen)"],
                            "imageUrl": product["Image URL"]
                        }
                        info = st.session_state.get(f"video_info_{selected_product_idx}", {})
                        try:
                            vid_path = create_short_video(st.session_state.get(f"x_img_{selected_product_idx}"), product_data_vid, info)
                            if vid_path and os.path.exists(vid_path):
                                st.session_state[f"x_vid_{selected_product_idx}"] = vid_path
                                st.rerun()
                            else:
                                st.error("動画ファイルの作成に失敗しました。")
                        except Exception as e:
                            st.error(f"動画生成中にエラーが発生しました: {e}")
                
                if f"x_vid_{selected_product_idx}" in st.session_state:
                    st.video(st.session_state[f"x_vid_{selected_product_idx}"])
                    with open(st.session_state[f"x_vid_{selected_product_idx}"], "rb") as f:
                        st.download_button("📥 動画をダウンロード", f, file_name="x_post.mp4", mime="video/mp4", key=f"x_dl_vid_{selected_product_idx}")

        with col_gen2:
            st.subheader("📸 Instagram用")
            if st.button("Instagram用の投稿を生成", use_container_width=True):
                with st.spinner("AIが最新の商品ベネフィットを調査中..."):
                    product_data = {
                        "title": product["Product Name"],
                        "price": product["Price (Yen)"],
                        "description": product["AI Trend Analysis"],
                        "itemName": product["Product Name"],
                        "itemPrice": product["Price (Yen)"],
                        "imageUrl": product["Image URL"],
                        "itemCode": f"insta_{selected_product_idx}"
                    }
                    # 1. AIによるスクリプト生成
                    video_info = generate_video_scripts(product_data)
                    st.session_state[f"video_info_insta_{selected_product_idx}"] = video_info
                    
                    # 2. テキスト生成
                    insta_text = generate_sns_content(product_data, "instagram")
                    st.session_state[f"insta_text_{selected_product_idx}"] = insta_text
                    
                    # 3. 画像生成
                    insta_img_path = create_premium_banner(product_data, "instagram", info=video_info)
                    st.session_state[f"insta_img_{selected_product_idx}"] = insta_img_path

            if f"insta_text_{selected_product_idx}" in st.session_state:
                st.code(st.session_state[f"insta_text_{selected_product_idx}"], language="text")
                if f"insta_img_{selected_product_idx}" in st.session_state:
                    st.image(st.session_state[f"insta_img_{selected_product_idx}"], use_container_width=True)
                    with open(st.session_state[f"insta_img_{selected_product_idx}"], "rb") as f:
                        st.download_button("📥 画像をダウンロード", f, file_name="insta_post.png", mime="image/png", key=f"insta_dl_img_{selected_product_idx}")

                if st.button("🎬 Insta用のプロ品質動画を生成", key=f"insta_vid_btn_{selected_product_idx}"):
                    with st.spinner("AIテロップ付き動画を生成中..."):
                        # 商品データを再定義
                        product_data_vid = {
                            "title": product["Product Name"],
                            "price": product["Price (Yen)"],
                            "itemName": product["Product Name"],
                            "itemPrice": product["Price (Yen)"],
                            "imageUrl": product["Image URL"]
                        }
                        info = st.session_state.get(f"video_info_insta_{selected_product_idx}", {})
                        try:
                            vid_path = create_short_video(st.session_state.get(f"insta_img_{selected_product_idx}"), product_data_vid, info)
                            if vid_path and os.path.exists(vid_path):
                                st.session_state[f"insta_vid_{selected_product_idx}"] = vid_path
                                st.rerun()
                            else:
                                st.error("動画ファイルの作成に失敗しました。")
                        except Exception as e:
                            st.error(f"動画生成中にエラーが発生しました: {e}")
                
                if f"insta_vid_{selected_product_idx}" in st.session_state:
                    st.video(st.session_state[f"insta_vid_{selected_product_idx}"])
                    with open(st.session_state[f"insta_vid_{selected_product_idx}"], "rb") as f:
                        st.download_button("📥 動画をダウンロード", f, file_name="insta_post.mp4", mime="video/mp4", key=f"insta_dl_vid_{selected_product_idx}")
