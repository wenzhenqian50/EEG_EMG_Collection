from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import random
import math

app = FastAPI()

# 提供前端 HTML 页面
@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# WebSocket 路由：用于实时传输数据
@app.websocket("/ws/signal")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("前端已连接到 WebSocket!")
    
    t = 0.0
    try:
        while True:
            # 【核心策略：批量发送】
            # 对于高频信号(如250Hz)，不要一个一个点发，网络开销太大。
            # 这里我们每次打包 10 个数据点发送。
            data_batch = []
            for _ in range(10):
                # 模拟生物电信号：基础正弦波 + 随机高频噪声
                signal_value = math.sin(t * 10) * 50 + random.uniform(-15, 15)
                data_batch.append(round(signal_value, 2))
                t += 0.01

            # 将数据打包成 JSON 发送给前端
            await websocket.send_json({"type": "eeg_data", "values": data_batch})
            
            # 模拟采样延时：每 0.05 秒发送一次 (即每秒发送 20 次，每次 10 个点 = 200Hz 刷新率)
            await asyncio.sleep(0.05)
            
    except WebSocketDisconnect:
        print("前端已断开连接。")