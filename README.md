# Build an automated EEG & EMG acquisition kit

**EMG Device:** Long Push The Botton -> Double Click The Botton

**Install Dependencies:** `pip install -r requirements.txt`  
**Start Web:** `uvicorn main:app --reload`

- Dataset 采集数据集
- EEG_Upper 脑电采集上位机
- EMG_Upper 肌电采集上位机
- static 存放网页程式
- auto_start_script 上位机自启脚本
- data_collection 采集和管理脑电和肌电数据
- get_classnn 获取窗口控件列表（辅助）


**Experiments Demo**
![alt text](/Images/exp_flow.png)