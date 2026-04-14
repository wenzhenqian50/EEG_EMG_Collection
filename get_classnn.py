from pywinauto import Application

# 连接到已经打开的软件进程
# app = Application(backend="win32").connect(path="eegsdk_demo.exe")
app = Application(backend="uia").connect(path="emgsdk_demo.exe")

# 获取主窗口
main_win = app.top_window()

# 打印窗口里的所有层级和控件信息
# main_win.print_control_identifiers()
# 打印到指定文件中
main_win.print_control_identifiers(filename="widget_tree.txt")