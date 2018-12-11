# Copyright 2018 S.ZWeifel

import socket  # Netzwerk
import struct
import subprocess
import re
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
#Direkte Antworten an Sender


# Für Broadcasts ausgehend
sendbroad = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def artnetrecv():
    datarecv = recv.recvfrom(10240)  # Daten aus Port in Variable speichern
    global data
    data = datarecv[0]
    global controlleraddress
    controlleraddress = datarecv[1]
    global artnet
    artnet = data[0:7].decode('UTF-8')  # Bytes 0-7 in UTF-8 Zeichen konvertieren
    global arttype
    arttype = data[9:10].hex()


def artpoll():
    # Antwort für Artpoll erstellen
    artpollreplydata = []
    artpollreplydata.append(b'Art-Net\x00')  # Artnet Header
    artpollreplydata.append(struct.pack('<H', 0x2100))  # OpCode(Low Byte)
    # Eigene IP Adresse(High Byte)
    lsip = lsipcheck()
    artpollreplydata += [bytes([i]) for i in lsip]
    artpollreplydata.append(struct.pack('<H', 0x1936))  # Artnet Port(Low Byte)
    artpollreplydata.append(struct.pack('>H', 0x0000))  # Firmware Version(High Byte)
    artpollreplydata.append(bytes(chr(net), 'utf8'))  # Netz der Node
    artpollreplydata.append(bytes(chr(subnet), 'utf8'))  # Subnetz der Node
    artpollreplydata.append(struct.pack('>H', 0x0000))  # OEM Code(High Byte)
    artpollreplydata.append(b'\x00')  # Ubea Version(Wird nicht genutzt also 0)
    artpollreplydata.append(b'\xd0')  # Status 1 (Siehe Packetdefinition)
    artpollreplydata.append(b'SZ')  # ESTA Herstellercode(Auf Initalen SZ gesetzt)
    artpollreplydata.append(b'LedSaeule-SZ_____\x00')  # Kurzname(17 Zeichen, Enden mit null)
    artpollreplydata.append(
        b'LedSaeule-Sebastian_Zweifel____________________________________\x00')  # Name(63 Zeichen, Enden mit null)
    artpollreplydata.append(b'#0001[0001]LedSaeule Up and Running_____________________________')
    artpollreplydata.append(b'\x00')  # High Byte Num Ports (Bisher ungenutzt)
    artpollreplydata.append(b'\x02')  # Low Byte Num Ports (Anzahl Ports, 2)
    artpollreplydata.append(b'\x85')  # Port 1 Typ
    artpollreplydata.append(b'\x85')  # Port 2 Typ
    artpollreplydata.append(b'\x85')  # Port 3 Typ(ungenutzt)
    artpollreplydata.append(b'\x85')  # Port 4 Typ(ungenutzt)
    artpollreplydata.append(b'\x00\x00\x00\x00')  # Port 1-4 Input (ungenutzt)
    artpollreplydata.append(b'\x00\x00\x00\x00')  # Port 1-4 Output (ungenutzt)
    artpollreplydata.append(b'\x01\x01\x01\x01')  # Port 1-4 SwIn (ungenutzt)
    artpollreplydata.append(b'\x00\x00\x00\x00')  # Port 1-4 Swout (ungenutzt)
    artpollreplydata.append(b'\x00')  # SwVideo(deprecated)
    artpollreplydata.append(b'\x00')  # SwMarco (ungenutzt)
    artpollreplydata.append(b'\x00')  # Swremote (ungenutzt)
    artpollreplydata.append(b'\x00')  # ungenutzt
    artpollreplydata.append(b'\x00')  # ungenutzt
    artpollreplydata.append(b'\x00')  # ungenutzt
    artpollreplydata.append(b'\x00')  # Style(node)
    artpollreplydata.append(b'\x00\x00\x00\x00\x00\x00')  # MAC Adresse (ungenutzt)
    artpollreplydata += [bytes([i]) for i in lsip]  # IP Root device
    artpollreplydata.append(b'\x01')  # Root ID(root)
    artpollreplydata.append(b'\x1f')  # Status2
    artpollreplydata.append(b'\x00' * 26)  # ungenutzt aber so
    artpollreplydata = b''.join(artpollreplydata)
    sendbroad.sendto(artpollreplydata, ('255.255.255.255', 6454))


def artipprog():
    artipprogcommand = data[14:15].hex()
    artipprogcommand = bin(int(artipprogcommand, base=16))[2:]
    if artipprogcommand != "0":  # Nur Packete die etwa ändern wollen beachten
        if artipprogcommand == "01100001":
            # Ipadresse und Subnetz programmieren / DHCP ausstellen
            # Zu Programmierende Ip-Adresse auslesen in Dezimalzahlen umwandeln und in Array abspeichern
            artipprogip = ["1", "2", "3", "4"]
            artipprogip[0] = int(data[16:17].hex(), 16)
            artipprogip[1] = int(data[17:18].hex(), 16)
            artipprogip[2] = int(data[18:19].hex(), 16)
            artipprogip[3] = int(data[19:20].hex(), 16)
            # Zu Programmierende Subnet-Adresse auslesen in Dezimalzahlen umwandeln und in Array abspeichern
            artipprogsubnet = ["1", "2", "3", "4"]
            artipprogsubnet[0] = int(data[20:21].hex(), 16)
            artipprogsubnet[1] = int(data[21:22].hex(), 16)
            artipprogsubnet[2] = int(data[22:23].hex(), 16)
            artipprogsubnet[3] = int(data[23:24].hex(), 16)
            # Hier Funktion zur IP Einstellung aufrufen
            lsipconfig(0, artipprogip, artipprogsubnet)
            global lsdhcp
            lsdhcp = 0
        if artipprogcommand == "1001":
            # Standardwerte laden
            lsdefaultipconfig()
        if artipprogcommand == "10":
            # DHCP Einstellen
            lsipconfig(1, 0, 0)


def artipprogreply():
    artipprogreplydata = []
    artipprogreplydata.append(b'Art-Net\x00')  # Artnet Header
    artipprogreplydata.append(struct.pack('<H', 0xf900))  # OpCode(Low Byte)
    artipprogreplydata.append(struct.pack('>H', 0x000e))  # Artnet Protokollversion(14, High Byte)
    artipprogreplydata.append(b'\x00\x00\x00\x00')  # Filler 1-4
    # IP Adresse 4 Bytes
    lsip = lsipcheck()
    artipprogreplydata += [bytes([i]) for i in lsip]
    # Subnet Adresse 4 Bytes
    lssubnet = lssubnetcheck()
    artipprogreplydata += [bytes([i]) for i in lssubnet]
    artipprogreplydata.append(b'\x00')  # ungenutzt(ehemals ProgPort Hi)
    artipprogreplydata.append(b'\x00')  # ungenutzt(ehemals ProgPort Lo)
    # Status 1Byte Bit 6 DHCP alle anderen 0
    if lsdhcp == 0:
        artipprogreplydata.append(b'\x00')
    else:
        artipprogreplydata.append(b'\x02')

    artipprogreplydata.append(b'\x00')
    artipprogreplydata.append(b'\x00' * 7)  # ungenutzt
    # An Private Adresse des Controller schicken
    artipprogreplydata = b''.join(artipprogreplydata)
    recv.sendto(artipprogreplydata, controlleraddress)

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
        red = 1
        blue = 0
        green = 2
        for lednr in range(169):
            strip.setPixelColorRGB((lednr), (dmxuni0[red]), (dmxuni0[blue]), (dmxuni0[green]))
            red = red + 3
            blue = blue + 3
            green = green + 3
    elif universe == artuni2:
        red = 1
        blue = 0
        green = 2
        for lednr in range(170, 288):
            strip.setPixelColorRGB((lednr), (dmxuni1[red]), (dmxuni1[blue]), (dmxuni1[green]))
            red = red + 3
            blue = blue + 3
            green = green + 3
    strip.show()
def lsipconfig( progdhcp, progip, progsubnet):
    global lsdhcp
    if progdhcp == 1:
        #DHCP einschalten
        lsdhcp = 1
    else:
        #DHCP auschalten und IP/Subnet konfigurieren
        lsdhcp = 0

    print("heureka")
def lsdefaultipconfig():
    #Standardwerte definieren
    global lsdhcp
    lsdhcp = 1
    global lsip
    lsip = [192,168,0,201]
    global lssubnet
    lssubnet = [255,255,255,0]

def lsipcheck():
    lsipsubnet = subprocess.check_output(["ifconfig", "wlan0"]) #später auf eth0 ändern
    lsipsubnet = lsipsubnet.decode('UTF-8')
    a = re.compile('inet ')
    b = a.search(lsipsubnet)
    c = b.end()
    d = c + 16
    lsip = lsipsubnet[c:d]
    lsip = re.findall('([0-9]+)', lsip)
    # Listen Elemente von String zu Int konvertieren
    lsip[0] = int(lsip[0])
    lsip[1] = int(lsip[1])
    lsip[2] = int(lsip[2])
    lsip[3] = int(lsip[3])
    return lsip

def lssubnetcheck():
    lsipsubnet = subprocess.check_output(["ifconfig", "wlan0"])  # später auf eth0 ändern
    lsipsubnet = lsipsubnet.decode('UTF-8')
    a = re.compile('mask ')
    b = a.search(lsipsubnet)
    c = b.end()
    d = c + 16
    lssubnet = lsipsubnet[c:d]
    lssubnet = re.findall('([0-9]+)', lssubnet)
    # Listen Elemente von String zu Int konvertieren
    lssubnet[0] = int(lssubnet[0])
    lssubnet[1] = int(lssubnet[1])
    lssubnet[2] = int(lssubnet[2])
    lssubnet[3] = int(lssubnet[3])
    return lssubnet


while True:
    artnetrecv()
    lsdefaultipconfig()
    if artnet != 'Art-Net':  # Wenn Packet nicht mit "Art-Net" startet, nächstes Packet abarbeiten
        continue
    if arttype == "50":
        artdmx()
        lightstrip()
    elif arttype == "20":
        artpoll()
    elif arttype == "f8":
        artipprog()
        artipprogreply()
