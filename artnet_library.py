import socket
from neopixel import *

N = 512
dmxuni0 = [0 for x in range(N)]
dmxuni1 = [0 for x in range(N)]

# LED strip configuration:
LED_COUNT = 288  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 6454))


def lhex(h):
    return ':'.join(x.encode('hex') for x in h)


while True:
    data = sock.recv(10240)
    artnet = data[0:7].decode('UTF-8')
    if artnet != 'Art-Net':
        continue
    if len(data) < 20:
        continue
    seq = data[12]
    physicalnet = data[13]
    universe = ord(data[14:15])
    lenght = ord(data[16:17])
    if universe == 0:
        x = 0
        for x in range(512):
            y = x + 18
            dmxuni0[x] = data[y]
            x = x + 1
        lednr = 0
        red = 1
        blue = 0
        green = 2
        for lednr in range(169):
            strip.setPixelColorRGB((lednr), (dmxuni0[red]), (dmxuni0[blue]), (dmxuni0[green]))
            red = red + 3
            blue = blue + 3
            green = green + 3
            lednr = lednr + 1
    elif universe == 1:
        x = 0
        for x in range(512):
            y = x + 18
            dmxuni1[x] = data[y]
            x = x + 1
        lednr = 170
        red = 1
        blue = 0
        green = 2
        for lednr in range(170, 288):
            strip.setPixelColorRGB((lednr), (dmxuni1[red]), (dmxuni1[blue]), (dmxuni1[green]))
            red = red + 3
            blue = blue + 3
            green = green + 3
            lednr = lednr + 1
    strip.show()


