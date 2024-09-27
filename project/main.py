"""
                     -=*#####*+=:.                    
                  :*%%%%%%%%%%%%%%*-   .:---          
                :*%%%%%%%%%%%%%%%%%%%##*+=***.        
               +%%%%%%%%%%%%%%%%%%%%%%%*******.       
     :+%-    .#%%%%%%%%%%%%%%%%%%%%%%%%%#*****+       
  :+%%%%%.  .#%%%%%%%%%%%%%%%%%%%%%%%%%%%#*##*#       
 +%%%%%%%#-=%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#####       
 =%%%%%%%%%%%%**#%%%#***#%%%%%%%%%%%%%%%%%+:+#=       
 .%%%%%%%%%%#-..:#%++*+...:=*%%%%%%%%%%%%%%.          
  =%%%%%%%%%*.=+:#*.==:....=+-=#%%%%%%%%%%%-          
   %%%%%%%%%*::=-+::%*.....-*%:.#%%%%%%%%%%=          
  .-%%%%%%%%%=-..-=.=:::::%@....#%%%%%%%%%%+          
.::.=%%%%%%%%+...*%=..::.:+-...+%#++*%%%%%%%          
-. ..-%%%*+#%-..:%%+:-::::=+::.*+....=%%%%%%+     :+  
-...  .=-  =%-..=%#:.+  +@@+::...:==.=%%%%%%%#=-=#%%: 
::        -%%+..-++*##==#%#........:=%%%%%%%%%%%%%%%* 
  :.  .. .*%%%-..=======+*:...:+#*#%%%%%%%%%%%%%%%%%%.
   ::.   -***##=.:======-....-*%%%+=#%%%%%%%%%%%%%%%%*
     -=.+*****#---::--:...:-+%@@@*  -%%%%##%%%%%%%%*-.
     +%*******-..=:==----=*#%%%%%=  :---...=%@@%*-.   
     .=+*#**#+...+-+:...-*******+          :+=:       
          ...++++**#-...:#******+   .   ..::          
             +***++**+==**#******::...::.::           
            .#***++********#****%%- .                 
            :#*****#*********.:-=:                    
            :+##***#**####**#.                        
              +*+++*#**+++++**.                       
              .*+++**-:**++++**                       
     .-+***+-: =#*+#-.  =*****#=..-=++*++=.           
   .===++++++***+*+#:      *+*****+++++++=+=.         
  -*+++++++++++****#:      :#*****+++++++++**:        
  =************#####.       *###*#************        
    :=++**++=-:.-=-.         ..   :-==+++==-:         
"""

from fastapi import (
    FastAPI,UploadFile, 
    File,Form,
    HTTPException,
    APIRouter)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from pydantic import BaseModel,HttpUrl
from celery.result import AsyncResult
from dotenv import load_dotenv
from typing import Union,Any
from worker import perform_transcription
import traceback
import base64

# 載入環境變數
load_dotenv()

# 創建 FastAPI 應用
app = FastAPI(openapi_tags=[{"name": "General"}])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API Router
api_router = APIRouter(prefix="/api")


# 模板路由
# /transcribe/introduction -> 會渲染 transcribe/introduction.html
@app.get("/transcribe/introduction",tags=["Template"])
async def introduction_page(request: Request):
    return templates.TemplateResponse("transcribe/introduction.html", {"request": request})

# /transcribe/index -> 會渲染 transcribe/index.html
@app.get("/transcribe/index",tags=["Template"])
async def index_page(request: Request):
    return templates.TemplateResponse("transcribe/index.html", {"request": request})

# /transcribe/from-url -> 會渲染 transcribe/from_url.html
@app.get("/transcribe/from-url",tags=["Template"])
async def transcribe_from_url(request: Request):
    return templates.TemplateResponse("transcribe/from_url.html", {"request": request})

# /transcribe/from-local -> 會渲染 transcribe/local_audio.html
@app.get("/transcribe/from-local",tags=["Template"])
async def transcribe_from_local(request: Request):
    return templates.TemplateResponse("transcribe/local_audio.html", {"request": request})


class TranscriptionResponse(BaseModel):
    transcription: str
    summary: str

class CreateTask(BaseModel):
    message: str = "Task created successfully"
    task_id: str

class TaskStatus(BaseModel):
    message: str
    current: int

class TaskResponse(BaseModel):
    task_id: str
    task_status: str
    task_progress: Union[TaskStatus, None] = None
    task_result: Union[Any, None] = None



async def source_preprocess(source: Union[UploadFile, str]):
    """處理音訊源文件"""
    try:
        if hasattr(source, 'filename'):
            file_content = await source.read()
            # 將二進制內容轉換為 base64 編碼
            source = 'data:audio/mpeg;base64,'+base64.b64encode(file_content).decode('utf-8')
            
        # 調用 Celery 任務執行音訊轉錄
        return perform_transcription.delay(source)
                
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    
# API 路由
@api_router.get("/",tags=["General"])
async def api_root():
    return {"message": "Response from FastAPI"}

@api_router.post("/transcribe/file",tags=['Transcription'],response_model=CreateTask)
async def transcribe_file(audio_file: UploadFile = File(...)) -> CreateTask:
    """從音訊文件中提取文字並生成摘要"""
    task = await source_preprocess(audio_file)
    return CreateTask(task_id=task.id)
    

@api_router.post("/transcribe/url",tags=['Transcription'],response_model=CreateTask)
async def transcribe_url(url: HttpUrl = Form(...))  -> CreateTask:
    """從 YouTube 影片中提取文字並生成摘要"""
    task = await source_preprocess(url.__str__())
    return CreateTask(task_id=task.id)

@api_router.get("/task/{task_id}",tags=['General'],response_model=TaskResponse)
async def get_task_status(task_id: str):
    """檢查任務的狀態 分為PENDING、PROGRESS和SUCCESS"""
    
    task_result = AsyncResult(task_id)
    response = TaskResponse(
        task_id=task_id,
        task_status=task_result.status,
    )
    if task_result.state == 'PENDING':
        response.task_progress = TaskStatus(message='任務等待執行...', current=0)
    elif task_result.state == 'PROGRESS':
        response.task_progress = TaskStatus(
            message=task_result.info.get('message', '任務啟動中...'),
            current=task_result.info.get('current', 0)
        )
    elif task_result.ready() and task_result.successful():
        text, summary = task_result.get()
        response.task_result = TranscriptionResponse(transcription=text, summary=summary)
        
    return response


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
