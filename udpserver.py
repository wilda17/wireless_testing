
import socket
import requests
import time

localIP     = ""
localPort   = 5005
bufferSize  = 1024


# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
UDPServerSocket.bind((localIP, localPort))

print("UDP server up and listening")

# Listen for incoming datagrams
counter = 1
try:
    while(True):
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        print(str(time.asctime(time.localtime())) + "\t" + str(counter) + ":\t" + str(message))
        counter = counter+1

except KeyboardInterrupt:
    print("Adios")
