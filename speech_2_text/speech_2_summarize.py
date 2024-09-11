from dotenv import load_dotenv
import os
import whisper
import asyncio
import itertools
import json
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from torch import cuda
import warnings


warnings.filterwarnings("ignore")

ffmpeg_path = "./speech_2_text/ffmpeg/bin"
model_path = "./speech_2_text/models"

# 讀取環境變數
load_dotenv(override=True)
os.environ['PATH'] += os.pathsep + ffmpeg_path

# 讀取 Whisper 模型
whisper_model = whisper.load_model('base',download_root=model_path)

# LLM 模型
model=ChatAnthropic(model=os.getenv('ANTHROPIC_LLM_MODEL'),temperature=0)
prompt = PromptTemplate.from_template("""
    請總結<text>中的內容，並遵循以下步驟：
    1、將內容轉換成繁體中文。
    2、想一個最適合的標題。
    3、將內容中的錯字進行修正。
    4、將內容整合成段落格式，並增加易讀性。
    5、一個段落之前加上一個小標題，並在小標題後加上冒號。
    5、除了正文的內容外，不要說明任何其他事情。
    
    輸出請匹配以下格式
    ```
    標題:
    <title>
    內容總結:
    <summary>
    ```
    
    <text>
    {text}
    </text>
    """)
chain=prompt|model|StrOutputParser()


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
    filename = os.path.basename(audio_path)
    print(f"開始轉譯 {filename}")
    async def show_loading():
        for frame in itertools.cycle(['.  ', '.. ', '...']):
            print(f'\rLoading {frame}', end='', flush=True)
            await asyncio.sleep(1)
    loading_task = asyncio.create_task(show_loading())

    # 使用 asyncio.to_thread 將同步的 Whisper 轉譯操作轉成異步
    task = asyncio.to_thread(
        whisper_model.transcribe,
        audio_path,
        initial_prompt='轉譯成繁體中文',
        language=language,
        fp16=cuda.is_available())

    # 當轉譯完成後停止 loading 動畫
    result = await task
    loading_task.cancel()  # 取消動畫

    print('\r轉譯完成!')
    if save_path:
        json.dump(result, open(save_path+filename.replace('.mp3','.json'), 'w',encoding='utf-8'), ensure_ascii=False)
    return result



async def main():
    media_path = './speech_2_text/media/'
    filename = input('請輸入音訊檔名稱 (包含副檔名)：')
    cache_path = media_path+filename.replace('.mp3','.json')
    # 如果有 cache 就直接讀取 cache
    if os.path.exists(cache_path):
        print('找到 cache，直接讀取')
        result = json.load(open(cache_path,'r',encoding='utf-8'))
    else:
        # 若無 cache 則進行轉譯
        result = await transcribe_audio(
            media_path+filename, 
            language='zh',
            save_path='./speech_2_text/media/'
            )
    
    summarize = chain.invoke({'text':result['text']})
    print(summarize)


if __name__ == '__main__':
    asyncio.run(main())
    

