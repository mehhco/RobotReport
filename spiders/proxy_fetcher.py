"""
代理获取和验证工具
支持从多个免费源获取代理，并验证其可用性
"""

import requests
import time
import threading
import concurrent.futures
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class ProxyFetcher:
    def __init__(self):
        """初始化代理获取器"""
        self.proxy_sources = {
            'kuaidaili': 'https://www.kuaidaili.com/free/inha/',
            'xicidaili': 'https://www.xicidaili.com/nn/',
            '89ip': 'https://www.89ip.cn/',
            'ihuan': 'https://ip.ihuan.me/',
            'ip3366': 'http://www.ip3366.net/free/'
        }
        self.test_url = 'http://httpbin.org/ip'  # 测试URL
        self.timeout = 10  # 超时时间
        
    def fetch_kuaidaili(self) -> List[str]:
        """从快代理获取免费代理"""
        proxies = []
        try:
            # 这里需要根据实际网站结构调整
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.proxy_sources['kuaidaili'], headers=headers, timeout=10)
            # 需要解析HTML页面获取代理列表
            # 这里只是示例，实际需要根据网站结构解析
            logger.info("从快代理获取代理列表")
        except Exception as e:
            logger.error(f"获取快代理失败: {e}")
        return proxies
    
    def fetch_89ip(self) -> List[str]:
        """从89代理获取免费代理"""
        proxies = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.proxy_sources['89ip'], headers=headers, timeout=10)
            # 解析HTML获取代理列表
            logger.info("从89代理获取代理列表")
        except Exception as e:
            logger.error(f"获取89代理失败: {e}")
        return proxies
    
    def fetch_from_api(self) -> List[str]:
        """从API获取代理"""
        proxies = []
        
        # 示例API（需要替换为真实可用的API）
        api_urls = [
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps'
        ]
        
        for api_url in api_urls:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # 根据API返回格式解析代理
                    logger.info(f"从API获取代理: {api_url}")
            except Exception as e:
                logger.error(f"API获取失败 {api_url}: {e}")
        
        return proxies
    
    def test_proxy(self, proxy: str) -> bool:
        """测试单个代理的可用性"""
        try:
            proxies = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(
                self.test_url, 
                proxies=proxies, 
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.debug(f"代理可用: {proxy}")
                return True
        except Exception as e:
            logger.debug(f"代理不可用 {proxy}: {e}")
        return False
    
    def test_proxies_batch(self, proxies: List[str], max_workers: int = 10) -> List[str]:
        """批量测试代理"""
        valid_proxies = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in proxies}
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        valid_proxies.append(proxy)
                except Exception as e:
                    logger.error(f"测试代理异常 {proxy}: {e}")
        
        return valid_proxies
    
    def get_proxies(self, max_proxies: int = 50) -> List[str]:
        """获取可用代理列表"""
        all_proxies = []
        
        # 从多个源获取代理
        logger.info("开始获取代理列表...")
        
        # 从免费源获取
        all_proxies.extend(self.fetch_kuaidaili())
        all_proxies.extend(self.fetch_89ip())
        all_proxies.extend(self.fetch_from_api())
        
        # 去重
        all_proxies = list(set(all_proxies))
        logger.info(f"获取到 {len(all_proxies)} 个代理")
        
        # 测试代理可用性
        logger.info("开始测试代理可用性...")
        valid_proxies = self.test_proxies_batch(all_proxies)
        
        logger.info(f"测试完成，可用代理: {len(valid_proxies)}/{len(all_proxies)}")
        
        return valid_proxies[:max_proxies]
    
    def save_proxies(self, proxies: List[str], filename: str = 'proxies.json'):
        """保存代理列表到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(proxies, f, ensure_ascii=False, indent=2)
            logger.info(f"代理列表已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存代理列表失败: {e}")
    
    def load_proxies(self, filename: str = 'proxies.json') -> List[str]:
        """从文件加载代理列表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                proxies = json.load(f)
            logger.info(f"从 {filename} 加载了 {len(proxies)} 个代理")
            return proxies
        except Exception as e:
            logger.error(f"加载代理列表失败: {e}")
            return []

def main():
    """主函数 - 获取和测试代理"""
    fetcher = ProxyFetcher()
    
    # 获取代理
    proxies = fetcher.get_proxies(max_proxies=20)
    
    # 保存代理
    if proxies:
        fetcher.save_proxies(proxies)
        print(f"成功获取 {len(proxies)} 个可用代理:")
        for proxy in proxies:
            print(f"  - {proxy}")
    else:
        print("未获取到可用代理")

if __name__ == "__main__":
    main() 