import argparse
import sys

from scraper_runner import process_and_notify
from callback_server import start_callback_server


def main():
    """
    解析命令行参数，并根据选择的模式启动对应的服务。
    """
    parser = argparse.ArgumentParser(
        description="钉钉通知机器人：支持主动推送和被动回调两种模式。",
        # 🚨 修正点 1: 在没有参数时自动打印帮助信息
        usage="%(prog)s <mode> [options]\n\n示例: python %(prog)s process\n       python %(prog)s callback"
    )
    
    parser.add_argument(
        'mode', 
        choices=['process', 'callback'], 
        help="选择启动模式: 'process' (主动推送) 或 'callback' (被动应答)"
    )

    # 🚨 修正点 2: 如果没有提供任何参数，打印帮助信息并退出
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()

    if args.mode == 'process':
        print("--- 启动主动推送任务 ---")
        process_and_notify()

    elif args.mode == 'callback':
        print("--- 启动回调服务器 ---")
        start_callback_server()


if __name__ == "__main__":
    main()