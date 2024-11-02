import eel
import os
import pyttsx3
import speech_recognition as sr
from datetime import date
import time
import webbrowser
import datetime
from pynput.keyboard import Key, Controller
import numpy as np
import sounddevice as sd
import sys
from queue import Queue
from threading import Thread

# -----------ChatBot Class Definition---------------
class ChatBot:

    started = False
    userinputQueue = Queue()

    @staticmethod
    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    @staticmethod
    def popUserInput():
        return ChatBot.userinputQueue.get()

    @staticmethod
    def close_callback(route, websockets):
        exit()

    @staticmethod
    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
        print(msg)

    @staticmethod
    def close():
        ChatBot.started = False
    
    @staticmethod
    def addUserMsg(msg):
        eel.addUserMsg(msg)
    
    @staticmethod
    def addAppMsg(msg):
        eel.addAppMsg(msg)

    @staticmethod
    def start():
        path = os.path.dirname(os.path.abspath(__file__))
        eel.init(path + r'\web', allowed_extensions=['.js', '.html'])
        try:
            eel.start('index.html', mode='chrome',
                      host='localhost',
                      port=27005,
                      block=False,
                      size=(350, 480),
                      position=(10, 100),
                      disable_cache=True,
                      close_callback=ChatBot.close_callback)
            ChatBot.started = True
            while ChatBot.started:
                try:
                    eel.sleep(10.0)
                except:
                    break
        
        except Exception as e:
            print(f"Error starting Eel: {e}")

# -------------Object Initialization---------------
today = date.today()
r = sr.Recognizer()
keyboard = Controller()
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# ----------------Variables------------------------
file_exp_status = False
files = []
path = ''
is_awake = True  # Bot status

# ------------------Functions----------------------
def reply(audio):
    print(audio)
    engine.say(audio)
    engine.runAndWait()

def wish():
    hour = int(datetime.datetime.now().hour)
    if hour < 12:
        reply("Good Morning!")
    elif hour < 18:
        reply("Good Afternoon!")
    else:
        reply("Good Evening!")
    reply("I am Proton, how may I help you?")

# Audio to String using sounddevice
def record_audio():
    fs = 44100  # Sample rate
    duration = 5  # Duration of recording in seconds
    print("Listening...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    print("Finished recording.")

    # Convert audio data to numpy array
    audio_data = audio_data.flatten()
    
    # Save the recording to a temporary WAV file
    filename = 'temp_audio.wav'
    sd.write(filename, audio_data, fs)

    # Use SpeechRecognition to recognize the audio
    with sr.AudioFile(filename) as source:
        audio = r.record(source)  # Read the entire audio file
        try:
            voice_data = r.recognize_google(audio)
            return voice_data.lower()
        except sr.RequestError:
            reply('Sorry, my service is down. Please check your internet connection.')
        except sr.UnknownValueError:
            print('Cannot recognize the audio.')
    return ''

# Executes Commands (input: string)
def respond(voice_data):
    global file_exp_status, files, is_awake, path
    print(voice_data)
    voice_data = voice_data.replace('proton', '').strip()
    
    # User Commands
    if is_awake == False and 'wake up' in voice_data:
        is_awake = True
        wish()

    elif 'hello' in voice_data:
        wish()

    elif 'what is your name' in voice_data:
        reply('My name is Proton!')

    elif 'date' in voice_data:
        reply(today.strftime("%B %d, %Y"))

    elif 'time' in voice_data:
        reply(datetime.datetime.now().strftime("%H:%M:%S"))

    elif 'search' in voice_data:
        search_term = voice_data.split('search')[1].strip()
        reply(f'Searching for {search_term}')
        url = f'https://google.com/search?q={search_term}'
        webbrowser.open(url)
        reply('This is what I found, Sir.')

    elif 'location' in voice_data:
        reply('Which place are you looking for?')
        temp_audio = record_audio()
        reply('Locating...')
        url = f'https://google.nl/maps/place/{temp_audio}'
        webbrowser.open(url)
        reply('This is what I found, Sir.')

    elif 'bye' in voice_data or 'exit' in voice_data or 'terminate' in voice_data:
        reply("Goodbye, Sir! Have a nice day.")
        is_awake = False
        return

    elif 'copy' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('c')
            keyboard.release('c')
        reply('Copied')

    elif 'paste' in voice_data:
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        reply('Pasted')

    elif 'list' in voice_data:
        path = 'C://'
        files = listdir(path)
        filestr = "\n".join(f"{i + 1}: {f}" for i, f in enumerate(files))
        file_exp_status = True
        reply('These are the files in your root directory:')
        print(filestr)

    elif file_exp_status:
        counter = 0
        if 'open' in voice_data:
            try:
                file_index = int(voice_data.split(' ')[-1]) - 1
                file_to_open = join(path, files[file_index])
                if isfile(file_to_open):
                    os.startfile(file_to_open)
                    file_exp_status = False
                else:
                    path = join(path, files[file_index], '')
                    files = listdir(path)
                    filestr = "\n".join(f"{i + 1}: {f}" for i, f in enumerate(files))
                    reply('Opened Successfully. Here are the files:')
                    print(filestr)
            except (IndexError, ValueError):
                reply('Please specify a valid file number.')
            except PermissionError:
                reply('You do not have permission to access this folder.')

        elif 'back' in voice_data:
            if path == 'C://':
                reply('Sorry, this is the root directory.')
            else:
                path = os.path.dirname(path)
                files = listdir(path)
                filestr = "\n".join(f"{i + 1}: {f}" for i, f in enumerate(files))
                reply('Going back. Here are the files:')
                print(filestr)

    else:
        reply('I am not programmed to do this!')

# ------------------Driver Code--------------------
t1 = Thread(target=ChatBot.start)
t1.start()

# Lock main thread until Chatbot has started
while not ChatBot.started:
    time.sleep(0.5)

wish()
voice_data = None
while True:
    if ChatBot.isUserInput():
        # Take input from GUI
        voice_data = ChatBot.popUserInput()
    else:
        # Take input from Voice
        voice_data = record_audio()

    # Process voice_data
    if 'proton' in voice_data:
        try:
            respond(voice_data)
        except SystemExit:
            reply("Exit Successful.")
            break
        except Exception as e:
            print(f"EXCEPTION raised: {e}")
