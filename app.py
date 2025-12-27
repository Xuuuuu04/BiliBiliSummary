"""
BiliBili 视频总结系统 - 主应用入口
重构版本：使用模块化路由架构
"""
from flask import Flask
from flask_cors import CORS
import os
import logging

# 初始化日志系统（必须在导入其他模块之前）
from src.backend.utils.logger import setup_logging, get_logger, get_log_dir, get_current_log_file
setup_logging(
    level=logging.INFO,
    console_level=logging.INFO,
    log_to_file=True
)

# 使用绝对路径确保在不同环境下都能找到前端资源
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(BASE_DIR, 'src', 'frontend')

# 创建 Flask 应用
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

# 配置 Flask 使用统一的日志格式
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)
for handler in log.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        ))

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

    # Flask 的重载机制：
    # 父进程（监控进程）启动时会创建子进程（实际应用进程）
    # 我们使用文件标记来确保只打印一次启动信息
    import tempfile

    # 创建临时标记文件
    startup_flag_file = tempfile.gettempdir() + '/bili_app_startup_flag'
    should_print_logo = not os.path.exists(startup_flag_file)

    if should_print_logo:
        # 创建标记文件
        with open(startup_flag_file, 'w') as f:
            f.write('started')

        # 终端颜色代码
        # B站品牌色：粉色 #FB7299 和 蓝色 #23ADE5
        BILI_PINK = '\033[38;2;251;114;153m'   # B站粉
        BILI_BLUE = '\033[38;2;35;173;229m'    # B站蓝
        CYAN = '\033[38;2;0;255;255m'
        WHITE = '\033[38;2;255;255;255m'
        GRADIENT = [
            '\033[38;2;251;114;153m',  # B站粉
            '\033[38;2;231;119;159m',
            '\033[38;2;211;124;165m',
            '\033[38;2;191;129;171m',
            '\033[38;2;171;134;177m',
            '\033[38;2;151;139;183m',
            '\033[38;2;131;144;189m',
            '\033[38;2;111;149;195m',
            '\033[38;2;91;154;201m',
            '\033[38;2;71;159;207m',
            '\033[38;2;51;164;213m',
            '\033[38;2;35;173;229m'    # B站蓝
        ]
        GOLD = '\033[38;5;220m'
        DIM = '\033[2m'
        RESET = '\033[0m'
        BOLD = '\033[1m'

        # 显示地址：如果是 0.0.0.0 则显示为 127.0.0.1
        display_host = '127.0.0.1' if Config.FLASK_HOST == '0.0.0.0' else Config.FLASK_HOST

        # 精致的 B 站小电视 + BILIBILI 渐变 Logo
        logo = f"""
{BILI_PINK}    ╭─────────────────────╮{RESET}
{BILI_PINK}   ╱                      ╲{RESET}
{BILI_PINK}  │   ╭─────────────╮   │{RESET}       {BOLD}{GRADIENT[0]}B{GRADIENT[1]}I{GRADIENT[2]}L{GRADIENT[3]}I{GRADIENT[4]}B{GRADIENT[5]}I{GRADIENT[6]}L{GRADIENT[7]}I{RESET}{BOLD}
{BILI_PINK}  │   │{WHITE}  ▄▄▄▄▄▄▄▄  {BILI_PINK}│   │{RESET}       {DIM}{WHITE}Video Analysis Helper{RESET}
{BILI_PINK}  │   │{WHITE}  █ ████ █  {BILI_PINK}│   │{RESET}
{BILI_PINK}  │   │{WHITE}  █ ▄▀ ▀█ █  {BILI_PINK}│   │{RESET}       {CYAN}▸{RESET} {BOLD}Author:{RESET} {WHITE}mumu_xsy{RESET}
{BILI_PINK}  │   │{WHITE}  █ ████ █  {BILI_PINK}│   │{RESET}       {CYAN}▸{RESET} {BOLD}GitHub:{RESET} {CYAN}https://gitcode.com/mumu_xsy/Bilibili_Analysis_Helper{RESET}
{BILI_PINK}  │   │{WHITE}  ▀▀▀▀▀▀▀▀  {BILI_PINK}│   │{RESET}
{BILI_PINK}  │   ╰─────────────╯   │{RESET}
{BILI_PINK}   ╲                      ╱{RESET}
{BILI_PINK}    ╰─────────────────────╯{RESET}
"""

        print(logo)
        print(f"{BOLD}🚀 BiliBili视频总结系统正在启动...{RESET}")
        print(f"{'='*60}")
        print(f"{BOLD}📡 运行配置:{RESET}")
        print(f"  > {BOLD}服务地址:{RESET} {BILI_BLUE}http://{display_host}:{Config.FLASK_PORT}{RESET}")
        print(f"  > {BOLD}调试模式:{RESET} {GOLD}{Config.FLASK_DEBUG}{RESET}")
        print(f"\n{BOLD}🤖 AI 引擎配置:{RESET}")
        print(f"  > {BOLD}基础模型:{RESET} {BILI_BLUE}{Config.OPENAI_MODEL}{RESET}")
        print(f"  > {BOLD}问答模型:{RESET} {BILI_BLUE}{Config.QA_MODEL}{RESET}")
        print(f"  > {BOLD}深度研究:{RESET} {GOLD}{Config.DEEP_RESEARCH_MODEL}{RESET}")
        print(f"  > {BOLD}API 代理:{RESET} {Config.OPENAI_API_BASE}")

        # 检查 API Key 状态（仅显示是否配置，不泄露任何字符）
        api_key_status = f"{BILI_PINK}✅ 已配置{RESET}" if Config.OPENAI_API_KEY else f"\033[31m❌ 未配置\033[0m"
        print(f"  > {BOLD}API Key :{RESET} {api_key_status}")
        print(f"\n{BOLD}📝 日志系统:{RESET}")
        print(f"  > {BOLD}日志目录:{RESET} {BILI_BLUE}{get_log_dir()}{RESET}")
        print(f"  > {BOLD}当前日志:{RESET} {BILI_BLUE}{get_current_log_file().name}{RESET}")
        print(f"{'='*60}")

    # 记录启动信息到日志（只在第一次打印时记录）
    logger = get_logger(__name__)
    if should_print_logo:
        logger.info("=" * 60)
        logger.info("应用启动")
        logger.info(f"Flask 服务: {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        logger.info(f"调试模式: {Config.FLASK_DEBUG}")
        logger.info(f"AI 模型: {Config.OPENAI_MODEL}")
        logger.info("=" * 60)

    try:
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    finally:
        # 清理标记文件
        if os.path.exists(startup_flag_file):
            try:
                os.remove(startup_flag_file)
            except:
                pass
