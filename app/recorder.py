import pyaudio           # Library for audio input/output
import subprocess        # Module for spawning new processes
from ftplib import FTP  # FTP client module
import time             # Module for working with time
import threading
import os

# Constants for audio recording
CHUNK = 1024            # Size of each audio chunk
FORMAT = pyaudio.paInt16 # Audio format
CHANNELS = 1            # Number of audio channels (mono)
RATE = 44100            # Sample rate (samples per second)
RECORD_SECONDS = 15*60    # Duration of each recording session (in seconds)

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
FTP_DIR = "/upload/audio"  # Directory on FTP server for uploads


class FTPManager:
    def __init__(self, host, user, pw, dir):
        self.host, self.user, self.pw, self.dir = host, user, pw, dir
        self.ftp = None
        self.connect()

    def connect(self):
        connected = False
        while not connected:
            try:
                self.ftp = FTP(self.host)
                self.ftp.login(self.user, self.pw)
                connected = True
                print(f"FTP server connected")
            except Exception as e:
                print(f"FTP srv connection fail: {e}")
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
                print(f"FTP upload fail: {e}")
                time.sleep(10)

    def close(self):
        if self.ftp:
            self.ftp.quit()
            print("Disconnected from FTP server")

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

def create_folder_in_ftp(ftp):
    try:
        today = time.strftime("%Y%m%d")
        if today not in ftp.nlst():
            ftp.mkd(today)
        ftp.cwd(today)
    except Exception as e:
        print(f"FTP upload error: {e}")
        pass

def upload_to_ftp(audio_data, ftp_manager):
    try:        
        ftp_manager.get_ftp().cwd(FTP_DIR)
        create_folder_in_ftp(ftp_manager.get_ftp())

        filename = f"{time.strftime('%Y%m%d-%H-%M-%S')}.wav"
        with open(filename, 'wb') as f:
            f.write(audio_data)
        ftp_manager.upload(filename)

        print(f"Audio uploaded successfully: {filename}")

    except Exception as e:
        print(f"FTP upload error: {e}")


def main():
    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_DIR)
    while True:

        audio_data = record_audio()
        upload_thread = threading.Thread(target=upload_to_ftp, args=(audio_data, ftp_manager))
        upload_thread.start()

        time.sleep(RECORD_SECONDS)  # Wait before next recording

if __name__ == "__main__":
    main()