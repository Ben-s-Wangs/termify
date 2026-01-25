#!./bin/python3
import time
from ytmusicapi import YTMusic
import yt_dlp
import vlc
import sys
# replacing hard coded strings with variables
video_url = 'youtu.be/'

ydl_opts = {}

ytmusic = YTMusic()
# video_url += ytmusic.search("Bohemian Rhapsody")[0]['videoId']
video_url += ytmusic.search(sys.argv[1])[0]['videoId']

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])

p = vlc.MediaPlayer("*.webm")
p.play()
time.sleep(int(ytmusic.search("Bohemian Rhapsody")[0]['duration_seconds']))