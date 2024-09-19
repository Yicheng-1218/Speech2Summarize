import os
from celery import Celery
from speech_2_text import SpeechSummarizer
from celery.utils.log import get_task_logger
import time

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")
celery.conf.update(
    # 設置時區
    timezone='Asia/Taipei',
    
    # 啟用 UTC
    enable_utc=True,
    
    # 任務相關設置
    task_time_limit=3600,  # 任務超時時間，單位為秒（這裡設置為1小時）
    task_soft_time_limit=3300,  # 軟超時時間，單位為秒（這裡設置為55分鐘）
    
    # 其他可能的配置...
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_backend='redis://localhost:6379/0',
)


logger = get_task_logger(__name__)
summarizer = SpeechSummarizer()


@celery.task(bind=True)
def test_progress(self) -> bool:
    for i in range(20):
        self.update_state(state='PROGRESS',meta={'current': i})
        time.sleep(1)
    return True


@celery.task(bind=True)
def perform_transcription(self, temp_path: str) -> tuple[str, str]:
    """執行音訊轉錄和總結

    Args:
        temp_path (str): 音訊檔案的臨時路徑

    Returns:
        tuple[str, str]: 轉錄後的文字和總結後的文字
    """
    try:
        # 確保文件存在
        if not os.path.exists(temp_path):
            raise FileNotFoundError(f"Audio file not found: {temp_path}")

        logger.info(f"\n\n開始執行轉錄任務，臨時文件路徑：{temp_path}\n\n")
        self.update_state(state='PROGRESS', meta={'current': 0})
        # # 註冊進度條回調函數
        summarizer.register_on_progress_callback(
            lambda current, total: 
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'message': '語音轉譯中...',
                        'current': round(current/total*95)
                        }
                ))
        
        #調用 SpeechSummarizer 進行音訊轉譯
        transcription = summarizer.transcribe_audio(temp_path)
        self.update_state(
            state='PROGRESS',
            meta={
                'message': '語音轉譯完成，正在生成摘要...',
                'current': 99
                })
        summary = summarizer.summarize_text(transcription['text'])
        
        return transcription['text'], summary
        
    except Exception as e:
        logger.error(f"Error in perform_transcription: {str(e)}")
        raise
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

