import asyncio
import os
import csv
import serial
import shutil
import time
from pywinauto import Application
from pywinauto import mouse

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
        self.serial_buffer_str = ""
        
        self._connect_serial()

    def _connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.01)
            print(f"[硬件] 已连接串口 {SERIAL_PORT}")
        except Exception as e:
            print(f"[警告] 无法连接串口 {SERIAL_PORT}: {e}")

    def trigger_eeg_app(self, cmd="start"):
        try:
            if cmd == "start":
                # 根据层级信息，"保存" 按钮的位置 (L1174, T543, R1244, B567)
                # 计算出中心点坐标: x = (1174+1244)/2 = 1209, y = (543+567)/2 = 555
                mouse.click(coords=(522, 180))
                print("[EEG上位机] 触发: 保存 (开始采集) - 使用固定坐标 (1209, 555) 点击")
            elif cmd == "stop":
                # 根据层级信息，"保存结束" 按钮的位置 (L1273, T543, R1337, B567)
                # 计算出中心点坐标: x = (1273+1337)/2 = 1305, y = (543+567)/2 = 555
                mouse.click(coords=(613, 180))
                print("[EEG上位机] 触发: 保存结束 (停止采集) - 使用固定坐标 (1305, 555) 点击")
        except Exception as e:
            print(f"[警告] 鼠标点击操作失败 ({cmd}): {e}")
    # def trigger_eeg_app(self, cmd="start"):
    #     try:
    #         # 改为使用 win32 模式寻找窗口，提升速度与兼容性
    #         app = Application(backend="win32").connect(path=EEG_EXE_PATH)
    #         win = app.top_window()
    #         if cmd == "start":
    #             # 根据 widget_tree.txt，触发保存（即开始记录数据）为 "保存" 按钮 
    #             win.child_window(title="保存").click()
    #             print("[EEG上位机] 触发: 保存 (开始采集)")
    #         elif cmd == "stop":
    #             # 根据 widget_tree.txt，触发停止记录数据为 "保存结束" 按钮 
    #             win.child_window(title="保存结束").click()
    #             print("[EEG上位机] 触发: 保存结束 (停止采集)")
    #     except Exception as e:
    #         print(f"[警告] pywinauto未能成功控制EEG上位机 ({cmd}): {e}")

    def start_trial(self, action, subject_name, round_num):
        """开始一次新的完整动作采集（前3个阶段）"""
        self.current_action = action
        self.buffer = {'Baseline': [], 'MotorPrep': [], 'Execution': []}
        
        # 定义 EMG 数据存储路径
        folder_path = os.path.join("Dataset", "EMG_Data", subject_name)
        os.makedirs(folder_path, exist_ok=True)
        self.current_filepath = os.path.join(folder_path, f'{subject_name}_{round_num}_{action}.csv')
        
        # 定义 EEG 数据存储目录路径
        eeg_folder_path = os.path.join("Dataset", "EEG_Data", subject_name)
        os.makedirs(eeg_folder_path, exist_ok=True)
        self.current_eeg_dest = os.path.join(eeg_folder_path, f'{subject_name}_{round_num}_{action}')
        
        if self.ser is None or not self.ser.is_open:
            print("\n[极度危险] 硬件串口尚未连接或已断开！本次采集将无法录入任何 EMG 数据，请检查设备！\n")
        
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

        # ============ EMG 数据落表保存 ============
        try:
            with open(self.current_filepath, 'w', encoding='utf-8', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7", "CH8", "PHASE"])
                
                for phase_key in ['Baseline', 'MotorPrep', 'Execution']:
                    for row in self.buffer[phase_key]:
                        writer.writerow(row + [phase_key])
                        
            print(f"[数据] 动作 {self.current_action} 采集完毕，已保存至 {self.current_filepath}")
        except Exception as e:
            print(f"[EMG写入错误] 无法保存数据表：{e}")

        # ============ EEG 自动迁移 ============
        # 等待1秒确保KSEEG软件生成并释放文件写入锁
        time.sleep(1)
        
        try:
            # 获取当前工程盘符 (如 "D:\") 并拼接KSEEG根目录
            drive_root = os.path.splitdrive(os.getcwd())[0] + os.sep
            kseeg_dir = os.path.join(drive_root, "KSEEG")
            
            if os.path.exists(kseeg_dir):
                # 找出 KSEEG 底下的所有子目录并按修改时间(mtime)获取最新的一个
                dirs = [os.path.join(kseeg_dir, d) for d in os.listdir(kseeg_dir) if os.path.isdir(os.path.join(kseeg_dir, d))]
                if dirs:
                    latest_dir = max(dirs, key=os.path.getmtime)
                    
                    # 移动到 Dataset/EEG_Data/{subject_name}/{subject_name}_{round_num}_{action} 中
                    if os.path.exists(self.current_eeg_dest):
                        shutil.rmtree(self.current_eeg_dest) # 直接擦除旧记录
                    
                    shutil.move(latest_dir, self.current_eeg_dest)
                    print(f"[EEG数据] 已将KSEEG新数据成功搬运并重命名为: {self.current_eeg_dest}")
                else:
                    print("[EEG警告] KSEEG 目录下未找到任何采集文件夹。")
            else:
                print(f"[EEG警告] 没有找到上位机的默认保存目录 {kseeg_dir}。")
        except Exception as e:
            print(f"[EEG移动失败] {e}")
            
    def abort_trial(self):
        """撤销操作：中止当前采集并丢弃数据"""
        self.is_collecting = False
        self.trigger_eeg_app("stop")
        self.buffer = {'Baseline': [], 'MotorPrep': [], 'Execution': []}
        print(f"[撤销] 动作 {self.current_action} 已被废弃。")

    async def run_loop(self):
        """异步持续从串口读数据并存入buffer"""
        while True:
            if self.is_collecting and self.ser and self.ser.is_open:
                try:
                    # 使用 in_waiting 读取可用字节，避免 readline() 被 timeout 截断
                    if self.ser.in_waiting > 0:
                        raw_data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                        self.serial_buffer_str += raw_data
                        
                        # 按换行符分割出所有的完整行
                        if '\n' in self.serial_buffer_str:
                            lines = self.serial_buffer_str.split('\n')
                            # 最后一个元素是不完整的行（可能是空字符串），保留到缓冲区等下次拼接
                            self.serial_buffer_str = lines.pop()
                            
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # .split()（不带参数）能自动过滤多余的空格或制表符
                                data = line.split()
                                if len(data) == 8:
                                    try:
                                        row_vals = [int(v) for v in data]
                                        if self.current_phase in self.buffer:
                                            self.buffer[self.current_phase].append(row_vals)
                                    except ValueError:
                                        pass # 忽略解析错误的数据
                                else:
                                    print(f"警告: 收到的数据通道数不正确(已丢弃): {data}")
                except Exception as e:
                    print(f"串口读取异常: {e}")
            else:
                # 没在采集时，为了防止缓冲区无限暴涨也可以清空一下脏数据
                if self.serial_buffer_str:
                    self.serial_buffer_str = ""
            await asyncio.sleep(0.005) # 高频轮询

collector = DataCollector()





