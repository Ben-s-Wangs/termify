#!./bin/python3
import time
from ytmusicapi import YTMusic
import yt_dlp
import vlc
import sys
import glob

# replacing hard coded strings with variables
video_url = 'youtu.be/'

ydl_opts = {}

ytmusic = YTMusic()
# video_url += ytmusic.search("Bohemian Rhapsody")[0]['videoId']
if len(sys.argv) >= 2:
    
    video_id = ytmusic.search(sys.argv[1])[0]['videoId']
    video_url += video_id
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    p = vlc.MediaPlayer(glob.glob(f'*[[]{video_id}[]].webm')[0])
    p.play()
    time.sleep(int(ytmusic.search(sys.argv[1])[0]['duration_seconds']))