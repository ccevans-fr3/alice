import praw
from gtts import gTTS
import time
import subprocess
import os
import RPi.GPIO as GPIO
import threading
from snowboy import snowboydecoder

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

i = 0   # index of joke told
j = 0   # index of joke downloaded

reddit = praw.Reddit(client_id='l1iXXpo71aAJNQ',
                     client_secret='qok8GmuuDc8W2dLxD1tlA3Tw8CI',
                     user_agent='jokesv1')

subreddit = reddit.subreddit('jokes')

hot_python = subreddit.hot(limit = 25)

submission_ids = [] # list to hold first n submission IDs

GPIO.add_event_detect(4, GPIO.FALLING, callback=run_callback, bouncetime=300)
GPIO.add_event_detect(3, GPIO.FALLING, callback=shutdown_callback, bouncetime=300)

detector = snowboydecoder.HotwordDetector('hey_alice.pmdl', sensitivity=0.45, audio_gain=1.5)

def get_text(submission):
    title = submission.title
    firstn = submission.selftext[0:len(title)]
    if title.lower() == firstn.lower():
        text = submission.selftext
    else:
        text = title + '.\n' + submission.selftext
    text = text.replace('!\"', '!').replace('?\"', '?').replace('!\'', '!').replace('?\'', '?').replace('&#x200B;', '').replace('**', '')
    if 'edit:' in text.lower():
        text = text[0:text.lower().index('edit:')]
    return text

def save_audio(text, index):
    tts = gTTS(text=text, lang='en')
    filename = 'voice' + str(index) + '.mp3'
    tts.save(filename)
    print(filename + ' saved')

def call_joke():
    global i
    global j
    print('Run callback triggered. i = ' + str(i) + ', j = ' + str(j))
    if i < j:
        subprocess.call('sudo pulseaudio -D', shell=True)
        subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'voice' + str(i) + '.mp3'])
    else:
        if i == j:
            subprocess.call('sudo pulseaudio -D', shell=True)
            subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'hmm.mp3'])
        get_new_submission()
    i += 1

def detected_callback():
    call_joke()

def run_callback(channel):
    if not GPIO.input(4):
        call_joke()

def shutdown_callback(channel):
    for i in range(10):
        time.sleep(0.1)
        if GPIO.input(3):
            return
    subprocess.call('sudo pulseaudio -D', shell=True)
    subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'bye.mp3'])
    time.sleep(3)
    GPIO.cleanup()
    os.system("sudo shutdown now -h")

# After downloaded jokes have been used, new jokes are downloaded individually
def get_new_submission():
    try:
        hot_python_extra = subreddit.hot(limit = 200)
        for submission in hot_python_extra:
            print(submission)
            if not submission.stickied and submission not in submission_ids and len(submission.selftext) <= 1000:
                save_audio(get_text(submission), 0)
                submission_ids.append(submission)
                subprocess.call('sudo pulseaudio -D', shell=True)
                subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'voice0.mp3'])
                break
    except:
        subprocess.call('sudo pulseaudio -D', shell=True)
        subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'sorry.mp3'])


# Attempt to download jokes and keep script running
def download():
    global j
    for attempt in range(100):
        try:
            for submission in hot_python:
                if not submission.stickied and len(submission.selftext) <= 1000:
                    try:
                        submission_ids.append(submission)
                        text = get_text(submission)
                        save_audio(text, j)
                        j += 1
                    except Exception as e:
                        print(e)
                        pass
            # Keep script running
            while True:
                print('jokesd running')
                time.sleep(60)

        except Exception as e:
            print("Unable to get data\n" + str(e))
            # Keep script running even if internet is unavailable and re-attempt download
            while True:
                print('jokesd running (offline)')
                time.sleep(60)
                continue

def listen():
    detector.start(detected_callback)

d = threading.Thread(name='download', target=download)
l = threading.Thread(name='listen', target=listen)

d.start()
f.start()

