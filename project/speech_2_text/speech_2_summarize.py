import os
import sys
import json
import warnings
import asyncio
from typing import Optional,Callable,Any
import tqdm
import whisper
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from torch import cuda
from dotenv import load_dotenv

try:
    import yt_tool
except ImportError:
    from . import yt_tool

warnings.filterwarnings("ignore")


load_dotenv(override=True)
ffmpeg_path = os.getenv('FFMPEG_PATH')
model_path = os.getenv('WHISPER_MODEL_PATH')
media_path = os.getenv('MEDIA_PATH')
os.environ['PATH'] += os.pathsep + ffmpeg_path


class _CustomProgressBar(tqdm.tqdm):
    callback = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current = self.n
        
    @staticmethod
    def set_callback(callback):
        _CustomProgressBar.callback = staticmethod(callback)
    
    def update(self, n):
        super().update(n)
        self._current += n
        if self.callback:
            self.callback(self._current, self.total)
            



class SpeechSummarizer:
    """語音轉文字並總結文字
           
        Args:
            on_progress (func, optional): 設置進度條回調函數，用於更新進度條。 Defaults to None.
            
            #todo 自訂選擇LLM模型
            
        特別注意該on_progress的callback函數的參數必須是兩個，分別是當前進度和總進度
        
        Instantiate:
        .. code-block:: python

            from speech_2_text import SpeechSummarizer

            def your_callback_function(current, total):
                do_something
                
            summarizer = SpeechSummarizer(on_progress=your_callback_function)

        """
    def __init__(self,on_progress=None):
        # 載入模型
        #  ! 要是在init階段載入模型，會導致在celery中無法正常transcribe ...相當奇怪
        # self.whisper_model = whisper.load_model('base', download_root=model_path)
        self.llm_model = ChatAnthropic(model=os.getenv('ANTHROPIC_LLM_MODEL'), temperature=0)

        self._setup_prompt_chain()
        self.on_progress = on_progress
        
        
    def register_on_progress_callback(self, func: Callable[[int, int], None]):
        """Register a progress callback function post initialization.

        :param callable func:
            A callback function that takes ``current`` and ``total`` as parameters.

        :rtype: None

        """
        self.on_progress = func
    
    
    def _setup_prompt_chain(self):
        prompt = PromptTemplate.from_template("""
            Please summarize the content in <text> and follow the steps starting with ####:
                #### 1. Always respond in zh-tw.
                #### 2. Correct any typos in the content.
                #### 3. Do not provide any information other than the main text content.
                #### 4. Summarize the content according to the Care Management Assessment Scale\
                        (ADLs, IADLs, Special Complex Care Needs, Home Environment and Social Participation,\
                        Emotional and Behavioral Patterns, Primary Caregiver Burden,\
                        Primary Caregiver Work and Support).
                #### 5. Ensure that HTML <br> tags are used for new lines instead of "\n".
                
                #### 6. Fill in your summary using the following format:
                <h3>1. 個案基本資料(含疾病史):</h3>
                <p><AI's brief response></p>
                
                <h3>2. 生理/心理狀況:</h3>
                <p><AI's detailed response></p>

                <h3>3. 經濟狀況:</h3>
                <p><AI's brief response></p>
                
                <h3>4. 家庭支持狀況:</h3>
                <p><AI's brief response></p>
                
                <h3>5. 期待得到的服務:</h3> <if available>
                <p><AI's brief response></p>
                
                <text>
                {text}
                </text>
            
            Your answer (start with 1.個案基本資料(含疾病史)):

            """)
        self.chain = prompt | self.llm_model | StrOutputParser()

    def transcribe_audio(self, audio_path: str, language: str = 'zh', save_path: Optional[str] = None) -> dict:
        """使用 Whisper 模型將音訊檔轉譯成文字"""
        
        assert os.path.exists(audio_path), f"Audio file not found: {audio_path}"
        self.whisper_model = whisper.load_model('base', download_root=model_path)

        filename = os.path.basename(audio_path)
        print(f"\r\n\n開始轉譯 {filename} ...")

        if self.on_progress:
            _CustomProgressBar.set_callback(self.on_progress)
            sys.modules['whisper.transcribe'].tqdm.tqdm = _CustomProgressBar
            self.verbose = None
        else:
            self.verbose = False

        result = self.whisper_model.transcribe(
            audio_path,
            verbose=self.verbose,
            initial_prompt='轉譯成繁體中文',
            language=language,
            fp16=cuda.is_available()
        )

        print('轉譯完成!\n')
        if save_path:
            self._save_result(result, save_path, filename)
        return result
        

    async def transcribe_audio_async(self, audio_path: str, language: str = 'zh', save_path: Optional[str] = None) -> dict:
        """異步版本的音訊轉譯方法"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.transcribe_audio, audio_path, language, save_path)
        return result

    def _save_result(self, result: dict, save_path: str, filename: str):
        """保存轉譯結果到 JSON 文件"""
        json_filename = filename.replace('.mp3', '.json')
        full_path = os.path.join(save_path, json_filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)

    def summarize_text(self, text: str) -> str:
        """使用語言模型總結文字"""
        return self.chain.invoke({'text': text})

    def process_local_audio(self, filename: str) -> str:
        """處理本地音訊文件"""
        audio_path = os.path.join(media_path, filename)
        cache_path = audio_path.replace('.mp3', '.json')

        if os.path.exists(cache_path):
            print('找到 cache，直接讀取')
            with open(cache_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
        else:
            result = self.transcribe_audio(audio_path, save_path=media_path)

        return self.summarize_text(result['text'])

    def process_youtube_video(self, url: str) -> str:
        """處理 YouTube 視頻"""
        print('\r\n開始下載音訊檔...')
        filename = os.path.basename(yt_tool.download_audio(url,media_path))
        return self.process_local_audio(filename)


# 自訂進度條回調函數
def on_progress(current,total):
    percent = current / total * 100
    print(f'進度: {percent:.2f}%')

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__)+'/..')
    summarizer = SpeechSummarizer(on_progress=on_progress)
    mode_choice = input('使用本地音檔請輸入1 , 使用 YouTube 影片請輸入2：')
    summary = ''
    if mode_choice == '1':
        filename = input('請輸入音訊檔名稱 (包含副檔名)：')
        summary = summarizer.process_local_audio(filename)
    elif mode_choice == '2':
        url = input('請輸入 YouTube 影片網址：')
        summary = summarizer.process_youtube_video(url)
    else:
        print("無效的選擇")
    print(summary)