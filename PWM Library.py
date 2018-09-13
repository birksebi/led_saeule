import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

p =GPIO.PWM(12, 400000)
p.start(0)
try:
    while 1:
        