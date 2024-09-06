import dotenv
import os
import whisper
import asyncio
from pathlib import Path
import itertools
import pickle
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


ffmpeg_path = "./speech_2_text/ffmpeg/bin"
model_path = "./speech_2_text/models"

# 讀取環境變數
dotenv.load_dotenv(override=True)
os.environ['PATH'] += os.pathsep + ffmpeg_path

# 讀取 Whisper 模型
whisper_model = whisper.load_model('base',download_root=model_path)

# LLM 模型
model=ChatOpenAI(model='gpt-3.5-turbo',temperature=0.5)
prompt = PromptTemplate.from_template("""
    Please summarize the following text between ``` and respond in zh-TW. 
    Only summary is needed dont't ask any questions.
    
    ```
    {text}
    ```
    """)
chain=prompt|model


# 異步執行 Whisper 的轉譯
async def transcribe_audio(audio_path, language='zh',save_path=None):
    """使用 Whisper 模型將音訊檔轉譯成文字

    Args:
        audio_path (str): 音訊檔路徑
        language (str, optional): 猜測模型輸入之語言 Defaults to 'zh'.
        save_path (str, optional): 快取儲存位置 Defaults to None.

    Returns:
        dict[str, str | list]: 轉譯結果
    """
    assert os.path.exists(audio_path), f"Audio file not found: {audio_path}"
    print(f"開始轉譯 {audio_path}...")

    async def show_loading():
        for frame in itertools.cycle(['.  ', '.. ', '...']):
            print(f'\rLoading {frame}', end='', flush=True)
            await asyncio.sleep(1) 
            
    loading_task = asyncio.create_task(show_loading())

    # 使用 asyncio.to_thread 將同步的 Whisper 轉譯操作轉成異步
    task = asyncio.to_thread(whisper_model.transcribe, audio_path, language=language)

    # 當轉譯完成後停止 loading 動畫
    result = await task
    loading_task.cancel()  # 取消動畫

    print('\r轉譯完成!')
    if save_path:
        pickle.dump(result, open(save_path+'cache.pkl', 'wb'))
    return result



async def main():
        media_path = './speech_2_text/media/'
        filename = 'stock_news.mp3'
        
        # 如果有 cache 就直接讀取 cache
        if Path(media_path+'cache.pkl').exists():
            print('找到 cache，直接讀取')
            result = pickle.load(open(media_path+'cache.pkl','rb'))
        else:
            # 若無 cache 則進行轉譯
            result = await transcribe_audio(
                media_path+filename, 
                language='zh',
                save_path='./speech_2_text/media/'
                )
        
        summarize = chain.invoke({'text':result['text']})
        print(summarize.content)


if __name__ == '__main__':
    asyncio.run(main())
    

