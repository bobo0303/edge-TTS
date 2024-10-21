import asyncio
import edge_tts
import time
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.constant import SPEAKERS

async def tts(text, speaker):
    """  
    Convert text to speech and save the audio file.  
  
    This asynchronous function uses the edge_tts library to convert the provided text into speech.  
    The generated audio is saved as a .wav file, and the path to the saved file is returned.  
  
    :param text: str  
        The text to be converted to speech.  
    :type text: str  
  
    :param speaker: str  
        The speaker to use for the text-to-speech conversion.  
    :type speaker: str  
  
    :return: str  
        The file path to the saved audio file.  
    :rtype: str  
  
    :raises Exception:  
        If there is an error during the text-to-speech conversion or file saving process, an exception is raised.  
    """  
    
    communicate = edge_tts.Communicate(text, speaker)

    # save file
    saved_file_path = f'./audio/{datetime.datetime.now()}.wav'
    await communicate.save(saved_file_path)
    
    return saved_file_path


if __name__ == "__main__":
    # 示例使用
    
    text = "在非洲，每六十秒，就有一分鐘過去"
    
    start = time.time()
    audio_path = asyncio.run(tts(text, SPEAKERS[0]))
    end = time.time()
    print("audio save path:", audio_path)
    print("spent time:", end - start)

