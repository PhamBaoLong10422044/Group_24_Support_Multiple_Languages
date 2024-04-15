import time
import serial.tools.list_ports


#connect to device
try:
    ser = serial.Serial(port="COM5", baudrate=115200)
    print("Port connected...")
except:
    print("Can not open the port")

def sendCommand(cmd):
    ser.write(cmd.encode())

#Sensor for temp and humid
mess = ""
def processData(data):
    print(data)
    data = data.replace("!", "")
    data = data.replace("#", "")
    processData.splitData = data.split(":")
    print(processData.splitData)


def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]

def requestData(cmd):
    sendCommand(cmd)
    time.sleep(1)
    readSerial()
    requestData.cmd = int(cmd)
    print(requestData.cmd)