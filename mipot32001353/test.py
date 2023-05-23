
import time
import serial
import RPi.GPIO as GPIO
from wirelessModule import WirelessModule, Mipot32001353


def show_hex(msg, data: bytes) -> None:
    print(msg, end='')
    for v in data:
        print(' %02X' % (v), end='')
    print('')

    return

GPIO.setmode(GPIO.BOARD)

mipot = Mipot32001353({'wakeup':8, 'reset': 5}, '/dev/ttyS0')

time.sleep(1)
mipot.reset()
time.sleep(1)
mipot.transmit(b'\x30\x00') # reset by command
time.sleep(1)
# Get version
module_version = mipot.get_fw_version()
print('Module version: %x' % (module_version))

# # Get serial number
# serial_number = mipot.get_serial_no()
# print('Module serial: %d' % (serial_number))

# # Get device EUI
# device_eui = mipot.get_deveui()
# show_hex('Device EUI:', device_eui)

# # Get AppEUI / Join EUI
# join_eui = mipot.eeprom_read(0x08, 8)[::-1]
# show_hex('Join EUI:', join_eui)

# # Get Class
# lora_class = mipot.eeprom_read(0x20, 1)
# if lora_class[0] == 0:
#     print('Class: A')
# elif lora_class[0] == 1:
#     print('Class C')
# else:
#     print('Unknown class: 0x%02X' % (lora_class[0]))

# # ADR active?
# adr = mipot.eeprom_read(0x23, 1)
# if adr[0] == 0:
#     print('ADR disabled')
# else:
#     print('ADR enabled')

# # Unconfirmed transmit message repeat setting
# tx_repeat = mipot.eeprom_read(0x25, 1)
# print('Unconfirmed message repeat: %d' % (tx_repeat[0]))

# # Public network?
# public_net = mipot.eeprom_read(0x2E, 1)
# if public_net[0] == 0:
#     print('Network: private')
# elif public_net[0] == 1:
#     print('Network: public')
# else:
#     print('Unknown network config: 0x%02X' % (public_net[0]))

# # Write application key
# mipot.set_app_key(bytes.fromhex("64E9F222257C902279A9348A6FC9E316"))

# # Main powered
# #mipot.set_battery_level(0)


# # Initiate join
# result = mipot.join(1)
# if result != 0:
#     print('Join command failed with code %d' % result)
    
# print('Join in progress')

# # Wait for join indication
# now = time.clock_gettime(time.CLOCK_MONOTONIC)
# timeout = now + 180

# got_join = False
# while not got_join and timeout > now:
#     indication = mipot.get_parsed_indication(int(timeout - now))
#     if indication is not None and indication['indication'] == 'join':
#         got_join = True
#         break
#     now = time.clock_gettime(time.CLOCK_MONOTONIC)

# if not got_join:
#     print('Timeout while waiting for join indication')
#     mipot.reset()

# if indication != None and indication['success']:
#     print('Join OK')
# else:
#     print('Join failed')


# result = mipot.tx_msg(b'\x01\x23\x45\x67\x89\xAB\xCD\xEF', 1, False)
# if result != 0:
#     print('Sending failed with error code %s' % (result))

time.sleep(1)
