import wave
import pyaudio
import argparse

def play_wav(filename):
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    chunk = 4096
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Play a WAV file',
        usage='python sound.py <filename.wav>'
    )
    parser.add_argument('filename')
    args = parser.parse_args()
    play_wav(args.filename)