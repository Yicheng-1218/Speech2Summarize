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
        
        Example:
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
        """註冊進度條回調函數

        Args:
            func (Callable[[int, int], None]): 進度條回調函數，參數分別是當前進度和總進度
        """
        self.on_progress = func
    
    
    def _setup_prompt_chain(self):
        prompt = PromptTemplate.from_template("""
            Please summarize the content in <text> and follow the steps starting with ####:
                #### 1. If the content is not fitting for the Care Management Assessment Scale, please say you cannot summarize it.
                #### 2. Always respond in zh-tw.
                #### 3. Correct any typos in the content.
                #### 4. Do not provide any information other than the main text content.
                #### 5. Summarize the content according to the Care Management Assessment Scale\
                        (ADLs, IADLs, Special Complex Care Needs, Home Environment and Social Participation,\
                        Emotional and Behavioral Patterns, Primary Caregiver Burden,\
                        Primary Caregiver Work and Support).
                #### 6. Ensure that HTML <br> tags are used for new lines instead of "\n".
                
                #### 7. Fill in your summary using the following format:
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

    def _save_result(self, result: dict, save_path: str, filename: str):
        """保存轉譯結果到 JSON 文件"""
        json_filename = filename.replace('.mp3', '.json')
        full_path = os.path.join(save_path, json_filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)

    def summarize_text(self, text: str) -> str:
        """使用語言模型總結文字"""
        return self.chain.invoke({'text': text})
