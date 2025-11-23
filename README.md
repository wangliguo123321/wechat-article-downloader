# ⚡ 微信公众号文章批量下载工具 (WeChat Article Downloader)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32.0-ff4b4b)

一个基于 Python 和 Streamlit 开发的微信公众号文章批量下载工具。支持自动扫码登录、多格式导出（HTML/PDF/Word）、断点续传和可视化界面。

## ✨ 功能亮点

*   **🚀 自动扫码登录**: 内置浏览器自动化，一键唤起微信登录，无需手动抓包 Cookie。
*   **🍎 极简 UI 设计**: 采用 Apple 风格的深色模式界面，纯黑背景 + 系统蓝配色。
*   **📂 智能下载管理**:
    *   自动按公众号名称创建文件夹。
    *   支持断点续传，自动跳过已下载文章。
    *   默认保存至系统 **下载 (Downloads)** 文件夹。
*   **📝 多格式导出**:
    *   **HTML**: 包含完整图片和样式的网页原文。
    *   **PDF**: 完美还原网页排版（基于 Chrome 打印技术）。
    *   **Word**: 纯文本提取，适合后续编辑。
*   **🛡️ 稳定防封**: 内置频率控制，触发微信限制时自动暂停保护账号。

## 🛠️ 安装与使用

### 1. 环境准备
确保您的电脑已安装 [Python 3.8+](https://www.python.org/downloads/) 和 [Google Chrome](https://www.google.com/chrome/) 浏览器。

### 2. 下载源码
```bash
git clone https://github.com/wangliguo123321/wechat-article-downloader.git
```

### 3. 安装依赖
```bash
cd wechat-article-downloader
pip install -r requirements.txt
```

### 4. 运行程序
```bash
streamlit run app.py
```
或者直接运行启动脚本（Mac/Linux）：
```bash
bash setup_and_run.sh
```

### 5. 开始使用
1.  程序会自动在浏览器中打开 (默认地址 `http://localhost:8501`)。
2.  点击 **“扫码登录”**，在弹出的 Chrome 窗口中扫码登录微信公众号平台。
3.  输入 **公众号名称** (例如 "薪火传")。
4.  选择需要的导出格式 (HTML/PDF/Word)。
5.  点击 **“⚡ 开始下载”**。
![](https://img2024.cnblogs.com/blog/1364007/202511/1364007-20251124011536886-823478726.png)
![](https://img2024.cnblogs.com/blog/1364007/202511/1364007-20251124011610373-1405586996.png)

## ⚠️ 注意事项

*   **账号要求**: 需要有微信公众号平台的登录权限（个人订阅号即可）。
*   **频率限制**: 微信接口有频率限制，如果程序提示“触发频率限制”，请耐心等待 60 秒或更换其他账号。

## 🤝 贡献与支持

欢迎提交 Issue 或 Pull Request 来改进这个项目！
*   **公众号**: 薪火传
![](https://img2024.cnblogs.com/blog/1364007/202511/1364007-20251123234521921-1044694549.jpg)
![](https://img2024.cnblogs.com/blog/1364007/202511/1364007-20251123231736292-1749490550.jpg)
## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。
