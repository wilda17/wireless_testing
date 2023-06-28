from cSer import cSer
import RPi.GPIO as GPIO
import time
import serial


def wakeup(device):
    GPIO.output(31, True)
    time.sleep(0.1)
    GPIO.output(31, False)
    ret = ""
    while str(ret).strip() != "+QATWAKEUP":
        # print(ret)
        ret = device._ser_read()


def wait(seconds):
    print("wait for " + str(seconds) + "s:\t", end="", flush=True)
    for i in range(seconds):
        if i % 30 != 0 and i % 5 == 0:
            print(".", end="", flush=True)
        elif i % 30 == 0:
            print(i, end="", flush=True)
        time.sleep(1)
    print(seconds)

def make_default_settings(device):
    GPIO.output(31, True)
    time.sleep(0.1)
    GPIO.output(31, False)
    device._ser_write("AT+CFUN=0")
    device._ser_write("AT+QATWAKEUP=1")

try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(31, GPIO.OUT)

    nbiot = cSer('/dev/ttyS0', 9600, serial.EIGHTBITS,
                 serial.PARITY_NONE, serial.STOPBITS_ONE, 1)

    for x in range(1, 100+1):
        try:
            wakeup(nbiot)
            print("########## Cycle " + str(x) + " started ##########")

            # --------------------- start default settings ---------------------

            nbiot._ser_write_read_verify("ATE0", "OK")  # deactivate serial echo
            # set to minimal functionality "turn off antenna"
            nbiot._ser_write_read_verify("AT+CFUN=0", "OK")
            # enable power save mode; TAU set to max; sleep after 2 seconds
            nbiot._ser_write_read_verify(
                "AT+CPSMS=1,,,\"11011111\",\"00000001\"", "OK")  # AT+CPSMS=1,,,"11011111","00000011"

            nbiot._ser_write_read_verify(
                "AT+QCGDEFCONT=\"IP\",\"iot.1nce.net\"", "OK")  # PSD connection settings

            # enable nb-iot related event report
            nbiot._ser_write_read_verify("AT+QNBIOTEVENT=0,1", "OK")
            # enable wakeup indication
            nbiot._ser_write_read_verify("AT+QATWAKEUP=1", "OK")
            # --------------------- end default settings ---------------------

            # ------------------------ start sending -------------------------
            # delete old socket no 1 config
            nbiot._ser_write_read_verify("AT+QICLOSE=1", "OK")
            nbiot._ser_read_verify("CLOSE OK")

            # set to full functionality "turn on antenna"
            start = int(time.time() * 1000)
            nbiot._ser_write_read_verify("AT+CFUN=1", "OK")
            ret = ""
            while str(ret).strip() != "+CPIN: READY":
                ret = nbiot._ser_read()
            while str(ret).strip()[0:4] != "+IP:":
                ret = nbiot._ser_read()
            connection_period = int(time.time() * 1000) - start
            
            nbiot._ser_write_read_verify(
                "AT+QIOPEN=1,1,\"UDP\",\"92.248.32.107\",5005,1001,0,0", "OK")  # declare socket no 1
            nbiot._ser_read_verify("+QIOPEN: 1,0")  # open socket no 1

            for i in range(1):
                
                nbiot._ser_write_read_verify(
                    "AT+QISENDEX=1,1,AA", "OK")  # send data over socket 1
                nbiot._ser_read_verify("SEND OK")
                
            # set to minimal functionality "turn off antenna"
            nbiot._ser_write_read_verify("AT+CFUN=0", "OK")
            nbiot._ser_write("AT+QATWAKEUP=1")
            # -------------------------- end sending -------------------------

            f = open("log.txt", "a")
            f.write(str(connection_period) + "\n")
            f.close()
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            pass
        finally:
            make_default_settings(nbiot)
            wait(120)


except KeyboardInterrupt:
    print("\n\radios amigos")
finally:
    make_default_settings(nbiot)
    GPIO.cleanup()
