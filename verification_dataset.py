import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    emg_dir = os.path.join(root_dir, "Dataset", "EMG_Data")
    eeg_dir = os.path.join(root_dir, "Dataset", "EEG_Data")
    
    if not os.path.exists(emg_dir) or not os.path.exists(eeg_dir):
        print("未找到 Dataset 中的 EEG_Data 和 EMG_Data 目录，无法进行可视化。")
        return

    # 递归查找所有的 EMG 数据文件
    emg_pattern = os.path.join(emg_dir, "**", "*.csv")
    emg_files = glob.glob(emg_pattern, recursive=True)
    
    paired_data = []
    
    for emg_file in emg_files:
        # 解析受试者和文件名（如：Dataset/EMG_Data/wzq/wzq_1_8.csv）
        subject_dir = os.path.basename(os.path.dirname(emg_file))
        filename = os.path.basename(emg_file)
        
        # 排除可能是临时文件或是目录的可能性
        if not os.path.isfile(emg_file):
            continue
            
        trial_id, ext = os.path.splitext(filename)
        
        # 对应构造出预期的 EEG 文件路径
        eeg_file = os.path.join(eeg_dir, subject_dir, trial_id, "rawData.csv")
        
        if os.path.exists(eeg_file):
            paired_data.append((trial_id, emg_file, eeg_file))
            
    if not paired_data:
        print("未找到任何成对的 EEG 与 EMG 数据，请检查数据集是否匹配！")
        return
        
    print(f"找到 {len(paired_data)} 对实验数据组。在独立窗口中浏览，关闭当前弹窗后自动展示下一张图片。")

    for trial_id, emg_path, eeg_path in paired_data:
        try:
            emg_df = pd.read_csv(emg_path)
            eeg_df = pd.read_csv(eeg_path)
        except Exception as e:
            print(f"[{trial_id}] 表格读取失败: {e}")
            continue

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle(f"Trial ID: {trial_id} - Sync Visualization", fontsize=16)

        # ---------------- EEG 可视化 ----------------
        if 'channel_1' in eeg_df.columns and 'channel_2' in eeg_df.columns:
            ax1.plot(eeg_df.index, eeg_df['channel_1'], label='Channel 1 (EEG)', alpha=0.8)
            ax1.plot(eeg_df.index, eeg_df['channel_2'], label='Channel 2 (EEG)', alpha=0.8)
        else:
            for col in eeg_df.columns:
                ax1.plot(eeg_df.index, eeg_df[col], label=f"{col} (EEG)", alpha=0.8)
                
        ax1.set_title("EEG Signal")
        ax1.set_ylabel("Amplitude")
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle='--', alpha=0.5)

        # ---------------- EMG 可视化 ----------------
        emg_channels = [col for col in emg_df.columns if col.startswith('CH')]
        for ch in emg_channels:
            ax2.plot(emg_df.index, emg_df[ch], label=f"{ch} (EMG)", alpha=0.7)
            
        ax2.set_title("EMG Signal")
        ax2.set_ylabel("Amplitude")
        ax2.set_xlabel("Sample Index")
        ax2.legend(loc='upper right', ncol=4, fontsize='small')
        ax2.grid(True, linestyle='--', alpha=0.5)

        # ---------------- 阶段锚点竖线对齐 ----------------
        if 'PHASE' in emg_df.columns:
            phases = emg_df['PHASE'].values
            
            # 使用差分/移位来定位变化索引
            phase_changes = []
            if len(phases) > 0:
                current_phase = phases[0]
                phase_changes.append((0, current_phase))
                
                for i in range(1, len(phases)):
                    if phases[i] != current_phase:
                        current_phase = phases[i]
                        phase_changes.append((i, current_phase))
            
            # 由于EEG与EMG可能采样率不一致（如 500Hz 和 1000Hz）
            # 我们通过数据长度的比例将 EMG 中的相位截断点映射回 EEG 子图中
            ratio = len(eeg_df) / max(1, len(emg_df))
            
            for idx, phase_name in phase_changes:
                # 给 EMG 子图追加红线标记
                ax2.axvline(x=idx, color='r', linestyle='--', linewidth=2, alpha=0.7)
                y_pos_emg = ax2.get_ylim()[1]
                ax2.text(idx, y_pos_emg, f' {phase_name} ', color='red', 
                         rotation=90, verticalalignment='top', fontsize=10,
                         bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
                
                # 给 EEG 子图按照比例追加标记
                eeg_idx = int(idx * ratio)
                ax1.axvline(x=eeg_idx, color='r', linestyle='--', linewidth=2, alpha=0.7)
                y_pos_eeg = ax1.get_ylim()[1]
                ax1.text(eeg_idx, y_pos_eeg, f' {phase_name} ', color='red', 
                         rotation=90, verticalalignment='top', fontsize=10,
                         bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
