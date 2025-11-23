import requests
import json
import time
import random
import os
import re
import base64
from datetime import datetime
from bs4 import BeautifulSoup
from docx import Document
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class WeChatScraper:
    def __init__(self, cookie, token):
        self.cookie = cookie
        self.token = token
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie
        }
        # Initialize driver path once
        self.driver_path = self._get_driver_path()

    def _get_driver_path(self):
        try:
            driver_path = ChromeDriverManager().install()
            if "THIRD_PARTY_NOTICES" in driver_path:
                driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver")
            os.chmod(driver_path, 0o755)
            return driver_path
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return None

    def log(self, message, callback=None):
        if callback:
            callback(message)
        else:
            print(message)

    def get_fakeid(self, name, callback=None):
        """Search for the official account and get its fakeid."""
        url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        params = {
            "action": "search_biz",
            "begin": 0,
            "count": 5,
            "query": name,
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": 1
        }
        
        try:
            self.log(f"Searching for '{name}'...", callback)
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if data.get('base_resp', {}).get('ret') != 0:
                self.log(f"Error searching for account: {data}", callback)
                return None
                
            for item in data.get('list', []):
                if item['nickname'] == name:
                    return item['fakeid']
            
            self.log(f"Account '{name}' not found.", callback)
            return None
        except Exception as e:
            self.log(f"Exception in get_fakeid: {e}", callback)
            return None

    def get_articles(self, fakeid, callback=None):
        """Fetch article list for the given fakeid."""
        url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        articles = []
        page = 0
        MAX_PAGES_ESTIMATE = 40 
        
        while True:
            self.log(f"Fetching page {page + 1}...", callback)
            params = {
                "token": self.token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": 1,
                "action": "list_ex",
                "begin": page * 5,
                "count": 5,
                "query": "",
                "fakeid": fakeid,
                "type": 9
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                data = response.json()
                
                if data.get('base_resp', {}).get('ret') == 200013:
                    self.log("⚠️ Rate limit detected (freq control). Waiting 60 seconds...", callback)
                    time.sleep(60)
                    response = requests.get(url, headers=self.headers, params=params)
                    data = response.json()
                    if data.get('base_resp', {}).get('ret') != 0:
                        self.log("❌ Rate limit persists. Please try again in 1-24 hours.", callback)
                        break

                if data.get('base_resp', {}).get('ret') != 0:
                    self.log(f"Error fetching articles: {data}", callback)
                    break
                    
                msg_list = data.get('app_msg_list', [])
                if not msg_list:
                    self.log("No more articles found.", callback)
                    break
                    
                for msg in msg_list:
                    create_time = datetime.fromtimestamp(msg['create_time'])
                    date_str = create_time.strftime('%Y-%m-%d')
                    
                    article_info = {
                        "title": msg['title'],
                        "link": msg['link'],
                        "create_time": msg['create_time'],
                        "date_str": date_str,
                        "digest": msg['digest']
                    }
                    articles.append(article_info)
                
                page += 1
                
                if page > MAX_PAGES_ESTIMATE:
                    self.log("⚠️ Warning: Reached potential WeChat API limit (approx 200 articles). Older articles may not be accessible via this method.", callback)
                
                time.sleep(random.randint(3, 6)) 
                
            except Exception as e:
                self.log(f"Exception in get_articles: {e}", callback)
                break
                
        return articles

    def _clean_filename(self, title):
        return re.sub(r'[\\/*?:"<>|]', "", title)

    def _convert_html_to_pdf_selenium(self, html_path, pdf_path):
        """Convert HTML file to PDF using Selenium (Print to PDF)."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        driver = None
        try:
            driver = webdriver.Chrome(service=Service(self.driver_path), options=options)
            driver.get(f"file://{os.path.abspath(html_path)}")
            
            print_params = {
                "landscape": False,
                "displayHeaderFooter": False,
                "printBackground": True,
                "preferCSSPageSize": True,
            }
            
            result = driver.execute_cdp_cmd("Page.printToPDF", print_params)
            
            with open(pdf_path, 'wb') as f:
                f.write(base64.b64decode(result['data']))
                
            return True
        except Exception as e:
            print(f"Selenium PDF Error: {e}")
            return False
        finally:
            if driver:
                driver.quit()

    def save_article_content(self, article, base_dir, formats=['html'], callback=None):
        """Download and save the article content in specified formats."""
        title = article['title']
        date_str = article['date_str']
        safe_title = self._clean_filename(title)
        filename_base = f"{date_str}_{safe_title}"
        
        # Fetch content once
        try:
            response = requests.get(article['link'], headers=self.headers)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                self.log(f"Failed to download {title}: Status {response.status_code}", callback)
                return False
            html_content = response.text
        except Exception as e:
            self.log(f"Error downloading {title}: {e}", callback)
            return False

        success = False

        # 1. HTML (Always save first)
        save_dir_html = os.path.join(base_dir, "HTML")
        if not os.path.exists(save_dir_html): os.makedirs(save_dir_html)
        html_filepath = os.path.join(save_dir_html, f"{filename_base}.html")
        
        if not os.path.exists(html_filepath):
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            if 'html' in formats: success = True
        elif 'html' in formats:
            self.log(f"Skip HTML (Exists): {filename_base}", callback)
            success = True

        # 2. PDF (Selenium)
        if 'pdf' in formats:
            save_dir_pdf = os.path.join(base_dir, "PDF")
            if not os.path.exists(save_dir_pdf): os.makedirs(save_dir_pdf)
            filepath = os.path.join(save_dir_pdf, f"{filename_base}.pdf")
            
            if not os.path.exists(filepath):
                try:
                    pdf_success = self._convert_html_to_pdf_selenium(html_filepath, filepath)
                    if pdf_success:
                        success = True
                    else:
                        self.log(f"Error converting to PDF", callback)
                except Exception as e:
                    self.log(f"Error converting to PDF: {e}", callback)
            else:
                self.log(f"Skip PDF (Exists): {filename_base}", callback)

        # 4. Word (Robust Text Extraction)
        if 'docx' in formats:
            save_dir_word = os.path.join(base_dir, "Word")
            if not os.path.exists(save_dir_word): os.makedirs(save_dir_word)
            filepath = os.path.join(save_dir_word, f"{filename_base}.docx")
            
            if not os.path.exists(filepath):
                try:
                    doc = Document()
                    doc.add_heading(title, 0)
                    doc.add_paragraph(f"发布日期: {date_str}")
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    content_div = soup.find(id="js_content")
                    
                    if content_div:
                        # Extract text paragraphs and headings
                        for element in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            text = element.get_text(strip=True)
                            if text:
                                if element.name.startswith('h'):
                                    level = int(element.name[1])
                                    doc.add_heading(text, level=level)
                                else:
                                    doc.add_paragraph(text)
                    else:
                        # Fallback if no js_content
                        doc.add_paragraph("无法解析文章内容结构，仅保存纯文本。")
                        doc.add_paragraph(soup.get_text())

                    doc.save(filepath)
                    success = True
                except Exception as e:
                    self.log(f"Error converting to Word: {e}", callback)
            else:
                self.log(f"Skip Word (Exists): {filename_base}", callback)

        if success:
            self.log(f"Downloaded: {filename_base}", callback)
            
        return success
