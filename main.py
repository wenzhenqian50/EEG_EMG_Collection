import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import contextlib

# 引入我们改造后的采集模块
from data_collection import collector

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动硬件读取循环
    task = asyncio.create_task(collector.run_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# 动作列表
action_list = ['wj', 'down', 'left', 'right', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'wq', 'ok']

class ExperimentState:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        
        self.action_queue = random.sample(action_list, len(action_list))
        self.current_action = None
        
        self.phase_name = "等待启动"
        self.countdown = 0.0
        
        self.active_task = None
        self.undo_flag = False
        self.subject_name = ""
        self.round_num = 1

state = ExperimentState()

# ----- 网络接口 -----

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

class CommandRequest(BaseModel):
    command: str
    subject_name: str = ""

@app.post("/api/control")
async def control_experiment(req: CommandRequest):
    cmd = req.command
    if cmd == "start":
        if not state.is_running:
            state.is_running = True
            state.is_paused = False
            state.subject_name = req.subject_name or "Unknown"
            
            # 计算轮数
            import os
            folder_path = os.path.join("Dataset", "EMG_Data", state.subject_name)
            max_round = 0
            if os.path.exists(folder_path):
                for f in os.listdir(folder_path):
                    if f.endswith(".csv") and f.startswith(state.subject_name + "_"):
                        parts = f.split("_")
                        if len(parts) >= 3:
                            try:
                                r = int(parts[1])
                                max_round = max(max_round, r)
                            except ValueError:
                                pass
            state.round_num = max_round + 1
            
            state.action_queue = random.sample(action_list, len(action_list))
            state.active_task = asyncio.create_task(experiment_loop())
        elif state.is_paused:
            state.is_paused = False
    elif cmd == "pause":
        if state.is_running:
            state.is_paused = True
    elif cmd == "undo":
        if state.is_running and state.current_action:
            state.undo_flag = True
    
    return {"status": "ok", "message": f"Command '{cmd}' processed."}

@app.websocket("/ws/state")
async def websocket_state(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "phase_name": "暂停中" if state.is_paused else state.phase_name,
                "current_action": state.current_action,
                "countdown": state.countdown
            })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass

# ----- 实验状态机循环 -----

async def run_phase(phase_name: str, duration: float, collector_phase_key: str = None):
    """通用等待一段带倒计时的阶段，处理暂停与撤销打断"""
    state.phase_name = phase_name
    if collector_phase_key:
        collector.set_phase(collector_phase_key)
        
    state.countdown = duration
    
    while state.countdown > 0:
        if state.undo_flag:
            return False # 撤销打断
            
        if not state.is_paused:
            state.countdown -= 0.1
            
        await asyncio.sleep(0.1)
        
    return True

async def handle_undo():
    """撤销当前动作，放回队列"""
    print(f"[撤销] 已打断，废弃当前动作数据: {state.current_action}")
    collector.abort_trial()
    
    # 重新放回队列并打乱
    state.action_queue.append(state.current_action)
    random.shuffle(state.action_queue)
    
    state.undo_flag = False
    state.current_action = None

async def experiment_loop():
    print("实验主循环已启动")
    
    while state.action_queue and state.is_running:
        if state.is_paused:
            await asyncio.sleep(0.5)
            continue
            
        # 开始新的一轮
        state.current_action = state.action_queue.pop(0)
        state.undo_flag = False
        
        print(f"\n--- 抽取动作: {state.current_action} 剩余: {len(state.action_queue)} ---")
        
        # 1. 触发准备收集
        collector.start_trial(state.current_action, state.subject_name, state.round_num)

        # 2. 准备阶段：基线（持续3s）
        if not await run_phase("准备阶段", 3.0, "Baseline"):
            await handle_undo()
            continue

        # 3. 运动准备阶段：看屏幕但是不做（持续2s）
        if not await run_phase("运动准备阶段", 2.0, "MotorPrep"):
            await handle_undo()
            continue

        # 4. 运动执行阶段：开始动作（持续3s）
        if not await run_phase("运动执行阶段", 3.0, "Execution"):
            await handle_undo()
            continue

        # 正常完成，停止采集并落表保存
        collector.stop_and_save_trial()

        # 5. 放松阶段（持续4s，不收集）
        if not await run_phase("放松阶段", 4.0, None):
            await handle_undo()
            continue

    if not state.action_queue:
        state.phase_name = "实验结束，任务完成！"
        state.current_action = None
        state.countdown = 0
        state.is_running = False
        print("所有队列动作采集完毕。")
