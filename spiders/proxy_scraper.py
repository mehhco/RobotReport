"""
实际可用的代理爬取脚本
包含HTML解析和代理验证
"""

import requests
import re
import time
import json
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_kuaidaili(self) -> List[str]:
        """从快代理爬取免费代理"""
        proxies = []
        try:
            url = 'https://www.kuaidaili.com/free/inha/'
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找代理表格
            table = soup.find('table', class_='table table-bordered table-striped')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
            
            logger.info(f"从快代理获取到 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"爬取快代理失败: {e}")
        
        return proxies
    
    def scrape_89ip(self) -> List[str]:
        """从89代理爬取免费代理"""
        proxies = []
        try:
            url = 'https://www.89ip.cn/'
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找代理表格
            table = soup.find('table', class_='layui-table')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
            
            logger.info(f"从89代理获取到 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"爬取89代理失败: {e}")
        
        return proxies
    
    def scrape_xicidaili(self) -> List[str]:
        """从西刺代理爬取免费代理"""
        proxies = []
        try:
            url = 'https://www.xicidaili.com/nn/'
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找代理表格
            table = soup.find('table', id='ip_list')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        ip = cols[1].text.strip()
                        port = cols[2].text.strip()
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
            
            logger.info(f"从西刺代理获取到 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"爬取西刺代理失败: {e}")
        
        return proxies
    
    def scrape_ip3366(self) -> List[str]:
        """从云代理爬取免费代理"""
        proxies = []
        try:
            url = 'http://www.ip3366.net/free/'
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找代理表格
            table = soup.find('table', class_='table table-bordered table-striped')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
            
            logger.info(f"从云代理获取到 {len(proxies)} 个代理")
        except Exception as e:
            logger.error(f"爬取云代理失败: {e}")
        
        return proxies
    
    def test_proxy(self, proxy: str) -> bool:
        """测试单个代理"""
        try:
            proxies = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            if response.status_code == 200:
                logger.debug(f"代理可用: {proxy}")
                return True
        except:
            pass
        return False
    
    def test_proxies_batch(self, proxies: List[str], max_workers: int = 20) -> List[str]:
        """批量测试代理"""
        valid_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in proxies}
            
            for future in future_to_proxy:
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        valid_proxies.append(proxy)
                except:
                    pass
        
        return valid_proxies
    
    def get_all_proxies(self) -> List[str]:
        """获取所有代理"""
        all_proxies = []
        
        # 从多个源爬取
        all_proxies.extend(self.scrape_kuaidaili())
        time.sleep(2)  # 避免请求过快
        
        all_proxies.extend(self.scrape_89ip())
        time.sleep(2)
        
        all_proxies.extend(self.scrape_xicidaili())
        time.sleep(2)
        
        all_proxies.extend(self.scrape_ip3366())
        
        # 去重
        all_proxies = list(set(all_proxies))
        logger.info(f"总共获取到 {len(all_proxies)} 个唯一代理")
        
        return all_proxies
    
    def get_valid_proxies(self, max_proxies: int = 50) -> List[str]:
        """获取有效代理"""
        all_proxies = self.get_all_proxies()
        
        if not all_proxies:
            logger.warning("未获取到任何代理")
            return []
        
        logger.info("开始测试代理可用性...")
        valid_proxies = self.test_proxies_batch(all_proxies)
        
        logger.info(f"测试完成，可用代理: {len(valid_proxies)}/{len(all_proxies)}")
        
        return valid_proxies[:max_proxies]
    
    def save_proxies(self, proxies: List[str], filename: str = 'valid_proxies.json'):
        """保存代理到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(proxies, f, ensure_ascii=False, indent=2)
            logger.info(f"代理已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存代理失败: {e}")

def main():
    """主函数"""
    scraper = ProxyScraper()
    
    print("开始获取代理...")
    valid_proxies = scraper.get_valid_proxies(max_proxies=30)
    
    if valid_proxies:
        scraper.save_proxies(valid_proxies)
        print(f"\n成功获取 {len(valid_proxies)} 个可用代理:")
        for i, proxy in enumerate(valid_proxies, 1):
            print(f"{i:2d}. {proxy}")
    else:
        print("未获取到可用代理")

if __name__ == "__main__":
    main() 