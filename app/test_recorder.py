import pytest
import datetime
import time
from unittest.mock import  MagicMock, patch
import io
from .recorder import upload_to_ftp, record_audio

CHUNK = 1024            # Size of each audio chunk
CHANNELS = 1            # Number of audio channels (mono)
RATE = 44100            # Sample rate (samples per second)
RECORD_SECONDS = 10    # Duration of each recording session (in seconds)

@pytest.fixture
def mock_ftp_manager():
  return MagicMock()

@pytest.fixture
def mocker():
  return MagicMock()  


def test_upload_to_ftp(mock_ftp_manager):
    # Mock audio data
    audio_data = b'\x00\x01\x02\x03'
    
    # Create a BytesIO object to hold the audio data
    audio_bytesio = io.BytesIO(audio_data)

    # Patch the open function to return a file-like object
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value = audio_data
        upload_to_ftp(audio_data, mock_ftp_manager)

    # Assert that the upload method is called with a BytesIO object
    upload_call_args = mock_ftp_manager.upload.call_args_list[0][0]
    uploaded_object = upload_call_args[1]
    assert isinstance(uploaded_object, io.BytesIO)

    # compare the content of the BytesIO objects
    uploaded_object.seek(0)
    audio_bytesio.seek(0)
    assert uploaded_object.read() == audio_bytesio.read()

    mock_ftp_manager.get_ftp.assert_called_once()
    mock_ftp_manager.get_ftp.return_value.cwd.assert_called_once_with('/upload')
    today_dir = datetime.datetime.now().strftime("%Y%m%d")
    mock_ftp_manager.createDir.assert_called_once_with(today_dir)


# def test_record_audio():
#     # Create mock PyAudio and stream objects
#     mock_pyaudio = MagicMock()
#     mock_stream = MagicMock()

#     # Mock time.time using MagicMock
#     mock_time = MagicMock(side_effect=[0, 10])

#     # Define expected audio chunks
#     chunk_data = b"audio_data" * int(CHUNK / len(b"audio_data"))
#     expected_chunks = [chunk_data] * int(10 * RATE / CHUNK)

#     # Set up side effects for the mock stream read method
#     mock_stream.read.side_effect = expected_chunks

#     # Patch PyAudio to return the mock PyAudio instance
#     mock_pyaudio.open.return_value = mock_stream

  
#     audio_data = record_audio()

#     # Assert audio data contains expected chunks
#     assert all(chunk in audio_data for chunk in expected_chunks)