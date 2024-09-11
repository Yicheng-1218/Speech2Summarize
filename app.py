from fastapi import FastAPI
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

# 創建 FastAPI 應用
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "歡迎使用我們的 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
