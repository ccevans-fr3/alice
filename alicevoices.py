from gtts import gTTS

def save_audio(text, filename):
    tts = gTTS(text=text, lang='en')
    filename = str(filename) + '.mp3'
    tts.save(filename)
    print(filename + ' saved')

voices = {}

voices['bye'] = 'Catchya later boyz'
voices['hmm'] = 'Hang on. Lemme think of a good one'
voices['sorry'] = 'Gimme a wifi connection and I\'ll dish out some more. Okay?'

for f,t in voices.items():
    save_audio(t, f)

