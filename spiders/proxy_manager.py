"""
代理管理模块
用于轮换IP地址，避免被单一IP限制
"""

import random
import time
import logging
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxy_list: List[str] = None):
        """
        初始化代理管理器
        
        Args:
            proxy_list: 代理列表，格式: ['http://ip:port', 'socks5://ip:port']
        """
        self.proxy_list = proxy_list or []
        self.current_proxy = None
        self.proxy_failures = {}  # 记录每个代理的失败次数
        self.max_failures = 3  # 单个代理最大失败次数
        
    def add_proxy(self, proxy: str):
        """添加代理"""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            logger.info(f"添加代理: {proxy}")
    
    def remove_proxy(self, proxy: str):
        """移除代理"""
        if proxy in self.proxy_list:
            self.proxy_list.remove(proxy)
            if proxy in self.proxy_failures:
                del self.proxy_failures[proxy]
            logger.info(f"移除代理: {proxy}")
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """获取可用代理"""
        if not self.proxy_list:
            return None
        
        # 过滤掉失败次数过多的代理
        available_proxies = [
            proxy for proxy in self.proxy_list 
            if self.proxy_failures.get(proxy, 0) < self.max_failures
        ]
        
        if not available_proxies:
            # 重置所有代理的失败计数
            self.proxy_failures.clear()
            available_proxies = self.proxy_list
            logger.warning("所有代理都失败次数过多，重置失败计数")
        
        # 随机选择一个代理
        self.current_proxy = random.choice(available_proxies)
        logger.debug(f"使用代理: {self.current_proxy}")
        
        return {
            'http': self.current_proxy,
            'https': self.current_proxy
        }
    
    def mark_failure(self, proxy: str = None):
        """标记代理失败"""
        proxy = proxy or self.current_proxy
        if proxy:
            self.proxy_failures[proxy] = self.proxy_failures.get(proxy, 0) + 1
            logger.warning(f"代理 {proxy} 失败，当前失败次数: {self.proxy_failures[proxy]}")
    
    def mark_success(self, proxy: str = None):
        """标记代理成功"""
        proxy = proxy or self.current_proxy
        if proxy and proxy in self.proxy_failures:
            self.proxy_failures[proxy] = max(0, self.proxy_failures[proxy] - 1)
            logger.debug(f"代理 {proxy} 成功，减少失败计数")
    
    def rotate_proxy(self):
        """强制轮换代理"""
        if self.current_proxy:
            logger.info(f"轮换代理: {self.current_proxy}")
        self.current_proxy = None
    
    def get_status(self) -> Dict:
        """获取代理状态"""
        return {
            'total_proxies': len(self.proxy_list),
            'current_proxy': self.current_proxy,
            'proxy_failures': self.proxy_failures.copy(),
            'available_proxies': len([
                p for p in self.proxy_list 
                if self.proxy_failures.get(p, 0) < self.max_failures
            ])
        }

# 示例代理列表（需要替换为真实代理）
SAMPLE_PROXIES = [
    # 'http://proxy1:8080',
    # 'http://proxy2:8080',
    # 'socks5://proxy3:1080',
]

def create_proxy_manager(use_proxies: bool = False) -> Optional[ProxyManager]:
    """
    创建代理管理器
    
    Args:
        use_proxies: 是否使用代理
        
    Returns:
        ProxyManager实例或None
    """
    if not use_proxies:
        return None
    
    # 这里可以从配置文件或环境变量读取代理列表
    proxy_list = SAMPLE_PROXIES
    if proxy_list:
        return ProxyManager(proxy_list)
    else:
        logger.warning("未配置代理列表，将不使用代理")
        return None 

def get_free_proxies():
    """获取免费代理列表"""
    proxies = []
    
    # 快代理API
    try:
        response = requests.get('https://www.kuaidaili.com/api/getproxy/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('data', []):
                proxies.append(f"http://{item['ip']}:{item['port']}")
    except:
        pass
    
    return proxies 