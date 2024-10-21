from fastapi import FastAPI, HTTPException  
from fastapi.responses import FileResponse, StreamingResponse  
import os  
import time  
import pytz  
import asyncio
import logging  
import uvicorn  
import datetime  
from pydantic import BaseModel  
from threading import Thread, Event  
from api.tts import tts  
from lib.constant import SPEAKERS
  
#############################################################################  
if not os.path.exists("./audio"):  
    os.mkdir("./audio")  
  
# 配置日志记录  
log_format = "%(asctime)s - %(message)s"  # 输出时间戳和消息内容  
logging.basicConfig(level=logging.INFO, format=log_format)  # ['DEBUG', 'INFO']  
logger = logging.getLogger(__name__)  
  
# 配置 utc+8 時間  
utc_now = datetime.datetime.now(pytz.utc)  
tz = pytz.timezone('Asia/Taipei')  
local_now = utc_now.astimezone(tz)  
  
app = FastAPI()  
  
@app.get("/")  
def HelloWorld():  
    return {"Hello": "World"}  
  
##############################################################################  
class TextRequest(BaseModel):  
    text: str  
    
class UserSelection(BaseModel):  
    user_index: int  
    
speaker = SPEAKERS[0]   # HsiaoChenNeural

##############################################################################
  
# load the default model at startup  
@app.on_event("startup")  
async def set_default_speaker():
    logger.info("#####################################################")  
    logger.info("Use the default speaker \"HsiaoChenNeural\"")  
    logger.info(f"You can post the \"/change_speaker\" and select \"0~{len(SPEAKERS)-1}\" to change the voice (For speaker info, please refer to constant.py)")  
    logger.info("#####################################################")  
    delete_old_audio_files()

@app.post("/change_speaker")  
def select_user(selection: UserSelection): 
    """  
    Change the current speaker based on user selection.  
  
    This function updates the global speaker variable to the speaker selected by the user.  
    The selection is validated to ensure it falls within the valid range of available speakers.  
  
    :param selection: UserSelection  
        The request body containing the user index to select the speaker.  
    :type selection: UserSelection  
  
    :return: dict  
        A dictionary containing a message confirming the selected user.  
    :rtype: dict  
  
    :raises HTTPException:  
        If the user index is out of the valid range, an HTTP 400 error is raised with the error message.  
    """  
    
    global speaker 
    
    # 驗證索引是否在範圍內  
    if selection.user_index < 0 or selection.user_index >= (len(SPEAKERS)-1):  
        raise HTTPException(status_code=400, detail="Invalid user index")  
      
    speaker = SPEAKERS[selection.user_index]  
    logger.info(f"Selected user is now {speaker}")
    return {"message": f"Selected user is now {speaker}"}  
  
  
# inference endpoint  
@app.post("/to_speech")  
def generate_audio(request: TextRequest):  
    """  
    Convert text to speech and return the audio file.  
  
    This function uses the Text-to-Speech (TTS) service to convert the provided text  
    into an audio file. The audio file is then returned as a response.  
  
    :param request: TextRequest  
        The request body containing the text to be converted to speech.  
    :type request: TextRequest  
  
    :return: FileResponse  
        The response containing the audio file.  
    :rtype: FileResponse  
  
    :raises HTTPException:   
        If there is an error during the TTS conversion or file retrieval process,  
        an HTTP 500 error is raised with the error message.  
    """ 
    logger.info(f"input message: {request.text}")
    try:  
        start = time.time()
        audio_file_path = asyncio.run(tts(request.text, speaker))
        logger.info(audio_file_path)  
        end = time.time()
        logger.info(f"generate has been completed in {(end -start):.2f} seconds.")  
        # 使用 FileResponse 返回音频文件  
        return FileResponse(audio_file_path, media_type='audio/wav', filename=os.path.basename(audio_file_path))  
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e))  
  
# 清理音频文件  
def delete_old_audio_files():  
    """  
    The process of deleting old audio files  
    :param  
    ----------  
    None: The function does not take any parameters  
    :rtype  
    ----------  
    None: The function does not return any value  
    :logs  
    ----------  
    Deleted old files  
    """  
    current_time = time.time()  
    audio_dir = "./audio"  
    for filename in os.listdir(audio_dir):  
        file_path = os.path.join(audio_dir, filename)  
        if os.path.isfile(file_path):  
            file_creation_time = os.path.getctime(file_path)  
            # 删除超过一天的文件  
            if current_time - file_creation_time > 24 * 60 * 60:  
                os.remove(file_path)  
                logger.info(f"Deleted old file: {file_path}")  
  
# 每日任务调度  
def schedule_daily_task(stop_event):  
    while not stop_event.is_set():  
        if local_now.hour == 0 and local_now.minute == 0:  
            delete_old_audio_files()  
            time.sleep(60)  # 防止在同一分鐘內多次觸發 
        time.sleep(1)  
        
# 启动每日任务调度  
stop_event = Event()  
task_thread = Thread(target=schedule_daily_task, args=(stop_event,))  
task_thread.start()  
  
@app.on_event("shutdown")  
def shutdown_event():  
    stop_event.set()  
    task_thread.join()  
    logger.info("Scheduled task has been stopped.")  
  
if __name__ == "__main__":  
    port = int(os.environ.get("PORT", 52004))  
    uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"  
    uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(asctime)s [%(name)s] %(client_addr)s - "%(request_line)s" %(status_code)s'  
    uvicorn.run(app, log_level='info', host='0.0.0.0', port=port)  
 
 