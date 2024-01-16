from fastapi import FastAPI
import uvicorn
from threading import Thread

from BKVisionListener.states.computer import ComputerStates
from BKVisionListener.states import app

# 创建 FastAPI 应用
app_ = FastAPI()


# 定义路由
@app_.get("/app")
async def read_root():
    return app.process_iter()

@app_.get("/computer")
async def computer():
    return ComputerStates().__dict__()


class Server(Thread):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self):
        uvicorn.run(app_, host=self.ip, port=self.port)
