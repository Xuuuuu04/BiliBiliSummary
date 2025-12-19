import asyncio
import json
import time
import qrcode
import io
import base64
from bilibili_api import login_v2
from typing import Dict, Optional
import os
from src.config import Config


class BilibiliLoginService:
    """B站登录服务（使用bilibili_api login_v2模块）"""

    def __init__(self):
        self.active_sessions = {}  # 存储活跃的登录会话

    async def start_login(self) -> Dict:
        """开始真正的B站QR码登录流程"""
        try:
            # 创建QR码登录实例
            qr_login = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)

            # 生成QR码
            await qr_login.generate_qrcode()

            # 获取QR码图片数据
            qr_picture = qr_login.get_qrcode_picture()
            qr_image_data = base64.b64encode(qr_picture.content).decode('utf-8')

            # 生成会话ID
            session_id = f"qr_{int(time.time())}"

            # 存储登录实例
            self.active_sessions[session_id] = {
                'qr_login': qr_login,
                'created_at': time.time()
            }

            print(f"[登录] 生成QR码成功，会话ID: {session_id}")

            return {
                'success': True,
                'data': {
                    'session_id': session_id,
                    'qr_code': f"data:image/png;base64,{qr_image_data}",
                    'message': '请使用B站手机APP扫描二维码登录'
                }
            }

        except Exception as e:
            print(f"[错误] 生成QR码失败: {str(e)}")
            return {
                'success': False,
                'error': f'生成QR码失败: {str(e)}'
            }

    async def check_login_status(self, session_id: str) -> Dict:
        """检查QR码登录状态"""
        try:
            # 检查会话是否存在
            if session_id not in self.active_sessions:
                return {
                    'success': False,
                    'error': '会话不存在或已过期'
                }

            session_data = self.active_sessions[session_id]
            qr_login = session_data['qr_login']

            # 检查登录状态
            state = await qr_login.check_state()

            print(f"[登录] 检查状态 - 会话: {session_id}, 状态: {state}")

            if state == login_v2.QrCodeLoginEvents.DONE:
                # 登录成功，获取凭据
                credential = qr_login.get_credential()

                # 提取cookie数据
                cookies = credential.get_cookies()
                print(f"[调试] 获取到的cookies: {list(cookies.keys())}")

                # 构建凭据字典（get_cookies()返回的是字典格式）
                credentials = {
                    'SESSDATA': cookies.get('SESSDATA', ''),
                    'bili_jct': cookies.get('bili_jct', ''),
                    'buvid3': cookies.get('buvid3', ''),
                    'DedeUserID': cookies.get('DedeUserID', '')
                }

                print(f"[调试] 构建的凭据: {[k for k, v in credentials.items() if v]}")

                # 保存凭据到.env文件
                save_success = await self.save_credentials(credentials)

                if save_success:
                    # 清理会话
                    del self.active_sessions[session_id]

                    return {
                        'success': True,
                        'data': {
                            'status': 'success',
                            'message': '登录成功！凭据已自动保存'
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': '保存凭据失败'
                    }

            elif state == login_v2.QrCodeLoginEvents.TIMEOUT:
                # QR码过期
                del self.active_sessions[session_id]
                return {
                    'success': True,
                    'data': {
                        'status': 'expired',
                        'message': 'QR码已过期，请重新获取'
                    }
                }

            elif state in [login_v2.QrCodeLoginEvents.SCAN, login_v2.QrCodeLoginEvents.CONF]:
                # 已扫描或已确认，等待下一步
                return {
                    'success': True,
                    'data': {
                        'status': 'waiting',
                        'message': '等待确认登录...' if state == login_v2.QrCodeLoginEvents.SCAN else '请在手机上确认登录'
                    }
                }

            else:  # 其他未知状态
                return {
                    'success': True,
                    'data': {
                        'status': 'waiting',
                        'message': '等待扫码或确认...'
                    }
                }

        except Exception as e:
            print(f"[错误] 检查登录状态失败: {str(e)}")
            return {
                'success': False,
                'error': f'检查登录状态失败: {str(e)}'
            }

    async def save_credentials(self, credentials: Dict[str, str]) -> bool:
        """保存登录凭据到.env文件"""
        try:
            env_file = '.env'

            # 更新内存中的配置
            Config.BILIBILI_SESSDATA = credentials.get('SESSDATA', '')
            Config.BILIBILI_BILI_JCT = credentials.get('bili_jct', '')
            Config.BILIBILI_BUVID3 = credentials.get('buvid3', '')
            Config.BILIBILI_DEDEUSERID = credentials.get('DedeUserID', '')

            # 读取现有的.env内容
            env_content = {}
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_content[key] = value

            # 更新凭据（处理键名映射）
            env_content.update({
                'BILIBILI_SESSDATA': Config.BILIBILI_SESSDATA,
                'BILIBILI_BILI_JCT': Config.BILIBILI_BILI_JCT,
                'BILIBILI_BUVID3': Config.BILIBILI_BUVID3,
                'BILIBILI_DEDEUSERID': Config.BILIBILI_DEDEUSERID
            })

            # 写入.env文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# B站API配置（自动保存）\n")
                for key, value in env_content.items():
                    if key.startswith('BILIBILI_'):
                        f.write(f"{key}={value}\n")

                f.write("\n# 其他配置\n")
                for key, value in env_content.items():
                    if not key.startswith('BILIBILI_'):
                        f.write(f"{key}={value}\n")

            print("[登录] 凭据已保存到.env文件并更新内存")
            return True

        except Exception as e:
            print(f"[错误] 保存凭据失败: {str(e)}")
            return False

    def cleanup_expired_sessions(self):
        """清理过期的登录会话"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            # 5分钟后会话过期
            if current_time - session_data['created_at'] > 300:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            print(f"[登录] 清理过期会话: {session_id}")

    async def logout(self) -> Dict:
        """登出并清理凭据"""
        try:
            # 清理所有活跃会话
            self.active_sessions.clear()

            # 清理内存中的凭据
            Config.BILIBILI_SESSDATA = None
            Config.BILIBILI_BILI_JCT = None
            Config.BILIBILI_BUVID3 = None
            Config.BILIBILI_DEDEUSERID = None

            # 清理.env文件中的B站凭据
            env_file = '.env'
            if os.path.exists(env_file):
                env_content = {}
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if not key.startswith('BILIBILI_'):
                                env_content[key] = value

                # 重写.env文件
                with open(env_file, 'w', encoding='utf-8') as f:
                    for key, value in env_content.items():
                        f.write(f"{key}={value}\n")

            print("[登录] 已清理B站登录凭据(内存及文件)和所有会话")

            return {
                'success': True,
                'data': {
                    'message': '已成功登出，凭据已清理'
                }
            }

        except Exception as e:
            print(f"[错误] 登出失败: {str(e)}")
            return {
                'success': False,
                'error': f'登出失败: {str(e)}'
            }


# 全局登录服务实例
login_service = BilibiliLoginService()