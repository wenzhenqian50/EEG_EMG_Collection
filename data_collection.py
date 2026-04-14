import asyncio
import os
import csv
import serial
from pywinauto import Application

# ================= Configuration ==================
LOG_NAME = "wzq"
IDX_COUNTER = 1
# 串口配置
SERIAL_PORT = "COM3"
SERIAL_BAUD = 115200
# EEG上位机窗口名
EEG_EXE_PATH = "eegsdk_demo.exe"
# ==================================================

class DataCollector:
    def __init__(self):
        self.is_collecting = False
        self.current_action = None
        self.current_phase = "IDLE"  # "Baseline", "MotorPrep", "Execution"
        
        self.ser = None
        self.buffer = {
            'Baseline': [],
            'MotorPrep': [],
            'Execution': []
        }
        
        self._connect_serial()

    def _connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.01)
            print(f"[硬件] 已连接串口 {SERIAL_PORT}")
        except Exception as e:
            print(f"[警告] 无法连接串口 {SERIAL_PORT}: {e}")

    def trigger_eeg_app(self, cmd="start"):
        try:
            # 改为使用 win32 模式寻找窗口，提升速度与兼容性
            app = Application(backend="win32").connect(path=EEG_EXE_PATH)
            win = app.top_window()
            if cmd == "start":
                # 根据 widget_tree.txt，触发保存（即开始记录数据）为 "保存" 按钮 
                win.child_window(title="保存").click()
                print("[EEG上位机] 触发: 保存 (开始采集)")
            elif cmd == "stop":
                # 根据 widget_tree.txt，触发停止记录数据为 "保存结束" 按钮 
                win.child_window(title="保存结束").click()
                print("[EEG上位机] 触发: 保存结束 (停止采集)")
        except Exception as e:
            print(f"[警告] pywinauto未能成功控制EEG上位机 ({cmd}): {e}")

    def start_trial(self, action, subject_name, round_num):
        """开始一次新的完整动作采集（前3个阶段）"""
        self.current_action = action
        self.buffer = {'Baseline': [], 'MotorPrep': [], 'Execution': []}
        
        folder_path = os.path.join("Dataset", "EMG_Data", subject_name)
        os.makedirs(folder_path, exist_ok=True)
        self.current_filepath = os.path.join(folder_path, f'{subject_name}_{round_num}_{action}.csv')
        
        self.trigger_eeg_app("start")
        self.is_collecting = True

    def set_phase(self, phase_name):
        """设置当前的打标阶段"""
        self.current_phase = phase_name

    def stop_and_save_trial(self):
        """当前动作完成，保存数据到CSV"""
        self.is_collecting = False
        self.trigger_eeg_app("stop")
        
        if not self.current_action:
            return

        # 整理并将数据写入 CSV
        # 写入格式: 8个通道数据，外加一列 Phase 标签
        try:
            with open(self.current_filepath, 'w', encoding='utf-8', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7", "CH8", "PHASE"])
                
                for phase_key in ['Baseline', 'MotorPrep', 'Execution']:
                    for row in self.buffer[phase_key]:
                        writer.writerow(row + [phase_key])
                        
            print(f"[数据] 动作 {self.current_action} 采集完毕，已保存至 {self.current_filepath}")
        except Exception as e:
            print(f"[写入错误] 无法保存数据表：{e}")
            
    def abort_trial(self):
        """撤销操作：中止当前采集并丢弃数据"""
        self.is_collecting = False
        self.trigger_eeg_app("stop")
        self.buffer = {'Baseline': [], 'MotorPrep': [], 'Execution': []}
        print(f"[撤销] 动作 {self.current_action} 已被废弃。")

    async def run_loop(self):
        """异步持续从串口读数据并存入buffer"""
        while True:
            if self.is_collecting and self.ser and self.ser.isOpen():
                try:
                    # 读取可用的所有行
                    while self.ser.in_waiting > 0:
                        line = self.ser.readline()
                        if line:
                            data = line.decode('utf-8', errors='ignore').rstrip().split(" ")
                            if len(data) == 8:
                                try:
                                    row_vals = [int(x) for x in data]
                                    if self.current_phase in self.buffer:
                                        self.buffer[self.current_phase].append(row_vals)
                                except ValueError:
                                    pass # 忽略解析错误的数据
                except Exception as e:
                    print(f"串口读取异常: {e}")
            await asyncio.sleep(0.005) # 高频轮询

collector = DataCollector()

# import serial
# import csv
# import os
# import random
# import time
# import pyautogui

# ##调用时输入x,y的坐标
# def click_screen(x, y, button='left'):
#     pyautogui.moveTo(x, y)
#     pyautogui.mouseDown()
#     time.sleep(0.2)
#     pyautogui.mouseUp()
#     print(f'已经在坐标({x}，{y})处点击,开始采集脑电数据')


# def save_emg_eeg(log_name, idx_counter, action, x, y, x1, y1, out_range, threshold = 2000):
#     ##读取串口数据
#     ser = serial.Serial('COM3', 115200)
#     folder_path = f'saved_files_{log_name}_{idx_counter}'
#     os.makedirs(folder_path, exist_ok=True)
#     data_csv = open(f'{folder_path}/{log_name}_{idx_counter}_{action}.csv', 'w', encoding='utf-8', newline="")
#     data_csv_writer = csv.writer(data_csv)

#     data0_cu = []
#     data1_cu = []
#     data2_cu = []
#     data3_cu = []
#     data4_cu = []
#     data5_cu = []
#     data6_cu = []
#     data7_cu = []

#     threshold_reached = False  # 阈值触发标志

#     print(f"----- 开始 {action} 动作 -----")

#     while True:
#         data = str(ser.readline().decode('utf-8').rstrip()).split(" ")

#         # 确保数据长度正确
#         if len(data) != 8:
#             print(f"警告: 收到的数据格式不正确: {data}")
#             continue

#         d0 = int(data[0])
#         d1 = int(data[1])
#         d2 = int(data[2])
#         d3 = int(data[3])
#         d4 = int(data[4])
#         d5 = int(data[5])
#         d6 = int(data[6])
#         d7 = int(data[7])

#         # 如果未触发阈值，则检查是否有通道达到阈值
#         if not threshold_reached:
#             if any(abs(value - threshold) >= out_range for value in [d0, d1, d2, d3, d4, d5, d6, d7]):
#                 threshold_reached = True
#                 # 点击屏幕eeg脑电开始采集按钮
#                 click_screen(x, y)

#         # 如果已触发阈值，则收集数据
#         if threshold_reached:
#             data0_cu.append(d0)
#             data1_cu.append(d1)
#             data2_cu.append(d2)
#             data3_cu.append(d3)
#             data4_cu.append(d4)
#             data5_cu.append(d5)
#             data6_cu.append(d6)
#             data7_cu.append(d7)

#             # 收集满80个数据点后退出循环
#             if len(data0_cu) == 80:
#                 break

#     # 将数据写入CSV文件
#     data_csv_writer.writerow(data0_cu)
#     data_csv_writer.writerow(data1_cu)
#     data_csv_writer.writerow(data2_cu)
#     data_csv_writer.writerow(data3_cu)
#     data_csv_writer.writerow(data4_cu)
#     data_csv_writer.writerow(data5_cu)
#     data_csv_writer.writerow(data6_cu)
#     data_csv_writer.writerow(data7_cu)

#     data_csv.close()

#     print(f"----- 完成  {action}  动作 -----\n")

#     print('--  休息3s  --')
#     time.sleep(2)
#     # 点击屏幕eeg脑电结束采集按钮
#     click_screen(x1, y1)


# if __name__ == '__main__':
#     log_name = 'wzq'  # 人名，文件夹(手动更改)
#     idx_counter = 1 #记录程序运行了多少次(手动更改)
#     threshold_value = 2020  # 基准值
#     out_range = 250 # 超出的阈值


#     action_list = ['wj', 'down', 'left', 'right', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'wq', 'ok']
#     random_actions = random.sample(action_list, len(action_list))  # 随机打乱 16 个动作

#     x = 490
#     y = 185  # 脑电开始采集按钮在电脑屏幕上的坐标(手动更改)

#     x1 = 580
#     y1 = 185  # 脑电结束采集按钮在电脑屏幕上的坐标(手动更改)



#     action_index = []     #记录随机打乱的动作顺序
#     # 总数据创建
#     for action in random_actions:
#         action_index.append(action)
#         save_emg_eeg(log_name, idx_counter, action, x, y, x1, y1,out_range,threshold_value)
#     print(action_index)





