import os
import yaml
import json
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
from urllib.parse import urlencode
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RoboCrawler:
    def __init__(self):
        self.config = self._load_config()
        self.session = requests.Session()
        self.idset = set()
        self.cookies = None
        
    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join('configs', 'sites.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_date_range(self):
        """获取日期范围"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        return {
            'pubTimeEnd': end_date.strftime('%Y%m%d'),
            'pubTimeStart': start_date.strftime('%Y%m%d')
        }
    
    def login_with_edge(self):
        """使用Edge浏览器登录并获取cookies"""
        try:
            options = Options()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
            options.add_argument('--ignore-ssl-errors')  # 忽略SSL错误
            # 使用 webdriver_manager 自动管理驱动
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            
            # 访问登录页面
            driver.get(self.config['baseUrl_login'])
            time.sleep(5)  # 等待页面加载
            
            # 获取cookies
            self.cookies = driver.get_cookies()
            
            # 将cookies添加到session中
            for cookie in self.cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            driver.quit()
            logger.info("登录成功并获取cookies")
            
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            raise
    
    def fetch_report_list(self):
        """获取报告列表"""
        base_url = self.config['baseUrl_industry']
        params = self.config['params'].copy()
        date_range = self._get_date_range()
        params.update(date_range)
        
        page_now = 1
        while True:
            params['pageNow'] = page_now
            url = f"{base_url}?{urlencode(params)}"
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                # 提取报告ID
                for item in data['data']['list']:
                    if item['type'] == 'EXTERNAL_REPORT':
                        self.idset.add(item['data']['id'])
                
                # 检查是否还有下一页
                if page_now >= data['data']['pageCount']:
                    break
                    
                page_now += 1
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"获取报告列表失败: {str(e)}")
                raise
    
    def download_report(self, report_id, sequence, total_count):
        """下载单篇报告"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 获取PDF下载地址
                overview_url = f"{self.config['report_overview_url']}/{report_id}/pdf"
                
                # 添加随机User-Agent和请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://robo.datayes.com/',
                    'Origin': 'https://robo.datayes.com',
                    'Connection': 'keep-alive'
                }
                
                response = self.session.get(overview_url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # 检查响应结构
                if 'data' not in data or 'downloadUrl' not in data['data']:
                    logger.warning(f"报告 {report_id} 没有下载链接，可能需要重新登录")
                    # 如果是认证问题，重新获取cookies
                    if attempt == 0:
                        self.login_with_edge()
                        continue
                    else:
                        logger.error(f"报告 {report_id} 最终无法获取下载链接")
                        return
                
                download_url = data['data']['downloadUrl']
                
                # 下载PDF
                pdf_response = self.session.get(download_url, headers=headers, timeout=60)
                pdf_response.raise_for_status()
                
                # 保存PDF
                filename = f"reports/{report_id}.pdf"
                os.makedirs('reports', exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(pdf_response.content)
                    
                logger.info(f"成功下载报告: {filename} 第{sequence}/{total_count}篇")
                return  # 成功下载，退出重试循环
                
            except Exception as e:
                logger.warning(f"下载报告失败 {report_id} (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(10 * (attempt + 1))  # 增加等待时间
                else:
                    logger.error(f"下载报告最终失败 {report_id}: {str(e)}")
    
    def run(self):
        """运行爬虫"""
        try:
            # 1. 登录获取cookies
            self.login_with_edge()
            
            # 2. 获取报告列表
            self.fetch_report_list()
            logger.info(f"共获取到 {len(self.idset)} 篇报告")
            start_time = time.time()
            # 3. 下载报告
            for i, report_id in enumerate(self.idset):
                self.download_report(report_id, i, len(self.idset))
                # 每下载5篇报告后休息更长时间
                if (i + 1) % 5 == 0:
                    logger.info("休息10秒...")
                    time.sleep(10)
                else:
                    time.sleep(3)  # 增加等待时间
            
            # 增加耗时信息
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"爬虫运行结束，耗时 {duration:.2f} 秒")
                
        except Exception as e:
            logger.error(f"爬虫运行失败: {str(e)}")
            raise

if __name__ == "__main__":
    crawler = RoboCrawler()
    crawler.run()
