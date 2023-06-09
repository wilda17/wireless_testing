from BC66 import BC66
import time
import serial


try:
    nbiot = BC66('/dev/ttyS0', 9600, serial.EIGHTBITS,
                 serial.PARITY_NONE, serial.STOPBITS_ONE, True)

    nbiot._debug = True

    nbiot._ser_write_read_verify("ATE0")
    nbiot._ser_write_read_verify("AT", "OK")

    nbiot._ser_write_read_verify("AT+QCGDEFCONT?")


except KeyboardInterrupt:
    print("\n\radios amigos")
finally:
    pass
