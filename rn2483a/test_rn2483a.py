from cSer import cSer
import time
import serial


def sleep_and_wake():
    lora._ser_write("sys sleep 10000")
    time.sleep(1)

    lora._ser.send_break(10)
    lora._ser_write("U")
    lora._ser_read_verify("ok")


def connect():
    r = True
    while r:
        lora._ser_write("mac join otaa")
        time.sleep(0.1)
        try:
            for _ in range(2):
                y = lora._ser_read()
                print(y)

                if (y.rstrip() == 'accepted'):
                    lora._ser_write_read_verify("mac save", "ok")
                    r = False
                    return
        except TimeoutError:
            pass
        time.sleep(10)


try:
    lora = cSer('/dev/ttyS0', 57600, serial.EIGHTBITS,
                serial.PARITY_NONE, serial.STOPBITS_ONE, 1)

    sleep_and_wake()
    lora._ser_write_read_verify("sys reset")
    if False:

        lora._ser_write_read_verify("sys factoryRESET")
        lora._ser_write_read_verify("mac reset 868", "ok")
        lora._ser_write_read_verify("radio set crc off", "ok")
        # lora._ser_write_read_verify("radio set sf sf9", "ok")

        lora._ser_write_read_verify("mac set devaddr 00000000", "ok")
        lora._ser_write_read_verify(
            "mac set appskey 00000000000000000000000000000000", "ok")

        lora._ser_write_read_verify(
            "mac set nwkskey 00000000000000000000000000000000", "ok")

        # lora._ser_write_read_verify("sys get hweui", "0004A30B01063D73")
        lora._ser_write_read_verify("mac set deveui 0004A30B01063D73", "ok")
        lora._ser_write_read_verify("mac set appeui 0000000000000000", "ok")
        lora._ser_write_read_verify(
            "mac set appkey AFB01FC11AB36057B35765D6D7195401", "ok")
        connect()

    lora._ser_write_read_verify("mac resume", "ok")
    lora._ser_write_read_verify("mac join abp", "ok")
    lora._ser_read_verify("accepted")

    for _ in range(1):
        lora._ser_write_read_verify("mac set dr 5", "ok")
        lora._ser_write_read_verify(
            "mac tx uncnf 1 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "ok")
        lora._ser_read_verify("mac_tx_ok")

        lora._ser_write_read_verify("mac set dr 5", "ok")
        lora._ser_write_read_verify(
            "mac tx uncnf 1 11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111", "ok")
        lora._ser_read_verify("mac_tx_ok")

    lora._ser_write_read_verify("mac save", "ok")

    sleep_and_wake()


except KeyboardInterrupt:
    print("\n\radios amigos")
finally:
    pass
