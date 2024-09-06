import dotenv
import os
import whisper

dotenv.load_dotenv()

whisper_model = whisper.load_model('base',download_root='./speech_2_text/models')

if __name__ == '__main__':
    pass
