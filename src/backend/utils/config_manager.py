"""
配置管理器模块

提供统一的配置管理、验证和持久化功能
"""
import os
import asyncio
from pathlib import Path
from typing import Any, Optional, Dict, Callable
from threading import Lock
from src.config import Config
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    配置管理器

    提供配置的读取、更新、验证和持久化功能
    """

    def __init__(self):
        """初始化配置管理器"""
        self._lock = Lock()
        self._watchers: Dict[str, list] = {}  # 配置变更监听器

        # 项目根目录
        self._project_root = Path(__file__).parent.parent.parent.parent.parent
        self._env_file = self._project_root / '.env'

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'openai.model'）
            default: 默认值

        Returns:
            配置值
        """
        # 从 Config 类获取
        value = getattr(Config, key.upper(), default)
        return value

    def set(self, key: str, value: Any, persist: bool = False) -> bool:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化到 .env 文件

        Returns:
            是否设置成功
        """
        with self._lock:
            try:
                # 更新 Config 对象
                setattr(Config, key.upper(), value)

                logger.info(f"配置已更新: {key} = {'***' if self._is_sensitive(key) else value}")

                # 触发监听器
                self._notify_watchers(key, value)

                # 持久化到 .env 文件
                if persist:
                    self._persist_to_env(key, value)

                return True
            except Exception as e:
                logger.error(f"设置配置失败: {key} = {value}, 错误: {str(e)}")
                return False

    def update_bilibili_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        更新B站凭据并同步到所有服务

        Args:
            credentials: 凭据字典
                - SESSDATA: SESSDATA
                - BILI_JCT: bili_jct
                - BUVID3: buvid3
                - DEDEUSERID: DedeUserID

        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                # 更新 Config
                Config.BILIBILI_SESSDATA = credentials.get('SESSDATA', '')
                Config.BILIBILI_BILI_JCT = credentials.get('BILI_JCT', '')
                Config.BILIBILI_BUVID3 = credentials.get('BUVID3', '')
                Config.BILIBILI_DEDEUSERID = credentials.get('DEDEUSERID', '')

                logger.info("B站凭据已更新到内存")

                # 持久化到 .env 文件
                self._persist_bilibili_credentials(credentials)

                # 触发凭据变更事件
                self._notify_watchers('bilibili_credentials', credentials)

                return True
            except Exception as e:
                logger.error(f"更新B站凭据失败: {str(e)}")
                return False

    def watch(self, key: str, callback: Callable[[Any], None]):
        """
        监听配置变更

        Args:
            key: 配置键
            callback: 回调函数
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
        logger.debug(f"注册配置监听器: {key}")

    def _notify_watchers(self, key: str, value: Any):
        """
        通知配置变更监听器

        Args:
            key: 配置键
            value: 新值
        """
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"配置监听器回调失败: {key}, 错误: {str(e)}")

    def _persist_to_env(self, key: str, value: str):
        """
        持久化配置到 .env 文件

        Args:
            key: 配置键
            value: 配置值
        """
        try:
            if not self._env_file.exists():
                logger.warning(f".env 文件不存在: {self._env_file}")
                return

            # 读取现有配置
            env_content = {}
            with open(self._env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env_content[k] = v

            # 更新配置
            env_key = key.upper()
            env_content[env_key] = value

            # 写回文件
            with open(self._env_file, 'w', encoding='utf-8') as f:
                for k, v in env_content.items():
                    f.write(f"{k}={v}\n")

            logger.debug(f"配置已持久化到 .env: {env_key}")
        except Exception as e:
            logger.error(f"持久化配置失败: {key}, 错误: {str(e)}")

    def _persist_bilibili_credentials(self, credentials: Dict[str, str]):
        """
        持久化B站凭据到 .env 文件

        Args:
            credentials: 凭据字典
        """
        try:
            if not self._env_file.exists():
                logger.warning(f".env 文件不存在: {self._env_file}")
                return

            # 读取现有配置
            env_content = {}
            with open(self._env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env_content[k] = v

            # 更新B站凭据
            env_content['BILIBILI_SESSDATA'] = credentials.get('SESSDATA', '')
            env_content['BILIBILI_BILI_JCT'] = credentials.get('BILI_JCT', '')
            env_content['BILIBILI_BUVID3'] = credentials.get('BUVID3', '')
            env_content['BILIBILI_DEDEUSERID'] = credentials.get('DEDEUSERID', '')

            # 写回文件
            with open(self._env_file, 'w', encoding='utf-8') as f:
                f.write("# B站API配置（自动保存）\n")
                for key, value in env_content.items():
                    if key.startswith('BILIBILI_'):
                        f.write(f"{key}={value}\n")
                    elif not key.startswith('OPENAI_'):  # 非敏感配置
                        f.write(f"{key}={value}\n")

            logger.info("B站凭据已持久化到 .env 文件")
        except Exception as e:
            logger.error(f"持久化B站凭据失败: {str(e)}")

    def _is_sensitive(self, key: str) -> bool:
        """
        判断配置是否敏感

        Args:
            key: 配置键

        Returns:
            是否敏感
        """
        sensitive_keys = ['key', 'token', 'password', 'secret', 'cookie', 'sessdata']
        return any(sk in key.lower() for sk in sensitive_keys)

    def validate_required(self) -> bool:
        """
        验证必需配置是否存在

        Returns:
            是否全部配置
        """
        required_configs = {
            'OPENAI_API_KEY': 'AI服务密钥',
            'OPENAI_MODEL': '主分析模型'
        }

        missing = []
        for key, desc in required_configs.items():
            if not getattr(Config, key, None):
                missing.append(desc)

        if missing:
            logger.error(f"缺少必需配置: {', '.join(missing)}")
            return False

        logger.info("所有必需配置已就绪")
        return True

    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要（脱敏）

        Returns:
            配置摘要字典
        """
        return {
            'ai_model': Config.OPENAI_MODEL,
            'qa_model': Config.QA_MODEL,
            'research_model': Config.DEEP_RESEARCH_MODEL,
            'api_base': Config.OPENAI_API_BASE,
            'api_key_configured': bool(Config.OPENAI_API_KEY),
            'bilibili_logged_in': bool(Config.BILIBILI_SESSDATA),
            'flask_port': Config.FLASK_PORT,
            'flask_host': Config.FLASK_HOST
        }


# 全局单例
config_manager = ConfigManager()
