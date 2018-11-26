# Copyright 2018 S.ZWeifel


import socket  # Netzwerk
import struct
import ipaddress
from subprocess import check_output
from neopixel import *  # Led Kontrolllibrary einbinden

N = 512  # Anzahl DMX Adressen pro Universum
dmxuni0 = [0 for x in range(N)]  # Dmx Universum 1
dmxuni1 = [0 for x in range(N)]  # Dmx Universum 2
artuni1 = 0  # Artnet Universum 1
artuni2 = 1  # Artnet Universum 2
net = 0
subnet = 0

strip = Adafruit_NeoPixel(288, 18, 800000, 10, False, 255,
                          0)  # Ledstreifen(Ans Leds,GPIO Pin, PWM Freq, DMA Channel, Helligkeit, Signal Invertieren,Channel)
strip.begin()  # LED Streifen ansprechen

# Port 6454 abhören
recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv.bind(('', 6454))

# Für Broadcasts ausgehend
sendbroad = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def artnetrecv():
    global data
    data = recv.recv(10240)  # Daten aus Port in Variable speichern
    global artnet
    artnet = data[0:7].decode('UTF-8')  # Bytes 0-7 in UTF-8 Zeichen konvertieren
    global arttype
    arttype = data[9:10].hex()


def artpoll():
    # Antwort für Artpoll erstellen
    artpollreplydata = []
    artpollreplydata.append(b'Art-Net\x00') #Artnet Header
    artpollreplydata.append(struct.pack('<H', 0x2100)) #OpCode(Low Byte)
    #Eigene IP Adresse(High Byte)
    global ip
    ip = check_output(['hostname', '--all-ip-addresses'])
    ip = ip.decode("utf-8")
    ip = ip.replace("\n", "")
    ip = [int(i) for i in ip.split('.')]
    artpollreplydata += [bytes([i]) for i in ip]
    artpollreplydata.append(struct.pack('<H', 0x1936)) #Artnet Port(Low Byte)
    artpollreplydata.append(struct.pack('>H', 0x0000)) #Firmware Version(High Byte)
    artpollreplydata.append(bytes(chr(net), 'utf8')) #Netz der Node
    artpollreplydata.append(bytes(chr(subnet), 'utf8')) #Subnetz der Node
    artpollreplydata.append(struct.pack('>H', 0x0000)) #OEM Code(High Byte)
    artpollreplydata.append(b'\x00') #Ubea Version(Wird nicht genutzt also 0)
    artpollreplydata.append(b'\xd0') #Status 1 (Siehe Packetdefinition)
    artpollreplydata.append(b'SZ') #ESTA Herstellercode(Auf Initalen SZ gesetzt)
    artpollreplydata.append(b'LedSaeule-SZ_____\x00') #Kurzname(17 Zeichen, Enden mit null)
    artpollreplydata.append(b'LedSaeule-Sebastian_Zweifel____________________________________\x00') #Name(63 Zeichen, Enden mit null)
    artpollreplydata = b''.join(artpollreplydata)
    print(artpollreplydata)


    sendbroad.sendto(artpollreplydata, ('255.255.255.255', 6454))


# def artipprog():
# ipprogrammierung und antwort...


def artdmx():
    global universe
    universe = ord(data[14:15])  # Universe abspeichern(Bytes 14 und 15)
    if universe == artuni1:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni0
            dmxuni0[x] = data[y]
            x = x + 1


    elif universe == artuni2:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni1
            dmxuni1[x] = data[y]
            x = x + 1


def lightstrip():
    if universe == artuni1:
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


while True:
    artnetrecv()
    if artnet != 'Art-Net':  # Wenn Packet nicht mit "Art-Net" startet, nächstes Packet abarbeiten
        continue
    if arttype == "50":
        artdmx()
        lightstrip()
    elif arttype == "20":
        artpoll()




