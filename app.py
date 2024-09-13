from fastapi import FastAPI,UploadFile, File,Form,HTTPException,BackgroundTasks
from pydantic import BaseModel,HttpUrl
from dotenv import load_dotenv
from speech_2_text import SpeechSummarizer
from speech_2_text.yt_tool import download_audio_to_tempfile_async
from typing import Union
import tempfile
import os
import traceback

# 載入環境變數
load_dotenv()

# 創建 FastAPI 應用
app = FastAPI(openapi_tags=[{"name": "General"}])
summarizer = SpeechSummarizer()

@app.get("/",tags=["General"])
async def root():
    return {"message": "Response from FastAPI"}


class TranscriptionResponse(BaseModel):
    transcription: str
    summary: str


    

@app.post("/transcribe/file",tags=['Transcription'],response_model=TranscriptionResponse)
async def transcribe_file(audio_file: UploadFile = File(...)) -> TranscriptionResponse:
    """從音訊文件中提取文字並生成摘要"""
    return await perform_transcription(audio_file)

@app.post("/transcribe/url",tags=['Transcription'],response_model=TranscriptionResponse)
async def transcribe_url(url: HttpUrl = Form(...)) -> TranscriptionResponse:
    """從 YouTube 影片中提取文字並生成摘要"""
    return await perform_transcription(str(url))
    
async def perform_transcription(source: Union[UploadFile, HttpUrl]):
    temp_path = None
    try:
        # 建立臨時文件
        with tempfile.NamedTemporaryFile(delete=False,suffix='.mp3') as temp_file:
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
                
            transcription = await summarizer.transcribe_audio_async(temp_path)
            summary = summarizer.summarize_text(transcription['text'])
        
        return TranscriptionResponse(transcription=transcription['text'], summary=summary)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        # 使用完畢刪除臨時文件
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    import uvicorn
    
    #@ reload=True 會在代碼更改時自動重啟服務器，正式環境中應該設置為 False
    uvicorn.run(app, host="127.0.0.1", port=8000 ,reload=True)
