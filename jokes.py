import sys
import pygame
import subprocess
import time
import pigpio

filename = sys.argv[1]

PA_SOURCE = "alsa_output.platform-soc_audio.analog-mono.monitor"

PA_FORMAT = "u8"
PA_CHANNELS = 1
PA_RATE = 500
PA_BUFFER = 32

parec = subprocess.Popen(["/usr/bin/pacat", "--record", "--device=" + PA_SOURCE, "--rate=" + str(PA_RATE), "--channels=" + str(PA_CHANNELS), "--format=" + PA_FORMAT, "--latency=" + str(PA_BUFFER)], stdout=subprocess.PIPE)

pi = pigpio.pi()
servo_pin = 14
pi.set_mode(servo_pin, pigpio.OUTPUT)
pi.set_PWM_frequency(servo_pin, 50)

def speak():
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    i = 0
    max = 0
    while pygame.mixer.music.get_busy() == True:
        sample = ord(parec.stdout.read(1)) - 128
        i += 1
        if i % 20 == 0:
            set_servo_angle(max)
            max = 0
        if abs(sample) > max: max = abs(sample)
        continue

def set_servo_angle(max):
    angle = (max/20) * 30
    pw = angle * 2000/180 + 500
    pi.set_servo_pulsewidth(servo_pin, pw)


try:
    set_servo_angle(0)
    speak()
    set_servo_angle(0)
    time.sleep(1)
    
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()

except:
    pi.set_servo_pulsewidth(servo_pin, 0)
    pi.stop()

