import RPi.GPIO as GPIO
import time

greenbin = 1
redbin = 1
bluebin = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

p =GPIO.PWM(12, 400000)
p.start(0)
while 1:
    green = [1,255,3,56,23,45]
    red = [2,34,43,34,67,222]
    blue = [34,23,45,33,221,111]
    x = 1
    while x < 244:

        greenbin[x] = bin(green[x])
        redbin[x] = bin(red[x])
        bluebin[x] = bin(blue[x])
        x = x+1
    y = 1
    while y < 244:
        greenbinarr = greenbin[y]
        redbinarr = redbin[y]
        bluebinarr = bluebin[y]
        greenbitcount = 0
        while greenbitcount < 8:
            if greenbinarr[greenbitcount] == 0:
                p.ChangeDutyCycle(3)
            else:
                p.ChangeDutyCycle(7)
        redbitcount = 0
        while redbitcount < 8:
            if redbinarr[redbitcount] == 0:
                p.ChangeDutyCycle(3)
            else:
                p.ChangeDutyCycle(7)
        bluebitcount = 0
        while bluebitcount < 8:
            if bluebinarr[bluebitcount] == 0:
                p.ChangeDutyCycle(3)
            else:
                p.ChangeDutyCycle(7)
        y = y + 1



p.stop()
GPIO.cleanup()