# Copyright 2018 S.ZWeifel

# Librarys einbinden, Standardwerte definieren
import socket  # Netzwerk
import struct
import subprocess
import re
import threading
import time
from os import system
from neopixel import *  # Led Kontrolllibrary einbinden

N = 512  # Anzahl DMX Adressen pro Universum
dmxuni0 = [0 for x in range(N)]  # Dmx Universum 1
dmxuni1 = [0 for x in range(N)]  # Dmx Universum 2
artuni1 = 0  # Artnet Universum 1
artuni2 = 1  # Artnet Universum 2
sacnuni1 = 1
sacnuni2 = 2
net = 0
subnet = 0
shutdown = 0
modus = "artnet"
sacndataselect = 1

strip = Adafruit_NeoPixel(288, 18, 800000, 10, False, 255,
                          0)  # Ledstreifen(Ans Leds,GPIO Pin, PWM Freq, DMA Channel, Helligkeit, Signal Invertieren,Channel)
strip.begin()  # LED Streifen ansprechen

# TCP/IP Kommunikation -------------------------------------------------------------------------------------------------
# Port 6454 abhören(ART-NET)
recvartnet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recvartnet.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recvartnet.bind(('', 6454))


# Für Broadcasts ausgehend
sendbroad = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sendbroad.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Port 5568/ Multicast IP 239.255.0.X abhören
sacn_recv1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sacn_recv1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sacn_recv1.bind((sacn_universe_1, 5568))
mreq = struct.pack("4sl", socket.inet_aton(sacn_universe_1), socket.INADDR_ANY)

sacn_recv1.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

sacn_recv2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sacn_recv2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sacn_recv2.bind((sacn_universe_2, 5568))
mreq = struct.pack("4sl", socket.inet_aton(sacn_universe_1), socket.INADDR_ANY)

sacn_recv2.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# ART-NET ----------------1---------------------------------------------------------------------------------------------
def artnet():
    while True:
        artnetrecv()
        defaultipconfig()
        if artnet != 'Art-Net':  # Wenn Packet nicht mit "Art-Net" startet, nächstes Packet abarbeiten
            continue
        if arttype == "50":
            artdmx()
            lightstrip()
            motorensteuerung()
        elif arttype == "20":
            artpoll()
        elif arttype == "f8":
            artipprog()
            artipprogreply()
        global modus
        if modus != "artnet":
            break
        global shutdown
        if shutdown == "1":
            break

def artnetrecv():
    artnetdatarecv = recvartnet.recvfrom(10240)  # Daten aus Port in Variable speichern
    global data
    data = artnetdatarecv[0]
    global controlleraddress
    controlleraddress = artnetdatarecv[1]
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
    lsip = ipcheck()
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
            ipconfig(0, artipprogip, artipprogsubnet)
            global lsdhcp
            lsdhcp = 0
        if artipprogcommand == "1001":
            # Standardwerte laden
            defaultipconfig()
        if artipprogcommand == "10":
            # DHCP Einstellen
            ipconfig(1, 0, 0)


def artipprogreply():
    artipprogreplydata = []
    artipprogreplydata.append(b'Art-Net\x00')  # Artnet Header
    artipprogreplydata.append(struct.pack('<H', 0xf900))  # OpCode(Low Byte)
    artipprogreplydata.append(struct.pack('>H', 0x000e))  # Artnet Protokollversion(14, High Byte)
    artipprogreplydata.append(b'\x00\x00\x00\x00')  # Filler 1-4
    # IP Adresse 4 Bytes
    lsip = ipcheck()
    artipprogreplydata += [bytes([i]) for i in lsip]
    # Subnet Adresse 4 Bytes
    lssubnet = subnetcheck()
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
    recvartnet.sendto(artipprogreplydata, controlleraddress)

def artdmx():
    global artnetuniverse
    artnetuniverse = ord(data[14:15])  # Universe abspeichern(Bytes 14 und 15)
    if artnetuniverse == artuni1:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni0
            dmxuni0[x] = data[y]
            x = x + 1


    elif artnetuniverse == artuni2:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni1
            dmxuni1[x] = data[y]
            x = x + 1

# SACN -----------------------------------------------------------------------------------------------------------------
def sacn():
    while True:
        sacnrecv()
        if sacn != "ASC-E1.17"
            continue
        if sacntype == "\x00\x00\x00\x02"
            sacndmx()
            lightstrip()
            motorensteuerung()
        global modus
        if modus != "sacn":
            break
        global shutdown
        if shutdown == "1":
            break

def sacnrecv():
    global sacndatarecv
    #Abwechselnd Daten der beiden Multicast Adressen auswerten
    global sacndataselect
    if sacndataselect == 1:
        sacndatarecv = sacn_recv1.recv(1024)
        sacndataselect = 2
    elif sacndataselect == 2:
        sacndatarecv = sacn_recv2.recv(1024)
        sacndataselect = 1
    global sacn
    sacn = sacndatarecv[4:15].decode('UTF-8')
    global sacnuniverse
    sacnuniverse = sacndatarecv[114]
    global sacntype
    sacntype = sacndatarecv[40:44]


def sacndmx():
    global sacndatarecv
    global data
    data = sacndatarecv[126:637]
    global sacnuniverse
    if sacnuniverse == sacnuni1:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni0
            dmxuni0[x] = data[y]
            x = x + 1
    elif sacnuniverse == sacnuni2:
        x = 0
        for x in range(512):
            y = x + 18
            global dmxuni1
            dmxuni1[x] = data[y]
            x = x + 1




# DMX ------------------------------------------------------------------------------------------------------------------
def dmx():



# Shutdown Sequenz -----------------------------------------------------------------------------------------------------
def shutdowndbcheck():
    while True:
        #DB Abfrage des Shutdown Werts in der DB
        if shutdown == 1:
            shutdownfunc()
            break
        time.sleep(30) #Pause damit nur alle 30 Sekunden eine Abfrage läuft



def shutdownfunc():
    settingsave()
    global shutdown
    shutdown = 1
    print("Gerät wird heruntergefahren, bitte warten.")
    time.sleep(30)
    system('systemctl poweroff')




# Reset Sequenz --------------------------------------------------------------------------------------------------------
def resetdbcheck():
    while True:
        # DB Abfrage des Reset Werts in der DB
        if reset == 1:
            resetfunc()
            break
        time.sleep(30)  # Pause damit nur alle 30 Sekunden eine Abfrage läuft

def resetfunc():
    settingsave()
    global shutdown
    shutdown = 1
    print("Neustart, bitte warten.")
    time.sleep(30)
    system('systemctl reboot')

# Einstellungen speichern ----------------------------------------------------------------------------------------------
def settingsave():
    print("Einstellungen werden gespeichert.")
    # Variablen für IP, Subnetz, DHCP, Modus speichern

# Einstellungen laden
def settingload():

# Initialisierung
def initfunc():
    # Shutdown/Reset Wert in der DB auf 0 setzen
    settingload()
    # Daten aus DB laden(IP, DHCP, Subnet, Modus)
    ipconfig(dhcp, ip, subnet) #Konfigurationsdaten ausführen
    print("Einstellungen geladen. Programmstart.")

# Modus Auswahl --------------------------------------------------------------------------------------------------------
def modusdbcheck():
    while True:
        if shutdown == 1:
            break




# Lightstrip Kontrollcode ----------------------------------------------------------------------------------------------
def lightstrip():
    global modus
    if modus == "artnet"
        if artnetuniverse == artuni1:
            red = 1
            blue = 0
            green = 2
            for lednr in range(169):
                strip.setPixelColorRGB((lednr), (dmxuni0[red]), (dmxuni0[blue]), (dmxuni0[green]))
                red = red + 3
                blue = blue + 3
                green = green + 3
        elif artnetuniverse == artuni2:
            red = 1
            blue = 0
            green = 2
            for lednr in range(170, 288):
                strip.setPixelColorRGB((lednr), (dmxuni1[red]), (dmxuni1[blue]), (dmxuni1[green]))
                red = red + 3
                blue = blue + 3
                green = green + 3
    elif modus == "sacn"
        if sacnuniverse == sacnuni1:
            red = 1
            blue = 0
            green = 2
            for lednr in range(169):
                strip.setPixelColorRGB((lednr), (dmxuni0[red]), (dmxuni0[blue]), (dmxuni0[green]))
                red = red + 3
                blue = blue + 3
                green = green + 3
        elif sacnuniverse == sacnuni2:
            red = 1
            blue = 0
            green = 2
            for lednr in range(170, 288):
                strip.setPixelColorRGB((lednr), (dmxuni1[red]), (dmxuni1[blue]), (dmxuni1[green]))
                red = red + 3
                blue = blue + 3
                green = green + 3


    strip.show()

# Motorensteuerung -----------------------------------------------------------------------------------------------------
def motorensteuerung():


# IP Einstellungen abspeichern, ausführen, auslesen --------------------------------------------------------------------
def ipconfig(progdhcp, progip, progsubnet):
    global lsdhcp
    if progdhcp == 1:
        #DHCP einschalten
        lsdhcp = 1
    else:
        #DHCP auschalten und IP/Subnet konfigurieren
        lsdhcp = 0

    print("heureka")
def defaultipconfig():
    #Standardwerte definieren
    global lsdhcp
    lsdhcp = 1
    global lsip
    lsip = [192,168,0,201]
    global lssubnet
    lssubnet = [255,255,255,0]

def ipcheck():
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

def subnetcheck():
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

def ipdbcheck():



# Hauptschleife --------------------------------------------------------------------------------------------------------
while True:
    initfunc()
    modusdbcheckthread = threading.Thread(target=modusdbcheck())
    ipdbcheckthread = threading.Thread(target=ipdbcheck())
    shutdowndbcheckthread = threading.Thread(target=shutdowndbcheck())
    resetdbcheckthread = threading.Thread(target=resetdbcheck())
    # Modusdbcheck als Thread Parallel starten
    modusdbcheckthread.start()
    # Ipdbcheck als Thread Parallel starten
    ipdbcheckthread.start()
    # Shutdowndbcheck als Thread Parallel starten
    shutdowndbcheckthread.start()
    # Resetdbcheck als Thread Parallel starten
    resetdbcheckthread.start()

    if modus == "artnet"
        artnet()
    elif modus == "sacn"
        sacn()
    elif modus == "dmx"
        dmx()
