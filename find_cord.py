import time
import win32api

print("请将鼠标移动到需要点击的按钮上，2秒更新一次坐标，按 Ctrl+C 退出...")
try:
    while True:
        x, y = win32api.GetCursorPos()
        print(f"当前鼠标绝对坐标: ({x}, {y})")
        time.sleep(2)
except KeyboardInterrupt:
    print("退出获取")