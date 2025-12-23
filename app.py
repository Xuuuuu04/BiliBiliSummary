"""
BiliBili 视频总结系统 - 主应用入口
重构版本：使用模块化路由架构
"""
from flask import Flask
from flask_cors import CORS
import os

# 使用绝对路径确保在不同环境下都能找到前端资源
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(BASE_DIR, 'src', 'frontend')

# 创建 Flask 应用
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

# 初始化核心服务（使用新的模块化架构）
from src.backend.services.bilibili import BilibiliService
from src.backend.services.ai import AIService
from src.backend.services.bilibili.login_service import LoginService

bilibili_service = BilibiliService()
ai_service = AIService()
login_service = LoginService()  # 实例化登录服务

# 创建 AI 服务引用容器（用于动态刷新）
ai_service_ref = {'service': ai_service}

# 初始化路由模块
from src.backend.api.routes import (
    init_settings_routes,
    init_research_routes,
    init_analyze_routes,
    init_bilibili_routes,
    init_user_routes
)
from src.backend.api.routes.helpers import init_helper_routes

# 注册所有路由
init_helper_routes(app)  # 首页和静态资源
init_settings_routes(app, ai_service_ref)  # 设置管理
init_research_routes(app, ai_service, bilibili_service)  # 深度研究
init_analyze_routes(app, bilibili_service, ai_service)  # 视频分析
init_bilibili_routes(app, bilibili_service, login_service)  # B站数据和登录
init_user_routes(app, bilibili_service, ai_service)  # 用户画像

if __name__ == '__main__':
    from src.config import Config

    # 终端颜色代码
    PINK = '\033[38;5;213m'
    BLUE = '\033[38;5;75m'
    GOLD = '\033[38;5;220m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # 顶级 Bilibili 风格 ASCII LOGO
    logo = f"""
{PINK}   ██████╗ ██╗██╗     ██╗██████╗ ██╗██╗     ██╗
   ██╔══██╗██║██║     ██║██╔══██╗██║██║     ██║
   ██████╔╝██║██║     ██║██████╔╝██║██║     ██║
   ██╔══██╗██║██║     ██║██╔══██╗██║██║     ██║
   ██████╔╝██║███████╗██║██████╔╝██║███████╗██║
   ╚═════╝ ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝╚══════╝╚═╝{RESET}

{BLUE}   ███████╗██╗   ██╗███╗   ███╗███╗   ███╗ █████╗ ██████╗ ██╗███████╗███████╗
   ██╔════╝██║   ██║████╗ ████║████╗ ████║██╔══██╗██╔══██╗██║╚══███╔╝██╔════╝
   ███████╗██║   ██║██╔████╔██║██╔████╔██║███████║██████╔╝██║  ███╔╝ █████╗
   ╚════██║██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██╔══██╗██║ ███╔╝  ██╔════╝
   ███████║╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║  ██║██║███████╗███████╗
   ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝{RESET}
    """
    print(logo)
    print(f"{BOLD}🚀 BiliBili视频总结系统正在启动...{RESET}")
    print(f"{'='*60}")
    print(f"{BOLD}📡 运行配置:{RESET}")
    print(f"  > {BOLD}服务地址:{RESET} {BLUE}http://{Config.FLASK_HOST}:{Config.FLASK_PORT}{RESET}")
    print(f"  > {BOLD}调试模式:{RESET} {GOLD}{Config.FLASK_DEBUG}{RESET}")
    print(f"\n{BOLD}🤖 AI 引擎配置:{RESET}")
    print(f"  > {BOLD}基础模型:{RESET} {BLUE}{Config.OPENAI_MODEL}{RESET}")
    print(f"  > {BOLD}问答模型:{RESET} {BLUE}{Config.QA_MODEL}{RESET}")
    print(f"  > {BOLD}深度研究:{RESET} {GOLD}{Config.DEEP_RESEARCH_MODEL}{RESET}")
    print(f"  > {BOLD}API 代理:{RESET} {Config.OPENAI_API_BASE}")

    # 检查 API Key 状态（脱敏显示）
    api_key = Config.OPENAI_API_KEY
    key_status = f"{PINK}已配置{RESET} ({api_key[:8]}...{api_key[-4:]})" if api_key else f"\033[31m未配置\033[0m"
    print(f"  > {BOLD}API Key :{RESET} {key_status}")

    print(f"{'='*60}")

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
