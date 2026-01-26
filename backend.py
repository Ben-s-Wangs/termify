import threading #allows you handle multiple processes at once
import glob #for file names
import wave #read audio files
import pyaudio #libraries for working w audio
import os
import yt_dlp
import time
from ytmusicapi import YTMusic #searches youtube music

class AudioBackend: 
    def __init__(self): #constructor
        #set initial values for object
        self.is_playing = False #initial state as music isnt played yet
        self._should_stop = False #signal code to stop
        self.thread = None 
        self.ytmusic = YTMusic() #API object

        self.chunk = 4096 # size
        self.p = pyaudio.PyAudio() #controlls audio

        #yt - dlp download options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',  #dictionary, map format to key and value pairs based on data
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': False,
        }

    def play_song(self, query):
        """Starts searching, downloading and playing a song without interfering with UI"""
        self.stop_song() #in case something is playing stop it
        self._should_stop = False

        self.thread = threading.Thread(target=self._run_loader_andplayer, args=(query,))
        self.thread.start() #have it work in the backgroud, essentially have play and do its magic using threading library

    def stop_song(self):
        """Tells the audio to stop"""
        self._should_stop = True #make sure its set to stop within field
        if (self.thread):
            self.thread.join() #stop calling the thread so it actually stops
    
    def _run_loader_andplayer(self, query):
        """Runs inside the background thread i.e does searching downloading and playing"""
        try: 
            #1. Search YT Music
            print(f"Searching for: {query}") #search music
            search_results = self.ytmusic.search(query)

            if not search_results: #if empty return 
                return
            video_id = search_results[0]['videoId'] #grabs first search id from result (0 indexed)\
            video_url = f'https://youtu.be/{video_id}' #create the url

            #2. Download the audio 
            filename = f"{video_id}.wav" 
            if not os.path.exists(filename): #check if the file has already been downloaded
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl: 
                    ydl.download([video_url]) #download it
            self._play_wav(filename) #download it

        except Exception as e:
            print(f"Error in backend: {e}") #write error message

    def _play_wav(self, filename):
        """Streams the audio into chunks from WAV files"""   
        wf = wave.open(filename, 'rb') #open file
        stream = self.p.open(
            format=self.p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(), #logic to get wav stuff, might be adjusted
            rate=wf.getframerate(),
            output=True
        )
        self.is_playing = True #update field

        data = wf.readframes(self.chunk) #read first part
        

        while data and not self._should_stop: #while the music shoukd be playing
            try:
                # FIX 2: Add exception_on_underflow=False
                # This tells ALSA "If you run out of data, don't crash, just wait for me."
                stream.write(data, exception_on_underflow=False)
            except OSError as e:
                # If a serious error happens, just print it and keep trying
                print(f"Audio Glitch: {e}")
            
            data = wf.readframes(self.chunk)
        #reset implementatio
        stream.stop_stream()
        stream.close()
        wf.close()

        self.is_playing = False #music done
 