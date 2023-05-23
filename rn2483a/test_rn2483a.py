from RN2483A import RN2483A
import time    
import serial

def connect():
    while True:  
        lora._ser_write("mac join otaa")
        time.sleep(0.1)
        print(lora._ser_read())
        try:
            x = lora._ser_read()
            print(x)
            if(x.strip() == "accepted"):
                return
        except TimeoutError:
            pass
        time.sleep(10)

def send(inStr):
    while(lora._ser_write("mac tx uncnf 1 " + inStr) != "ok"):
        connect()

try:
    lora = RN2483A('/dev/ttyS0', 57600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, True)

    lora._ser_write("sys reset")
    print(lora._ser_read())

    lora._ser_write_read_verify("radio set sf sf9", "ok")
    lora._ser_write_read_verify("sys get hweui", "0004A30B01063D73")
    lora._ser_write_read_verify("mac set deveui 0004A30B01063D73", "ok")
    lora._ser_write_read_verify("mac set appkey AFB01FC11AB36057B35765D6D7195401", "ok")

    #print("set appeui")
    #print(lora._ser_write_read_verify("mac set appeui 0000000000000000", "ok"))
   
    lora._ser_write_read_verify("mac save","ok")


    send("ABCD1234")
        
    
    
    print(lora._ser_read())
    time.sleep(30)
    print(lora._ser_read())


except KeyboardInterrupt:
    print ("\n\radios amigos")
finally:
    pass
