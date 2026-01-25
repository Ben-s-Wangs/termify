#!./bin/python3
import time
from ytmusicapi import YTMusic
import yt_dlp
import vlc
import sys
import glob
import os
# replacing hard coded strings with variables
video_url = 'youtu.be/'

ydl_opts = {}

ytmusic = YTMusic()
# video_url += ytmusic.search("Bohemian Rhapsody")[0]['videoId']
if len(sys.argv) >= 2:
 
    video_url += ytmusic.search(sys.argv[1])[0]['videoId']

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    p = vlc.MediaPlayer(f'{os.getcwd()}/{glob.glob('*.webm')[0]}')
    p.play()
    time.sleep(int(ytmusic.search(sys.argv[1])[0]['duration_seconds']))