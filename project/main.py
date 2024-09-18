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

from fastapi import FastAPI,UploadFile, File,Form,BackgroundTasks,HTTPException
from pydantic import BaseModel,HttpUrl
from celery.result import AsyncResult
from dotenv import load_dotenv
from typing import Union,Any
from speech_2_text.yt_tool import download_audio_to_tempfile_async
from worker import perform_transcription
import tempfile
import os
import traceback

# 載入環境變數
load_dotenv()

# 創建 FastAPI 應用
app = FastAPI(openapi_tags=[{"name": "General"}])


@app.get("/",tags=["General"])
async def root():
    return {"message": "Response from FastAPI"}


class TranscriptionResponse(BaseModel):
    transcription: str
    summary: str

class CreateTask(BaseModel):
    message: str = "Task created successfully"
    task_id: str
    
class TaskResponse(BaseModel):
    task_id: str
    task_status: str
    task_progress: Union[int, None] = None
    task_result: Union[Any, None] = None



async def source_preprocess(source: Union[UploadFile, str]):
    temp_path = None
    try:
        # 建立臨時文件
        with tempfile.NamedTemporaryFile(delete=False,dir='./uploaded_files',suffix='.mp3') as temp_file:
            # 如果有上傳音訊檔，將音訊寫入臨時文件
            if hasattr(source, 'filename') and source.filename.endswith('.mp3'):
                audio = await source.read()
                temp_file.write(audio)
                
                # 確保所有數據都被寫入磁盤
                temp_file.flush()
                temp_path = temp_file.name
                
            # 如果提供了 YouTube URL，則從 YouTube 下載音訊
            elif isinstance(source, str):
                temp_path = await download_audio_to_tempfile_async(source,temp_file)

            # 如果提供了無效的源類型
            else:
                raise ValueError("Invalid source type")
        
        # 調用 Celery 任務執行音訊轉錄
        return perform_transcription.delay(temp_path)
                
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    

@app.post("/transcribe/file",tags=['Transcription'],response_model=CreateTask)
async def transcribe_file(audio_file: UploadFile = File(...)) -> CreateTask:
    """從音訊文件中提取文字並生成摘要"""
    task = await source_preprocess(audio_file)
    return CreateTask(task_id=task.id)
    

@app.post("/transcribe/url",tags=['Transcription'],response_model=CreateTask)
async def transcribe_url(url: HttpUrl = Form(...))  -> CreateTask:
    """從 YouTube 影片中提取文字並生成摘要"""
    task = await source_preprocess(url.__str__())
    return CreateTask(task_id=task.id)

@app.get("/task/{task_id}",tags=['General'],response_model=TaskResponse)
async def get_task_status(task_id: str):
    """檢查任務的狀態"""
    
    task_result = AsyncResult(task_id)
    response = TaskResponse(
        task_id=task_id,
        task_status=task_result.status,
    )
    if task_result.state == 'PROGRESS':
        response.task_progress = task_result.info
    elif task_result.ready() and task_result.successful():
        text, summary = task_result.get()
        response.task_result = TranscriptionResponse(transcription=text, summary=summary)
        
    return response
   

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
