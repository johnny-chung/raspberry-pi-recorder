import pyaudio           # Library for audio input/output
from ftplib import FTP  # FTP client module
import time             # Module for working with time
import threading
import os
import logging
import requests
from logging.handlers import RotatingFileHandler


def check_internet_connection():
    try:
        response = requests.get("http://httpbin.org/get", timeout=5)
        if response.status_code == 200:
            logging.info("Internet connection is available.")
        else:
            logging.error("Failed to connect to the internet.")
    except Exception as e:
        logging.error("Failed to connect to the internet:", e)

# Constants for audio recording
CHUNK = 1024            # Size of each audio chunk
FORMAT = pyaudio.paInt16 # Audio format
CHANNELS = 1            # Number of audio channels (mono)
RATE = 44100            # Sample rate (samples per second)
RECORD_SECONDS = 15*60    # Duration of each recording session (in seconds)


# Configure logging with rotating file handler
LOG_FILENAME = "recorder.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB in bytes
BACKUP_COUNT = 5  # Keep up to 5 backup log files

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Load environment variables (if available)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Ignore if `python-dotenv` is not installed

# FTP server details
FTP_HOST = os.getenv("FTP_HOST", "")
FTP_USER = os.getenv("FTP_USER", "")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "")
FTP_DIR = "/upload"  # Directory on FTP server for uploads


class FTPManager:
    def __init__(self, host, user, pw, dir):
        self.host, self.user, self.pw, self.dir = host, user, pw, dir
        self.ftp = None
        self.connect()

    def connect(self):
        connected = False
        retries = 0
        logging.info(f"host: {self.host} | user: {self.user} | pw: {self.pw}")
        while not connected and retries < 3:
            try:
                self.ftp = FTP(self.host)
                self.ftp.login(self.user, self.pw)
                connected = True
                self.createDir("upload")
                logging.info(f"FTP server connected")
            except Exception as e:
                logging.error(f"FTP server connection fail: {e}")
                retries += 1
                time.sleep(10)

    def upload(self, filename):
        if self.ftp is None:
            self.connect()
        count = 0
        while count <= 2:
            try:                
                self.ftp.storbinary(f"STOR {filename}", open(filename, 'rb'))
                count = 3
            except Exception as e:
                count += 1
                logging.error(f"FTP upload fail: {e}")
                time.sleep(10)

    def close(self):
        if self.ftp:
            self.ftp.quit()
            logging.info("Disconnected from FTP server")

    def createDir(self, new_dir):
        try:        
            if new_dir not in self.ftp.nlst():
                self.ftp.mkd(new_dir)
            self.ftp.cwd(new_dir)
        except Exception as e:
            logging.error(f"Cannot create dir: {e}")
        pass

    def get_ftp(self):
        return self.ftp
    
def record_audio():
    audio = pyaudio.PyAudio()
    # open stream
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK
                        )
    frames = []
    start_time = time.time()
    # Record audio in chunks
    while time.time() - start_time < RECORD_SECONDS:
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    #join the audio trunk in bytes literal form 
    return b''.join(frames)

   

def upload_to_ftp(audio_data, ftp_manager):
    try:        
        ftp_manager.get_ftp().cwd(FTP_DIR)
        todayDir = time.strftime("%Y%m%d")
        ftp_manager.createDir(todayDir)

        filename = f"{time.strftime('%Y%m%d-%H-%M-%S')}.wav"
        with open(filename, 'wb') as f:
            f.write(audio_data)
        ftp_manager.upload(filename)

        print(f"Audio uploaded successfully: {filename}")

    except Exception as e:
        logging.error(f"Upload error: {e}")


def main():
    check_internet_connection()
    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_DIR)
    while True:

        audio_data = record_audio()
        upload_thread = threading.Thread(target=upload_to_ftp, args=(audio_data, ftp_manager))
        upload_thread.start()

        time.sleep(RECORD_SECONDS)  # Wait before next recording

if __name__ == "__main__":
    main()