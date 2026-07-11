"""CPU 和内存占用监控脚本。

每分钟采样一次，输出到控制台。当 CPU 占用低于阈值时，蜂鸣提醒用户并退出。
适用于 Nuitka 编译等长时间高 CPU 占用的任务——编译结束后 CPU 下降，自动提醒。

用法：
    python monitor_cpu.py [--threshold 50] [--interval 60]

参数：
    --threshold   CPU 占用阈值（百分比），低于此值触发提醒，默认 50
    --interval    采样间隔（秒），默认 60
"""

import psutil
import time
import argparse


def _beep():
    """蜂鸣提醒，优先用 Windows Beep，fallback 到控制台响铃"""
    try:
        import winsound
        winsound.Beep(800, 300)
        time.sleep(0.2)
        winsound.Beep(800, 300)
        time.sleep(0.2)
        winsound.Beep(800, 300)
    except (ImportError, RuntimeError):
        for _ in range(3):
            print("\a", end="", flush=True)
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="CPU 和内存占用监控")
    parser.add_argument("--threshold", type=float, default=50,
                        help="CPU 占用阈值（百分比），低于此值触发提醒，默认 50")
    parser.add_argument("--interval", type=int, default=60,
                        help="采样间隔（秒），默认 60")
    args = parser.parse_args()

    interval = max(10, args.interval)
    threshold = max(1, min(99, args.threshold))

    print(f"监控已启动: 间隔={interval}s, CPU阈值={threshold}%", flush=True)
    print(f"{'时间':<8} | {'CPU':>8} | {'内存':>10} | {'状态'}", flush=True)
    print("-" * 50, flush=True)

    # 首次采样用于初始化 psutil 内部计数器（结果不准，丢弃）
    psutil.cpu_percent(interval=1)

    try:
        while True:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            ts = time.strftime("%H:%M:%S")

            status = "运行中" if cpu >= threshold else "↓ 低于阈值"
            print(f"{ts:<8} | {cpu:>7.1f}% | {mem_pct:>9.1f}% | {status}", flush=True)

            if cpu < threshold:
                _beep()
                print("\n编译任务已结束（CPU 低于阈值），监控退出。", flush=True)
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n监控被用户中断。", flush=True)


if __name__ == "__main__":
    main()
