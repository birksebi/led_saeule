import socket


udp_ip = "127.0.0.1"
udp_port = 6454

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
sock.bind((udp_ip, udp_port))

while True:
    data, addr = sock.recvfrom(1024)
    print("Message: ", data)