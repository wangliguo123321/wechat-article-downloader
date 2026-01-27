import streamlit as st
import os
import base64
from wechat_scraper import WeChatScraper
from auth_helper import init_login_driver, get_login_qr, check_login_status, save_credentials, load_credentials, clear_credentials
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil

st.set_page_config(page_title="微信公众号文章下载工具", page_icon="⚡", layout="wide")

# --- Tech Theme CSS (Apple Style + White Text) ---
st.markdown("""
<style>
    /* Apple-Style Dark Theme - All White Text */
    .stApp {
        background-color: #000000; /* Pure Black */
        color: #ffffff; /* Pure White */
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p, label, .stCaption {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #ffffff !important; /* Force White */
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 980px; /* Pill shape */
        background-color: #0071e3; /* Apple Blue */
        color: white !important;
        font-weight: 500;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0077ed; /* Lighter Blue */
        transform: scale(1.02);
    }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #000000; /* Match main background */
        border-right: 1px solid #333;
    }
    
    /* Top Header (Remove white bar) */
    header[data-testid="stHeader"] {
        background-color: #000000;
    }
    
    /* Cards/Containers */
    .css-1r6slb0, .stExpander {
        background-color: #1c1c1e;
        border: none;
        border-radius: 12px;
        color: #ffffff;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #1c1c1e;
        color: #ffffff;
        border: 1px solid #3a3a3c;
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #0071e3;
        box-shadow: 0 0 0 1px #0071e3;
    }
    /* Placeholder Text Color */
    .stTextInput>div>div>input::placeholder {
        color: #ffffff !important;
        opacity: 0.7;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #30d158; /* Apple Green */
    }
    
    /* Branding Area */
    .branding-card {
        background-color: #1c1c1e;
        border-radius: 18px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .branding-title {
        color: #ffffff !important;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    /* Tooltip Customization (Pornhub Style) */
    div[data-baseweb="tooltip"] > div:last-child {
        background-color: #ff9900 !important; /* Pornhub Yellow */
        color: #000000 !important; /* Black Text */
        border-radius: 6px;
        padding: 8px 12px;
        font-weight: 500;
        font-size: 0.9rem;
    }
    /* Hide the arrow to prevent double-box effect or style mismatch */
    div[data-baseweb="tooltip"] > div:first-child {
        display: none; 
    }
    /* Sidebar Text Size */
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stMarkdown li {
        font-size: 0.85rem !important; /* Smaller font to match caption */
    }
    [data-testid="stSidebar"] h3 {
        font-size: 1.0rem !important;
    }
    
    /* Reduce Sidebar Top Padding */
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
    
    /* Sticky Title */
    .main .block-container h1 {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #000000; /* Match background */
        padding-top: 1rem;
        padding-bottom: 1rem;
        margin-top: 0;
        border-bottom: 1px solid #333;
        width: 100%;
    }
    
    /* Override "Running..." Status Text */
    /* Hide the original text */
    [data-testid="stStatusWidget"] label {
        font-size: 0 !important;
    }
    /* Insert new text */
    [data-testid="stStatusWidget"] label::after {
        content: "运行中...";
        font-size: 0.875rem !important;
        visibility: visible;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: User Guide ---
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    ### 🚀 快速开始
    1.  **登录**: 点击主界面的 **“扫码登录”** 按钮，在弹出的浏览器中扫码。
    2.  **配置**: 输入 **公众号名称** (如 "薪火传")。
    3.  **格式**: 默认下载 **Word（图文）**，可勾选 **PDF**。
    4.  **启动**: 点击 **“开始下载”**，程序将自动抓取并保存至 **下载** 文件夹。
    
    ### ⚠️ 注意事项
    *   **频率限制**: 如果出现黄色警告，说明触发了微信的频率控制，程序会自动暂停 60 秒。解决方案可以更换微信号扫码登录重新下载。
    """)

# --- Main Layout ---
main_col, brand_col = st.columns([3, 1])

with main_col:
    # --- Header ---
    st.title("⚡ 微信公众号文章下载工具")
    st.markdown("---")

    # Session State Initialization
    if 'cookie' not in st.session_state: 
        # Try loading from cache
        c, t = load_credentials()
        if c and t:
            st.session_state['cookie'] = c
            st.session_state['token'] = t
            st.toast("✅ 已自动登录")
        else:
            st.session_state['cookie'] = ''
            st.session_state['token'] = ''
            
    if 'token' not in st.session_state: st.session_state['token'] = ''
    
    # Use temporary directory for downloads in serverless environment
    if 'base_dir' not in st.session_state:
        st.session_state['temp_dir_obj'] = tempfile.TemporaryDirectory()
        st.session_state['base_dir'] = st.session_state['temp_dir_obj'].name
    
    base_dir = st.session_state['base_dir']

    # --- 1. Login Section ---
    if st.session_state['cookie'] and st.session_state['token']:
        # Logged In State
        st.success("✅ 已登录 | 凭证有效")
        if st.button("🔄 切换账号 / 退出登录"):
            clear_credentials()
            st.session_state['cookie'] = ''
            st.session_state['token'] = ''
            st.rerun()
    else:
        # Not Logged In State
        if 'login_driver' not in st.session_state: st.session_state['login_driver'] = None
        
        if not st.session_state['login_driver']:
            if st.button("🚀 扫码登录", type="primary"):
                with st.spinner("正在启动安全浏览器..."):
                    driver, err = init_login_driver()
                    if driver:
                        st.session_state['login_driver'] = driver
                        st.rerun()
                    else:
                        st.error(f"启动失败: {err}")
        else:
            # Driver is active, show QR Code and Poll
            st.info("⚠️ 请使用微信扫描下方二维码登录 (请勿关闭此页面)")
            
            col_qr, col_info = st.columns([1, 2])
            
            with col_qr:
                # Get QR Code
                if 'qr_img' not in st.session_state:
                     qr_b64, err = get_login_qr(st.session_state['login_driver'])
                     if qr_b64:
                         st.session_state['qr_img'] = qr_b64
                     else:
                         st.error(f"获取二维码失败: {err}")
                
                if 'qr_img' in st.session_state:
                    st.image(base64.b64decode(st.session_state['qr_img']), caption="请用微信扫码", width=200)

            with col_info:
                st.write("### 正在等待登录...")
                st.caption("扫码后请在手机上确认，程序会自动检测跳转。")
                
                # Polling mechanism using rerun
                status_placeholder = st.empty()
                status_placeholder.text(f"⏳ 正在检测登录状态 ({int(time.time()) % 60}s)...")
                
                success, cookie, token = check_login_status(st.session_state['login_driver'])
                
                if success:
                    st.success("✅ 登录成功！正在跳转...")
                    save_credentials(cookie, token)
                    st.session_state['cookie'] = cookie
                    st.session_state['token'] = token
                    
                    # Cleanup
                    st.session_state['login_driver'].quit()
                    st.session_state['login_driver'] = None
                    if 'qr_img' in st.session_state: del st.session_state['qr_img']
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    time.sleep(2)  # Wait 2 seconds before rerunning to poll again
                    st.rerun()
            
            # Cancel Button
            if st.button("取消登录"):
                st.session_state['login_driver'].quit()
                st.session_state['login_driver'] = None
                if 'qr_img' in st.session_state: del st.session_state['qr_img']
                st.rerun()

    st.markdown("---")

    # --- 2. Configuration Section ---
    st.subheader("⚙️ 下载配置")

    # Single column for account name
    account_name = st.text_input("公众号名称", value="", placeholder="请输入公众号名称 (例如: 薪火传)")

    # Formats
    st.caption("选择导出格式:")
    f1, f2 = st.columns(2)
    with f1: fmt_docx = st.checkbox("Word（图文）", value=True, help="推荐！包含文字和图片")
    with f2: fmt_pdf = st.checkbox("PDF (打印版)", value=False, help="完美还原网页排版")

    formats = []
    if fmt_docx: formats.append('docx')
    if fmt_pdf: formats.append('pdf')

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Date Range Selection
    st.caption("选择时间范围:")
    date_option = st.radio(
        "时间范围",
        ("最近一周", "最近一个月", "最近三个月", "历史全部"),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    today = datetime.date.today()
    date_range = None
    
    if date_option == "最近一周":
        start_date = today - datetime.timedelta(days=7)
        date_range = (start_date, today)
    elif date_option == "最近一个月":
        start_date = today - datetime.timedelta(days=30)
        date_range = (start_date, today)
    elif date_option == "最近三个月":
        start_date = today - datetime.timedelta(days=90)
        date_range = (start_date, today)
    else:
        date_range = None # All history

    # --- 3. Action & Output ---
    if st.button("⚡ 开始下载", type="primary"):
        if not st.session_state['cookie'] or not st.session_state['token']:
            st.error("❌ 请先登录！")
        elif not account_name:
            st.error("❌ 请输入公众号名称！")
        else:
            # Create target directory
            target_dir = os.path.join(base_dir, account_name)
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir)
                except Exception as e:
                    st.error(f"❌ 无法创建文件夹: {e}")
                    st.stop()
            
            # Initialize Scraper
            scraper = WeChatScraper(st.session_state['cookie'], st.session_state['token'])
            
            # Progress Container
            status_container = st.container()
            with status_container:
                status_text = st.empty()
                progress_bar = st.progress(0)
                log_container = st.empty()
            
            logs = []
            def update_log(msg):
                # Translate common logs
                if "Searching for" in msg: msg = f"🔍 正在搜索: {account_name}..."
                if "Found Account" in msg: msg = "✅ 找到公众号！"
                if "Fetching page" in msg: msg = f"📄 获取列表 (第 {msg.split(' ')[2]} 页)..."
                if "Downloaded:" in msg: msg = f"⬇️ 下载成功: {msg.split(': ')[1]}"
                if "Skip" in msg: msg = f"⏭️ 跳过: {msg.split(': ')[1]}"
                if "Rate limit detected" in msg: msg = "⚠️ 触发频率限制，暂停 60 秒..."
                if "Rate limit persists" in msg: msg = "❌ 限制未解除，请休息 1-24 小时后再试。"
                
                logs.append(msg)
                log_text = "\n".join(logs[-6:])
                log_container.code(log_text, language="bash")
            
            # 1. Get FakeID
            status_text.info("正在搜索公众号...")
            fakeid = scraper.get_fakeid(account_name, update_log)
            
            if fakeid:
                # 2. Get Articles
                status_text.info("正在获取文章列表...")
                
                # Handle date range input
                search_date_range = None
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    search_date_range = date_range
                
                articles = scraper.get_articles(fakeid, update_log, date_range=search_date_range)
                
                total = len(articles)
                if total == 0:
                    st.warning("⚠️ 未找到任何文章。")
                else:
                    status_text.success(f"✅ 找到 {total} 篇，开始下载...")
                    
                    # 3. Download (Multi-threaded)
                    downloaded_count = 0
                    skipped_count = 0
                    
                    # Define a wrapper function for the executor
                    def download_task(article):
                        # Pass None as callback to avoid threading issues with Streamlit
                        return scraper.save_article_content(article, target_dir, formats, callback=None)
                    
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        # Submit all tasks
                        future_to_article = {executor.submit(download_task, article): article for article in articles}
                        
                        for i, future in enumerate(as_completed(future_to_article)):
                            article = future_to_article[future]
                            try:
                                success = future.result()
                                if success:
                                    downloaded_count += 1
                                    update_log(f"⬇️ 下载成功: {article['title']}")
                                else:
                                    skipped_count += 1
                                    update_log(f"⏭️ 跳过/失败: {article['title']}")
                            except Exception as exc:
                                update_log(f"⚠️ 下载出错 {article['title']}: {exc}")
                                skipped_count += 1
                                
                            # Update progress
                            status_text.text(f"正在处理 {i+1}/{total}: {article['title']}")
                            progress_bar.progress((i + 1) / total) 
                    
                    st.balloons()
                    status_text.success(f"🎉 任务完成！下载: {downloaded_count}, 跳过: {skipped_count}")
                    
                    # Create ZIP file
                    shutil.make_archive(os.path.join(base_dir, "articles"), 'zip', target_dir)
                    zip_path = os.path.join(base_dir, "articles.zip")
                    
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📦 打包下载所有文章 (ZIP)",
                            data=f,
                            file_name=f"{account_name}_articles.zip",
                            mime="application/zip",
                            type="primary"
                        )
                    
                    st.info(f"📂 文件临时保存于: {target_dir}")
                    
                    # Cleanup
                    scraper.close_driver()
                    
            else:
                st.error("❌ 未找到公众号，请检查名称或凭证。")

with brand_col:
    # --- Branding (Right Column) ---
    st.caption("欢迎和开发者公众号交流：薪火传")
    if os.path.exists("assets/qr_account_new.jpg"):
        st.image("assets/qr_account_new.jpg", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.caption("赞赏支持")
    if os.path.exists("assets/qr_pay.jpg"):
        st.image("assets/qr_pay.jpg", use_container_width=True)
