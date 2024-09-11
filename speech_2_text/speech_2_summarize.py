from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from torch import cuda
from dotenv import load_dotenv
import os
import whisper
import json
import warnings
import yt_tool
import threading


warnings.filterwarnings("ignore")

ffmpeg_path = "./speech_2_text/ffmpeg/bin"
model_path = "./speech_2_text/models"

# 讀取環境變數
load_dotenv(override=True)
os.environ['PATH'] += os.pathsep + ffmpeg_path

# 載入 Whisper 模型
whisper_model = whisper.load_model('base',download_root=model_path)

# 建立 LLM 模型
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
    
    標題:
    <title>
    內容總結:
    <summary>
    
    
    <text>
    {text}
    </text>
    """)

# 建立語言模型鏈
chain = prompt|model|StrOutputParser()


# 執行 Whisper 轉譯
def transcribe_audio(audio_path, language='zh',save_path=None):
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
    print(f"\r\n\n開始轉譯 {filename} ...")
    
    
    result = whisper_model.transcribe(
        audio_path,
        verbose=False,
        initial_prompt='轉譯成繁體中文',
        language=language,
        fp16=cuda.is_available())

    print('轉譯完成!\n')
    if save_path:
        threading.Thread(target=
            lambda:
                json.dump(
                    result, 
                    open(save_path+filename.replace('.mp3','.json'), 'w', encoding='utf-8'),
                    ensure_ascii=False)
            ).start()
    return result




if __name__ == '__main__':
    mode_choice = input('使用本地音檔請輸入1 , 使用 YouTube 影片請輸入2：')
    media_path = './speech_2_text/media/'
    
    if mode_choice == '1':
        filename = input('請輸入音訊檔名稱 (包含副檔名)：')
    elif mode_choice == '2':
        url = input('請輸入 YouTube 影片網址：')
        print('\r\n開始下載音訊檔...')
        filename = os.path.basename(yt_tool.download_audio(url, media_path))
                
    cache_path = media_path+filename.replace('.mp3','.json')
        
    # 如果有 cache 就直接讀取 cache
    if os.path.exists(cache_path):
        print('找到 cache，直接讀取')
        result = json.load(open(cache_path,'r',encoding='utf-8'))
    else:
        # 若無 cache 則進行轉譯
        result = transcribe_audio(
            media_path+filename, 
            language='zh',
            save_path='./speech_2_text/media/'
            )
            
    summarize = chain.invoke({'text':result['text']})
    print(summarize) 
    

