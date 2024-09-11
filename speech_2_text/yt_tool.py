from pytubefix import YouTube
from pytubefix.cli import on_progress

    
def download_audio(url, save_path):
    """下載 YouTube 影片的音訊

    Args:
        url (str): YouTube 影片網址
        save_path (str): 儲存位置

    Returns:
        str: 儲存檔案路徑
    """
    youtube = YouTube(url, on_progress_callback = on_progress)
    youtube_stream = youtube.streams.get_audio_only()
    result = youtube_stream.download(save_path, mp3=True)
    return result


    
    
if __name__ == '__main__':   
    url = input('請輸入 YouTube 影片網址：')
    save_path = './speech_2_text/media/'
    result = download_audio(url, save_path)
    print(result)