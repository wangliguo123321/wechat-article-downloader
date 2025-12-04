import streamlit as st
import os
from wechat_scraper import WeChatScraper
from auth_helper import login_and_get_tokens
import time

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
    3.  **格式**: 默认下载 HTML，可勾选 **PDF** 或 **Word**。
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
    if 'cookie' not in st.session_state: st.session_state['cookie'] = ''
    if 'token' not in st.session_state: st.session_state['token'] = ''
    # Hardcode base_dir to system Downloads folder
    st.session_state['base_dir'] = os.path.join(os.path.expanduser("~"), "Downloads")
    base_dir = st.session_state['base_dir']

    # --- 1. Login Section ---
    if st.session_state['cookie'] and st.session_state['token']:
        # Logged In State
        st.success("✅ 已登录 | 凭证有效")
        if st.button("🔄 切换账号 / 重新登录"):
            st.session_state['cookie'] = ''
            st.session_state['token'] = ''
            st.rerun()
    else:
        # Not Logged In State
        if st.button("🚀 扫码登录", type="primary"):
            with st.spinner("正在启动安全浏览器..."):
                cookie, token, error_msg = login_and_get_tokens()
                if cookie and token:
                    st.session_state['cookie'] = cookie
                    st.session_state['token'] = token
                    st.rerun()
                else:
                    st.error(f"登录失败: {error_msg}")

    st.markdown("---")

    # --- 2. Configuration Section ---
    st.subheader("⚙️ 下载配置")

    # Single column for account name
    account_name = st.text_input("公众号名称", value="", placeholder="请输入公众号名称 (例如: 薪火传)")

    # Formats
    st.caption("选择导出格式:")
    f1, f2, f3 = st.columns(3)
    with f1: fmt_html = st.checkbox("HTML (网页)", value=True, disabled=True)
    with f2: fmt_pdf = st.checkbox("PDF (打印版)", value=False, help="推荐！完美还原网页排版")
    with f3: fmt_docx = st.checkbox("Word (纯文本)", value=False, help="仅提取文字，适合编辑")

    formats = ['html']
    if fmt_pdf: formats.append('pdf')
    if fmt_docx: formats.append('docx')

    st.markdown("<br>", unsafe_allow_html=True)

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
                articles = scraper.get_articles(fakeid, update_log)
                
                total = len(articles)
                if total == 0:
                    st.warning("⚠️ 未找到任何文章。")
                else:
                    status_text.success(f"✅ 找到 {total} 篇，开始下载...")
                    
                    # 3. Download
                    downloaded_count = 0
                    skipped_count = 0
                    
                    for i, article in enumerate(articles):
                        status_text.text(f"正在处理 {i+1}/{total}: {article['title']}")
                        progress_bar.progress((i + 1) / total)
                        
                        success = scraper.save_article_content(article, target_dir, formats, update_log)
                        if success:
                            downloaded_count += 1
                        else:
                            skipped_count += 1
                        
                        time.sleep(1) 
                    
                    st.balloons()
                    status_text.success(f"🎉 任务完成！下载: {downloaded_count}, 跳过: {skipped_count}")
                    st.info(f"📂 文件已保存至: {target_dir}")
                    
                    # Cleanup
                    scraper.close_driver()
                    
            else:
                st.error("❌ 未找到公众号，请检查名称或凭证。")

with brand_col:
    # --- Branding (Right Column) ---
    st.caption("欢迎和开发者公众号交流：薪火传")
    if os.path.exists("assets/qr_account_new.jpg"):
        st.image("assets/qr_account_new.jpg", use_column_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.caption("赞赏支持")
    if os.path.exists("assets/qr_pay.jpg"):
        st.image("assets/qr_pay.jpg", use_column_width=True)
