
"""
prompt
請將我上傳的 SRT 檔轉換成可讀性高的段落，以下是要處理的步驟：
(注意：只輸出最後翻譯好的段落，中間的過程不要輸出文字)
1、把 SRT 檔的編號和時間戳記移除掉，只保留字幕的文字內容。
2、如果原字幕檔中有錯字，請依據上、下文和句意進行修正。
3、將字幕內容翻譯成繁體中文。
4、將句子整合成「段落」的文章格式，並且用逗號、句號和 Enter 來增加易讀性。
"""



from pytubefix import YouTube
from pytubefix.cli import on_progress
 
url = "https://www.youtube.com/watch?v=Ajsri2Imd3o"
 
yt = YouTube(url, on_progress_callback = on_progress)
print(yt.title)
 
ys = yt.streams.get_audio_only()
ys.download('./speech_2_text/media',mp3=True)