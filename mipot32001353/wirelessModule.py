from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union
import serial
import time
import RPi.GPIO as GPIO
import queue

class WirelessModule(ABC):

    _pin_configuration: Dict[str, int]

    @abstractmethod
    def set_pin_configuration(self, pins: Dict[str, int] ) -> None:
        pass

    @abstractmethod
    def sleep(self) -> None:
        pass

    @abstractmethod
    def wakeup(self) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def transmit(self, command: bytes) -> None:
        pass

    @abstractmethod
    def receive(self, timeout_sec: float):
        pass

class Mipot32001353(WirelessModule):
    _pin_configuration = dict()
    _valid_indications = [0x41, 0x47, 0x48, 0x49]
    _indication_queue: queue.Queue = queue.Queue(32)
    _valid_commands = [
            0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36,
            0x40, 0x42, 0x43, 0x44, 0x45, 0x46, 0x4A, 0x4B,
            0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x57, 0x58]

    def __init__(self, pins: Dict[str, int], port: str):
        self.set_pin_configuration(pins)
        self._uart = serial.Serial(port=port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=False, dsrdtr=False)
        GPIO.setup(self._pin_configuration['wakeup'], GPIO.OUT)
        GPIO.setup(self._pin_configuration['reset'], GPIO.OUT)

    def tx_msg(self, data: bytes, fport: int, confirmed: bool) -> int:
        """ Transmit a message
        args:
        - data (bytes): data to be transmitted
        - fport (int): LoRaWAN frame port (1-223)
        - confirmed (bool): Request confirmation
        returns:
        - status (int): 0: success
                        1: device busy
                        2: device not activated
                        3: channel blocked by duty cycle
                        4: port number not supported
                        5: length not supported
                        6: end node in silent state
                        7: error
        """

        if fport < 1 or fport > 223:
            raise ValueError('Bad fport')
        if len(data) > 209:
            raise ValueError('data length too big')
        if len(data) == 0:
            raise ValueError('nothing to transmit')

        if confirmed:
            options = 1
        else:
            options = 0

        cmd = b'\x46' + bytes([len(data) + 2, options, fport]) + data
        try:
            self.transmit(cmd)
            response = self._get_reply(0x46, 1, 0.25)
        finally:
            self.sleep()

        return response[2]


    @staticmethod
    def parse_join_indication(indication: bytes) -> Dict[str, Union[str, bool]]:
        """ Parse a join indication
         args:
        - indication (bytes): A message confirmed indication
        returns dict with the following keys:
        - indication (str): 'tx_msg_con'
        - success (bool): True on success
        """

        if len(indication) != 3:
            raise ValueError('Wrong length for join indication')
        if indication[0] != 0x41:
            raise ValueError('Not a join indication')
        return {
                'indication': 'join',
                'success': (indication[2] == 0)
                }


    def set_pin_configuration(self, pins: Dict[str, int]) -> None:
        self._pin_configuration |= pins

    def sleep(self) -> None:
        GPIO.output(self._pin_configuration['wakeup'],GPIO.HIGH)

    def wakeup(self) -> None:
        GPIO.output(self._pin_configuration['wakeup'],GPIO.LOW)

    def reset(self) -> None:
        GPIO.output(self._pin_configuration['reset'],GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self._pin_configuration['reset'],GPIO.HIGH)
        time.sleep(2)
        return


    def transmit(self, command: bytes) -> None:
        # add 0xAA to the beginning of the command
        to_transmit = b'\xaa' + command

        # Calculate checksum
        checksum = 0
        for value in to_transmit:
            checksum += value

        checksum = ((checksum ^ 0xFF) + 1) & 0xFF

        # Append checksum
        to_transmit += bytes([checksum])

        self.wakeup()

        # command reference says we should wait 1ms
        time.sleep(0.001)

        self._uart.write(to_transmit)
        
        return

    def receive(self, timeout_sec: float, expected_cmd_reply: Optional[int]) -> Tuple[bytes, bool]:
        """ Receives data from device.
        Args:
        - timeout_msec (int): Number of seconds to wait for data. May be fractions of a second but not zero.
        - expected_cmd_reply (int): The expected reply. After sending a command, it should be set to the expected reply. Can be None.
        Returns:
        - Either expected command reply or an indication
        - Boolean, True when an indication is returned
        Raises:
        - TimeoutError
        """

        # Sanity check.
        if timeout_sec <= 0:
            raise ValueError('Timeout cannot be less or equal zero')

        # Calculate timeout
        now = time.clock_gettime(time.CLOCK_MONOTONIC)
        timeout = now + timeout_sec

        # Checksum OK?
        checksum_ok = False
        while not checksum_ok:
            # Get start of a command
            got_command = False
            while not got_command:
                # Wait for sync byte
                now = time.clock_gettime(time.CLOCK_MONOTONIC)
                while timeout > now:
                    self._uart.timeout = timeout - now
                    sync_byte = self._uart.read(size=1)
                    if len(sync_byte) != 1:
                        raise TimeoutError('Waiting for sync byte timed out')
                    if sync_byte[0] == 0xAA:
                        break
                    now = time.clock_gettime(time.CLOCK_MONOTONIC)

                # Get command byte. 0xAA is not a valid command reply or indication.
                # Skip superfluous 0xAA bytes but resync to 0xAA on other
                # unexpected command-reply or indication codes.
                command_byte = bytes([0xAA])
                while command_byte[0] == 0xAA:
                    now = time.clock_gettime(time.CLOCK_MONOTONIC)
                    self._uart.timeout = timeout - now
                    command_byte = self._uart.read(size=1)
                    if len(command_byte) != 1:
                        raise TimeoutError('Waiting for command byte timed out')
                    if expected_cmd_reply is not None:
                        if command_byte[0] == expected_cmd_reply or command_byte[0] in self._valid_indications:
                            got_command = True
                            break
                    elif (command_byte[0] & 0x7F in self._valid_commands and command_byte[0] & 0x80 == 0x80) or command_byte[0] in self._valid_indications:
                        got_command = True
                        break

            # Get length byte
            now = time.clock_gettime(time.CLOCK_MONOTONIC)
            if now >= timeout:
                raise TimeoutError('Waiting for length byte timed out')
            self._uart.timeout = timeout - now
            length_byte = self._uart.read(size=1)
            if len(length_byte) == 0:
                raise TimeoutError('Waiting for length byte timed out')

            # Receive remaining bytes
            now = time.clock_gettime(time.CLOCK_MONOTONIC)
            if now >= timeout:
                raise TimeoutError('Timeout while reading remaining bytes')
            self._uart.timeout = timeout - now
            bytes_to_read = length_byte[0] + 1
            further_bytes = self._uart.read(bytes_to_read)
            if len(further_bytes) != bytes_to_read:
                raise TimeoutError('Timeout while reading remaining bytes')

            # Calculate checksum
            checksum = 0xAA + command_byte[0] + length_byte[0]
            for value in further_bytes:
                checksum += value

            # Checksum OK?
            checksum_ok = ((checksum & 0xFF) == 0)

        # Return result
        result = command_byte + length_byte + further_bytes[0:-1]
        return (result, command_byte[0] in self._valid_indications)
    
    def _get_reply(self, command: int, expected_len: Optional[int], timeout_seconds: float) -> bytes:
        got_reply = False
        num_retries = 8
        while not got_reply and num_retries > 0:
            num_retries -= 1
            (data, is_indication) = self.receive(timeout_seconds, command | 0x80)
            if is_indication:
                try:
                    self._indication_queue.put(data, block=False)
                except queue.Full:
                    pass
            elif expected_len is None or data[1] == expected_len:
                got_reply = True

        return data

    def get_fw_version(self) -> int:
        try:
            self.transmit(b'\x34\x00')
            response = self._get_reply(0x34, 4, 0.25)
        finally:
            self.sleep()

        return int.from_bytes(response[2:6], 'little', signed=False)

    def get_serial_no(self) -> int:
        try:
            self.transmit(b'\x35\x00')
            response = self._get_reply(0x35, 4, 0.25)
        finally:
            self.sleep()

        return int.from_bytes(response[2:6], 'little', signed=False)

    def get_deveui(self) -> bytes:
        try:
            self.transmit(b'\x36\x00')
            response = self._get_reply(0x36, 8, 0.25)
        finally:
            self.sleep()

        eui = response[2:10]

        return eui[::-1]
    
    def set_app_key(self, app_key: bytes) -> None:
        """ Write the application key needed for OTAA to eeprom
        Args:
        - app_key (bytes): 16 bytes application key
        """

        if len(app_key) != 16:
            raise ValueError('app key must be exactly 16 bytes long')

        cmd = b'\x43\x10' + app_key[::-1]
        try:
            self.transmit(cmd)
            self._get_reply(0x43, 0, 2)
        finally:
            self.sleep()

        return

    def get_indication(self, timeout_seconds: Optional[int]) -> Optional[bytes]:
        if self._indication_queue.empty():
            self.wakeup()
            try:
                (data, is_indication) = self.receive(timeout_seconds, None)
            except TimeoutError:
                return None
            if not is_indication:
                raise RuntimeError('Got unexpected command reply 0x%02X' % (data[0]))
            return data
        else:
            return self._indication_queue.get(block=False)

    def set_ch_parameters(self, channel: int, frequency: int, min_data_rate: int, max_data_rate: int, enabled: bool) -> int:
        """ Set channel parameters
        args:
        - channel (int): Channel index, from 3-15
        - frequency (int): Frequency in hertz, from 863.125 MHz to 869.875 MHz
        - min_data_rate (int): Minimum data rate 0-7, 0=SF12/125Khz, 5=SF7/125kHz, 6=SF7/250kHz, 7=FSK/50kHz
        - max_data_rate (int): Maximum data rate
        - enabled (bool): Channel enabled?
        returns:
        - status (int): 0x00: Success
                        0xF1: channel out of range
                        0xF2: data rate out of range
                        0xF3: data rate and frequency out of range
                        0xF4: MAC busy
        """

        if channel < 3 or channel > 15:
            raise ValueError('Bad channel')

        if min_data_rate > max_data_rate:
            raise ValueError('Minimum data rate higher than maximum data rate')

        if min_data_rate < 6:
            bandwidth = 125000
        elif min_data_rate == 6:
            bandwidth = 250000
        elif min_data_rate == 7:
            bandwidth = 50000
        else:
            raise ValueError('Bad minimal data rate')

        if max_data_rate < 0 or max_data_rate > 7:
            raise ValueError('Bad maximal data rate')
        if max_data_rate == 6 and bandwidth < 250000:
            bandwidth = 250000

        if frequency - bandwidth / 2 < 863000000:
            raise ValueError('Frequency too low')
        if frequency + bandwidth / 2 > 869000000:
            raise ValueError('Frequency too high')

        data_rate = min_data_rate | (max_data_rate << 4)

        if enabled:
            enabled_parm = b'\x01'
        else:
            enabled_parm = b'\x00'

        cmd = b'\x57\x07' + bytes([channel]) + frequency.to_bytes(4, 'little', signed=False) + bytes([data_rate]) + enabled_parm

        try:
            self.transmit(cmd)
            response = self._get_reply(0x57, 1, 0.55)
        finally:
            self.sleep()

        return response[2]

    def get_parsed_indication(self, timeout_seconds: Optional[int]) -> Optional[Dict[str, Union[str, int, bool]]]:
        """ Get a indication as dictionary
        args:
        - timeout_seconds (int): Timeout in seconds or None
        Returns:
        - Dict with a parsed indication
        """

        indication = self.get_indication(timeout_seconds)

        if indication is None:
            return None

        if indication[0] == 0x41:
            return self.parse_join_indication(indication)

        if indication[0] == 0x47:
            return self.parse_tx_msg_confirmed_indication(indication)

        if indication[0] == 0x48:
            return self.parse_tx_msg_unconfirmed_indication(indication)

        if indication[0] == 0x49:
            return self.parse_rx_msg_indication(indication)

        raise RuntimeError('Unexpected indication 0x%02X' % (indication[0]))

    def join(self, mode: int) -> int:
        """ Join the LoRaWAN network
        args:
        - mode: 0: ABP
                1: OTAA
        Return:
        - int: 0: Success
                1: Invalid parameter
                2: Busy
        """

        if mode < 0 or mode > 1:
            raise ValueError('Bad mode')

        cmd = b'\x40\x01' + bytes([mode])
        try:
            self.transmit(cmd)
            response = self._get_reply(0x40, 1, 0.25)
        finally:
            self.sleep()

        return response[2]

    def get_activation_status(self) -> int:
        """ Get activation status
        Returns:
        - int: 0: Not activated
               1: Joining
               2: Joined
               3: MAC error
        """

        try:
            self.transmit(b'\x42\x00')
            response = self._get_reply(0x42, 1, 0.25)
        finally:
            self.sleep()

        return response[2]

    def eeprom_write(self, start_address: int, data: bytes) -> bool:
        if start_address > 0xFF:
            raise ValueError('Bad start address')
        if len(data) > 0xFE:
            raise ValueError('Data too long')
        if start_address + len(data) > 0xFF:
            raise ValueError('Data too long for start address')

        cmd = b'\x32' + bytes([len(data) + 1, start_address]) + data
        try:
            self.transmit(cmd)
            response = self._get_reply(0x32, 1, 1)
        finally:
            self.sleep()

        return response[2] == 0x00

    def eeprom_read(self, start_address: int, num_bytes: int) -> Optional[bytes]:
        if start_address > 0xFF:
            raise ValueError('Bad start address')
        if start_address + num_bytes > 0x100:
            raise ValueError('Too many bytes requested')

        cmd = b'\x33\x02' + bytes([start_address, num_bytes])

        try:
            self.transmit(cmd)
            response = self._get_reply(0x33, None, 1)
        finally:
            self.sleep()

        if response[1] != num_bytes + 1 or response[2] != 0x00:
            return None

        return response[3:]

    def __del__(self):
        self._uart.close()
        for item in self._pin_configuration.values():
            GPIO.cleanup(item)
