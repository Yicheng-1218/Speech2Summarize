from tempfile import _TemporaryFileWrapper
from pytubefix import YouTube, Stream
from pytubefix.exceptions import RegexMatchError,VideoUnavailable
from pytubefix.cli import on_progress

client = 'WEB_CREATOR'  # 客戶端類型


def _write_to_tempfile(youtube_stream:Stream,temp_file:_TemporaryFileWrapper) -> str:
    assert isinstance(temp_file, _TemporaryFileWrapper), 'temp_file must be a temporary file object'
    youtube_stream.stream_to_buffer(temp_file)
    temp_file.flush()
    return temp_file.name

def download_audio_to_tempfile(url:str, temp_file:_TemporaryFileWrapper,on_progrss_callback=None,on_complete=None) -> str:
    """下載 Youtube 影片的音訊到暫存文件

    Args:
        url (str): Youtube 影片網址
        temp_file (_TemporaryFileWrapper): 暫存文件
        on_progrss_callback (func, optional): 進度回呼函數 Defaults to None.
        on_complete (func, optional): 完成的回呼函數 Defaults to None.

    Returns:
        str: 暫存文件路徑
    """
    try:
        youtube = YouTube(
            url,
            client=client,
            on_progress_callback=on_progrss_callback if on_progrss_callback else on_progress,
            on_complete_callback=on_complete)
        youtube_stream = youtube.streams.get_audio_only()
        return _write_to_tempfile(youtube_stream, temp_file)
    except RegexMatchError:
        raise ValueError('Invalid YouTube URL')
    except VideoUnavailable as e:
        raise RuntimeError(f'Video unavailable: {e.video_id}')


# 指定位置下載音訊 Default -> os.getcwd()
def _save_file(youtube_stream:Stream, save_path=None) -> str:
    result = youtube_stream.download(save_path, mp3=True)
    return result

def download_audio(url:str, save_path:str = None , on_progrss_callback = None ,on_complete=None) -> str:
    """下載 Youtube 影片的音訊

    Args:
        url (str): Youtube 影片網址
        save_path (str, optional): 音訊儲存位置 Defaults to None.
        on_progrss_callback (func, optional): 進度回呼函數 Defaults to None.
        on_complete (func, optional): 完成時的回呼函數. Defaults to None.

    Returns:
        str: 儲存位置
    """
    try:
        youtube = YouTube(
            url,
            client=client,
            on_progress_callback=on_progrss_callback if on_progrss_callback else on_progress,
            on_complete_callback = on_complete)
        youtube_stream = youtube.streams.get_audio_only()
        return _save_file(youtube_stream, save_path)
    except RegexMatchError:
        raise ValueError('Invalid YouTube URL')