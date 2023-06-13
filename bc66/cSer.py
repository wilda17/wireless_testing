import serial


class cSer():
    def __init__(self, port, baudrate, size, parity, stopbits, debug=False):
        self._debug = debug
        try:
            ser = serial.Serial(port=port,
                                baudrate=baudrate,
                                bytesize=size,
                                parity=parity,
                                stopbits=stopbits,
                                timeout=60,
                                write_timeout=60)
        except serial.SerialException:
            raise Exception("No module at given port.")
        except ValueError:
            raise Exception("Wrong configuration parameter given.")

        self._ser = ser

    def __del__(self):
        try:
            self._ser.close()
        except serial.SerialException:
            raise Exception("Exception while closing the port")

    def _ser_write(self, strIn):
        '''Write via serial connection to module'''
        # reset error handling flags
        transmit_failed = False
        transmit_incomplete = False

        if self._debug:
            print("UART: ", strIn)

        # format input string
        data = "{}\r\n".format(strIn)
        data = data.encode('utf-8')

        # send data (blocking)
        transmitted_bytes = self._ser.write(data)

        # verify transmit
        if transmitted_bytes == 0:
            transmit_failed = True
        elif transmitted_bytes < len(data):
            transmit_incomplete = True

        # error handling
        if transmit_failed:
            raise Exception("Write failed due to timeout.")
        if transmit_incomplete:
            raise Exception("Write was incomplete.")

    def _ser_read(self):
        '''Read via serial connection from module'''
        # read one line from parent device (blocking)
        received_bytes = self._ser.readline()

        # verification of timeout
        if received_bytes is None or len(received_bytes) == 0:
            raise TimeoutError("Timeout occurred during reception.")

        # format output string
        received_bytes = received_bytes.decode('utf-8')

        if received_bytes == "\r\n":  # read again if only "empty" lines have been returned
            return self._ser_read()
        elif self._debug:
            print(received_bytes)

        return received_bytes

    def _ser_write_read_verify(self, strIn, strOut=0):
        '''Perform serial write and read and verify the read output'''
        # transmit data
        self._ser_write(strIn)

        return self._ser_read_verify(strOut)

    def _ser_read_verify(self, strOut=0):
        # wait for answer
        answer = self._ser_read()

        # verify return
        if strOut != 0:
            if self._debug:
                print(answer)
            assert answer.strip() == strOut

        return answer
