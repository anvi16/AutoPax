import socket
from serial import Serial
from serial.threaded import ReaderThread, Protocol
from playsound import playsound
import threading
import sys
import os
import time
from pydub import AudioSegment
from pydub.playback import play

# Set up serial
serial_port = Serial('/dev/ttyTHS1')  # COMxx   format on Windows
# ttyUSBx format on Linux

serial_port.baudrate = 115200  # set Baud rate to 115200
serial_port.bytesize = 8  # Number of data bits = 8
serial_port.parity = 'N'  # No parity
serial_port.stopbits = 1  # Number of Stop bits = 1
serial_port.timeout = 1

# ----------------------------------------------- #

# Set up UDP
UDP_IP_RX = "0.0.0.0"
UDP_PORT_RX = 2022

UDP_IP_TX = "192.168.10.101"
UDP_PORT_TX = 2021

try:
    sock_rx = socket.socket(socket.AF_INET,  # Internet
                            socket.SOCK_DGRAM)  # UDP

    sock_tx = socket.socket(socket.AF_INET,  # Internet
                            socket.SOCK_DGRAM)  # UDP

    sock_rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock_rx.bind((UDP_IP_RX, UDP_PORT_RX))

except OSError as msg:
    global sock_tx
    global sock_rx
    sock_tx.close()
    sock_rx.close()
    print(msg)
    print('Could not open socket')
    sys.exit(1)

# ----------------------------------------------- #
# Global variabeles
play_noice_warning = False
play_audio_warning = False
play_audio_warning_stop = False

audio_path = "/home/nvidia/AutoPAX/Audio/"

beep_warning = AudioSegment.from_mp3(audio_path + "warning-sound.mp3")
sensor_block_warning = AudioSegment.from_mp3(audio_path + "beat.mp3")


# ----------------------------------------------- #


# Help functions

# Kilde https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


# Kilde https://stackoverflow.com/questions/70625801/threading-reading-a-serial-port-in-python-with-a-gui
class SerialReaderProtocolRaw(Protocol):

    def connection_made(self, transport):
        """Called when reader thread is started"""
        print("Connected, ready to receive data..." + '\n')

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        try:
            # Convert data from 1 byte to int
            packet = int.from_bytes(data, 'big')

            if packet > 255:  # Skip corrupt data, larger than 1 byte
                raise Exception("Incoming serial data too big, skipping")

            # Convert Int to binary bytes and remove prefix 'b0'
            packet = remove_prefix(bin(packet), '0b')

            # Send packet to packet-handler
            packet_handler_serial(packet)

        except Exception as e:
            print(e)


class udp_thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(udp_thread, self).__init__(*args, **kwargs, daemon=True)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while not self.stopped():
            packet_handler_UDP()

        return


def encode_SAMr34_UART(arg1, arg2, arg3):  # To bytearray
    # Pack struct:
    # REID 2-bit|SEID 2-bits|DATA 4-bits
    arg1 = format(arg1, '0>2b')
    arg2 = format(arg2, '0>2b')
    arg3 = format(arg3, '0>4b')
    bit_str = arg1 + arg2 + arg3

    # Convert from bitstring to ascii, 10-system
    packet = bytes(bit_str, 'ascii')

    # Int to binary 2-system
    packet = int(packet, 2)

    # Binary to 1 Byte, MSB left (big)
    packet = packet.to_bytes(1, 'big')

    print("Data encoded serial: {}".format(packet))
    return packet


def decode_SAMr34_UART(data):  # To (hex | hex | hex)
    # Make data fixed 8-bits
    data = data.zfill(8)

    # Packet struct:
    # REID 2-bit|SEID 2-bits|DATA 4-bits
    # 00|00|0000 bits
    arg1 = data[:2]
    arg2 = data[2:4]
    arg3 = data[4:]

    print("Data decoded serial: {}".format(data))
    return hex(int(arg1, 2)), hex(int(arg2, 2)), hex(int(arg3, 2))


# https://code.activestate.com/recipes/576789-nmea-sentence-checksum/
def calc_NEMA_checksum(sentence):
    calc_cksum = 0
    for char in sentence:
        calc_cksum ^= ord(char)

    return hex(calc_cksum)


def decode_NMEA_sentence(sentence):
    # Validate NMEA string
    nmeadata = ""

    try:
        # Decode packet
        sentence = sentence.decode()

        end_str = sentence.find('\r\n')

        if end_str == -1:
            raise Exception("Empty string or no end")

        if not sentence[0] == '$':
            raise Exception("Not starting with '$' symbol")

        if sentence.find('*') == -1:
            raise Exception("Missing '*' symbol")

        if sentence.find(',') == -1:
            raise Exception("Missing ',' symbol")

        # Remove any bad expected characters
        sentence = sentence.strip('$')
        sentence = sentence.strip('\r\n')

        # Split out checksum from sentence
        nmeadata, cksum = sentence.split('*')

        # Give checksum prefix
        cksum = '0x' + cksum

        # Calculate checksum
        calc_cksum = calc_NEMA_checksum(nmeadata)

        # Verify checksum (will report checksum error)
        if cksum != str(calc_cksum):
            raise ValueError("Error: checksum not equal for incoming: {} {} != {}".format(nmeadata, cksum, calc_cksum))

        # Checksum ok
        else:
            print("Checksums are {} and {}".format(cksum, calc_cksum))

    except ValueError as ve:
        print(ve)
        nmeadata = ""

    except Exception as e:
        print(e)

    return nmeadata


def decode_NMEA_payload(payload_str):
    ID, REID, SEID, DATA = payload_str.split(',')
    return ID, int(REID, 16), int(SEID, 16), int(DATA, 16)


# ----------------------------------------------- #


# Response function for serial data

# Receive bitstream from serial port
#                |
#                |
#               \_/
# Send through data to io-machine
#                |
#                |
#               \_/
# Execute actions on pc in correspondence


def packet_handler_serial(data):
    # Decode data
    REID, SEID, STATE = decode_SAMr34_UART(data)

    # Send to I/O-machine
    data_string = "AUTOPAXFB,{},{},{}".format(REID, SEID, STATE)
    # data_string = "WAGOHATCHFB,0,1,2,0,0,2,2,0,0"

    # Calculate checksum
    calc_cksum = calc_NEMA_checksum(data_string)

    NMEA_str = "${}*{}\r\n".format(data_string, remove_prefix(calc_cksum, '0x'))
    print("Sending UDP packet: {}".format(NMEA_str))

    sock_tx.sendto(NMEA_str.encode('ascii'), (UDP_IP_TX, UDP_PORT_TX))


# Do something useful


def packet_handler_UDP():
    # Start listening to UDP stream from I/O-machine

    # Receive bitstream from io-machine
    #                |
    #                |
    #               \_/
    # Send through data to serial port
    #                |
    #                |
    #               \_/
    # Execute actions on pc in correspondence

    payload, addr = sock_rx.recvfrom(1024)  # buffer size is 1024 bytes
    print("received message: %s" % payload)

    # Handel incoming packets
    NMEA_payload = decode_NMEA_sentence(payload)

    if NMEA_payload == "":  # Not a valid message
        return

    # Get commands from string
    tag, receiver_id, sender_id, req = decode_NMEA_payload(NMEA_payload)

    # Check receiver
    if tag == 'AUTOPAX':
        # Send to request to terminal
        if req <= 0xf:  # 0x10 and above is reserved for Autopax pc
            byte_packet = encode_SAMr34_UART(receiver_id, sender_id, req)
            serial_reader.write(byte_packet)  # transmit (8bit) to SAM R34

        # Do something useful locally
        else:
            try:
                global play_noice_warning
                global play_audio_warning
                global play_audio_warning_stop

                # Decode command
                # 0x10 - play noise
                if req == 0x10:
                    print("Play noice-warning")
                    play_noice_warning = True

                # 0x11 - stop noise
                if req == 0x11:
                    print("Stop noice-warning")
                    play_noice_warning = False

                # 0x12 - play warning (sensor blocked)
                if req == 0x12:
                    play_audio_warning = True

                if req == 0x97:
                    play_audio_warning_stop = True

                if req == 0x98:
                    playsound(audio_path + "The_Lagoons_-_California.mp3", block=False)

                if req == 0x99:
                    playsound(audio_path + "Pirates_Of_The_Caribbean.mp3", block=False)

            except Exception as e:
                print("In request {}, exception: {}".format(hex(req), e))

    else:
        print("Packet is not for us ")


# Main thread
if __name__ == '__main__':
    try:
        # Start listening thread to serial from SAM R34
        serial_reader = ReaderThread(serial_port, SerialReaderProtocolRaw)
        serial_reader.start()

        # Start listening thread to udp packets from Ethernet
        # udp_reader = threading.Thread(target=packet_handler_UDP, daemon=True)
        # udp_reader.start()
        udp_reader = udp_thread()
        udp_reader.start()

        # Implement local events
        while True:
            try:
                if play_noice_warning:
                    play(beep_warning)
                # playsound(audio_path + "warning-sound.mp3", block = False)
                # os.system(audio_path + "warning-sound.mp3")
                # time.sleep(1.2)

                if play_audio_warning:
                    print("Play audio-warning")
                    play(sensor_block_warning)
                    # playsound(audio_path + "beat.mp3", block = False)
                    # os.system("mpg123 " + file)
                    play_audio_warning = False

                if play_audio_warning_stop:
                    print("Stop audio-warning")

                    play_audio_warning_stop = False

            except Exception as e:
                print(e)

    except KeyboardInterrupt as ki:
        print(ki)
        print("End script")

    except Exception as e:
        print(e)

serial_reader.close()  # Close the port
udp_reader.stop()
sock_rx.close()
sock_tx.close()

# exit()