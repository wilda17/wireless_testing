from RN2483A import RN2483A
import time
import serial


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
        time.sleep(30)


try:
    lora = RN2483A('/dev/ttyS0', 57600, serial.EIGHTBITS,
                   serial.PARITY_NONE, serial.STOPBITS_ONE, True)

    lora._ser_write_read_verify("sys reset")
    # lora._ser_write_read_verify("mac reset 868", "ok")
    # lora._ser_write_read_verify("radio set sf sf9", "ok")

    # lora._ser_write_read_verify("mac set devaddr 00000000", "ok")
    # lora._ser_write_read_verify(
    #    "mac set appskey 00000000000000000000000000000000", "ok")

    # lora._ser_write_read_verify(
    #    "mac set nwkskey 00000000000000000000000000000000", "ok")

    # lora._ser_write_read_verify("sys get hweui", "0004A30B01063D73")
    # lora._ser_write_read_verify("mac set deveui 0004A30B01063D73", "ok")
    # lora._ser_write_read_verify("mac set appeui 0000000000000000", "ok")
    # lora._ser_write_read_verify(
    #    "mac set appkey AFB01FC11AB36057B35765D6D7195401", "ok")

    # connect()

    # lora._ser_write_read_verify("mac resume", "ok")
    # lora._ser_write_read_verify("mac join abp", "ok")
    # print(lora._ser_read_verify("accepted"))

    # lora._ser_write_read_verify("mac tx uncnf 1 ABCD1234", "ok")
    # print(lora._ser_read_verify("mac_tx_ok"))
    # lora._ser_write_read_verify("mac save", "ok")

    lora._ser_write("sys sleep 10000")

    lora._ser.send_break(10)
    lora._ser_write("U")
    lora._ser_read_verify("ok")



except KeyboardInterrupt:
    print("\n\radios amigos")
finally:
    pass
