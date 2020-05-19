import praw
from gtts import gTTS
import time
import subprocess
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

i = 0   # index of joke told
j = 0   # index of joke downloaded

reddit = praw.Reddit(client_id='l1iXXpo71aAJNQ',
                     client_secret='qok8GmuuDc8W2dLxD1tlA3Tw8CI',
                     user_agent='jokesv1')

subreddit = reddit.subreddit('jokes')

hot_python = subreddit.hot(limit = 10)

def get_text(submission):
    title = submission.title
    firstn = submission.selftext[0:len(title)]
    if firstn.lower() == title.lower():
        text = submission.selftext
    else:
        text = title + '.\n' + submission.selftext
    text = text.replace('!\"', '!').replace('?\"', '?').replace('!\'', '!').replace('?\'', '?').replace('&#x200B;', '')
    if 'edit:' in text.lower():
        text = text[0:text.lower().index('edit:')]
    return text

def save_audio(text, index):
    tts = gTTS(text=text, lang='en')
    filename = 'voice' + str(index) + '.mp3'
    tts.save(filename)
    print(filename + ' saved')

def run_callback(channel):
    if not GPIO.input(4):
        global i
        global j
        print('Run callback triggered. i = ' + str(i) + ', j = ' + str(j))
        if i < j:
            subprocess.call('sudo pulseaudio -D', shell=True)
            subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'voice' + str(i) + '.mp3'])
        else:
            get_new_submission()
        i += 1

def shutdown_callback(channel):
    for i in range(10):
        time.sleep(0.1)
        if GPIO.input(18):
            return
    GPIO.cleanup()
    os.system("sudo shutdown now -h")

def get_new_submission():
    hot_python_extra = subreddit.hot(limit = 200)
    for submission in hot_python_extra:
        print(submission)
        if not submission.stickied and submission not in submission_ids:
            save_audio(get_text(submission), 0)
            submission_ids.append(submission)
            subprocess.call('sudo pulseaudio -D', shell=True)
            subprocess.call(['/usr/bin/python3', '/home/pi/jokes.py', 'voice0.mp3'])
            break


submission_ids = []

try:
    for submission in hot_python:
        if not submission.stickied and len(submission.selftext) <= 1000:
            submission_ids.append(submission)
            text = get_text(submission)
            save_audio(text, j)
            j += 1

    GPIO.add_event_detect(4, GPIO.FALLING, callback=run_callback, bouncetime=300)
    GPIO.add_event_detect(18, GPIO.FALLING, callback=shutdown_callback, bouncetime=300)

    while True:
        print('jokesd running')
        time.sleep(60)

except:
    print("Unable to get data")
