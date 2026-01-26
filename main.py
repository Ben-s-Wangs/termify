# import time
from ytmusicapi import YTMusic
import yt_dlp
# import vlc
import sys
import glob
import wave
import pyaudio

# replacing hard coded strings with variables
video_url = 'https://youtu.be/'

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'js_runtimes': {'deno':{'venv/lib/python3.14/site-packages/deno':'path'}} 
}

chunk = 1024

ytmusic = YTMusic()
# video_url += ytmusic.search("Bohemian Rhapsody")[0]['videoId']
if len(sys.argv) >= 2:
    
    video_id = ytmusic.search(sys.argv[1])[0]['videoId']
    video_url += video_id
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # p = vlc.MediaPlayer(glob.glob(f'*[[]{video_id}[]].mp3')[0])
    # p.play()
    # time.sleep(int(ytmusic.search(sys.argv[1])[0]['duration_seconds']))

    wf = wave.open(glob.glob(f'*[[]{video_id}[]].wav')[0])
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()