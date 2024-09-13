import os
import json
import warnings
import asyncio
from typing import Optional

import whisper
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from torch import cuda
from dotenv import load_dotenv

from . import yt_tool

warnings.filterwarnings("ignore")

class SpeechSummarizer:
    def __init__(self):
        self.ffmpeg_path = "./speech_2_text/ffmpeg/bin"
        self.model_path = "./speech_2_text/models"
        self.media_path = './speech_2_text/media/'

        load_dotenv(override=True)
        os.environ['PATH'] += os.pathsep + self.ffmpeg_path

        self.whisper_model = whisper.load_model('base', download_root=self.model_path)
        self.llm_model = ChatAnthropic(model=os.getenv('ANTHROPIC_LLM_MODEL'), temperature=0)

        self._setup_prompt_chain()

    def _setup_prompt_chain(self):
        prompt = PromptTemplate.from_template("""
            請總結<text>中的內容，並遵循以下步驟：
            1、將內容轉換成繁體中文。
            2、想一個最適合的標題。
            3、將內容中的錯字進行修正。
            4、將內容整合成段落格式，並增加易讀性。
            5、一個段落之前加上一個小標題，並在小標題後加上冒號。
            6、除了正文的內容外，不要說明任何其他事情。
            
            輸出請匹配以下格式
            
            標題:
            <title>
            內容總結:
            <summary>
            
            
            <text>
            {text}
            </text>
            """)
        self.chain = prompt | self.llm_model | StrOutputParser()

    def transcribe_audio(self, audio_path: str, language: str = 'zh', save_path: Optional[str] = None) -> dict:
        """使用 Whisper 模型將音訊檔轉譯成文字"""
        assert os.path.exists(audio_path), f"Audio file not found: {audio_path}"
        filename = os.path.basename(audio_path)
        print(f"\r\n\n開始轉譯 {filename} ...")

        result = self.whisper_model.transcribe(
            audio_path,
            verbose=False,
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
        audio_path = os.path.join(self.media_path, filename)
        cache_path = audio_path.replace('.mp3', '.json')

        if os.path.exists(cache_path):
            print('找到 cache，直接讀取')
            with open(cache_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
        else:
            result = self.transcribe_audio_async(audio_path, save_path=self.media_path)

        return self.summarize_text(result['text'])

    def process_youtube_video(self, url: str) -> str:
        """處理 YouTube 視頻"""
        print('\r\n開始下載音訊檔...')
        filename = os.path.basename(yt_tool.download_audio(url, self.media_path))
        return self.process_local_audio(filename)


if __name__ == '__main__':
    summarizer = SpeechSummarizer()
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