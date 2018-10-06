#Copyright 2018 S.ZWeifel


import socket   #Netzwerk
from neopixel import *  #Led Kontrolllibrary einbinden

N = 512 #Anzahl DMX Adressen pro Universum
dmxuni0 = [0 for x in range(N)]  #Dmx Universum 1
dmxuni1 = [0 for x in range(N)]  #Dmx Universum 2
artuni1 = 0 #Artnet Universum 1
artuni2 = 1 #Artnet Universum 2

strip = Adafruit_NeoPixel(288, 18, 800000, 10, False, 255, 0) #Ledstreifen(Ans Leds,GPIO Pin, PWM Freq, DMA Channel, Helligkeit, Signal Invertieren,Channel)
strip.begin()   #LED Streifen ansprechen

#Port 6454 abhören
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 6454))



while True:
    data = sock.recv(10240) #Daten aus Port in Variable speichern
    artnet = data[0:7].decode('UTF-8')  #Bytes 0-7 in UTF-8 Zeichen konvertieren
    if artnet != 'Art-Net': #Wenn Packet nicht mit "Art-Net" startet, nächstes Packet abarbeiten
        continue
    if len(data) < 20:  #Wenn Packet kürzer als 20 Bytes ebenfalls direkt nächstes Packet abarbeiten
        continue
    universe = ord(data[14:15]) #Universe abspeichern(Bytes 14 und 15)
    if universe == artuni1:
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
    elif universe == artuni2:
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


