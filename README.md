# Build an automated EEG & EMG acquisition kit

**EMG Device:** Long Push The Botton -> Double Click The Botton
**EEG Device:** Long Push The Botton -> Blinking Blue Light

**Python Version:** `3.11.15`
**Install Dependencies:** `pip install -r requirements.txt`  
**Start Web:** `uvicorn main:app --reload`

- Dataset 采集数据集
- EEG_Upper 脑电采集上位机
- EMG_Upper 肌电采集上位机
- static 存放网页程式
- auto_start_script 上位机自启脚本
- data_collection 采集和管理脑电和肌电数据
- get_classnn 获取窗口控件列表（辅助）

# Process
1. 将此工程放在电脑D盘中
2. 将EMG&EEG设备连接到电脑
3. 运行`auto_start_script.exe`启动EMG&EEG配套上位机
4. EEG上位机连接到EEG设备后最小化
5. EMG上位机连接到EMG设备后查看使用的端口号后将串口连接断开
6. 将`data_collection.py`中的`SERIAL_PORT`修改为对应端口号
7. 终端运行`conda activate eeg_emg`开启虚拟环境
8. 终端运行`uvicorn main:app --reload`开始采集
   1. 开启前需先输入采集者姓名
   2. 如果动作做错请点击**撤销**键
9.  采集完成后可运行`python verificaton_dataset.py`检查数据有效性


**Experiments Demo**
![alt text](/Images/exp_flow.png)