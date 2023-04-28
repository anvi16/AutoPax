import socket
import re
import bitarray
from serial import Serial
from serial.threaded import ReaderThread, Protocol
import threading

# Set up serial
serial_port = Serial('COM3')  # COMxx   format on Windows
# ttyUSBx format on Linux

serial_port.baudrate = 115200  # set Baud rate to 115200
serial_port.bytesize = 8  # Number of data bits = 8
serial_port.parity = 'N'  # No parity
serial_port.stopbits = 1  # Number of Stop bits = 1

# ----------------------------------------------- #

# Set up UDP
UDP_IP = "127.0.0.1"
UDP_PORT_TX = 2020
UDP_PORT_RX = 2021
MESSAGE = b"$WAGOHATCHFB,0,1,2,0,0,2,2,0,0*53"

sock_rx = socket.socket(socket.AF_INET,  # Internet
                        socket.SOCK_DGRAM)  # UDP

sock_tx = socket.socket(socket.AF_INET,  # Internet
                        socket.SOCK_DGRAM)  # UDP

sock_rx.bind((UDP_IP, UDP_PORT_RX))


# ----------------------------------------------- #


# Help functions

# Kilde https://stackoverflow.com/questions/70625801/threading-reading-a-serial-port-in-python-with-a-gui
class SerialReaderProtocolRaw(Protocol):
    def __init__(self):
        self.buffer = bytearray()

    def connection_made(self, transport):
        """Called when reader thread is started"""
        print("Connected, ready to receive data..." + '\n')

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        # Add incoming snippets to buffer and make sure format is 4-bits (0000)
        self.buffer.extend(data.zfill(4))
        if len(self.buffer) == 8:
            # Send 1 byte data to packet handler
            packet = self.buffer
            listener_serial(packet)
            del self.buffer[:]


# https://code.activestate.com/recipes/576789-nmea-sentence-checksum/
def calc_NEMA_checksum(sentence):
    calc_cksum = 0
    for char in sentence:
        calc_cksum ^= ord(char)

    return calc_cksum


def encode_SAMr34_UART(arg1, arg2, arg3):
    # Packet struct:
    # REID 2-bit|SEID 2-bits|DATA 4-bits
    # 00|00|0000 bits
    arg1 = arg1 << 6
    arg2 = arg2 << 4
    bit_stream_int = arg1 + arg2 + arg3

    # Convert from int to 8-bits
    bit_stream = bin(bit_stream_int)[2:].encode('ascii').zfill(8)

    print(bit_stream)
    return bit_stream


def decode_SAMr34_UART(data):
    # Make sure bitstream is 8bit
    data = data.zfill(8)

    # Packet struct:
    # REID 2-bit|SEID 2-bits|DATA 4-bits
    # 00|00|0000 bits
    arg1 = data[:2]
    arg2 = data[2:4]
    arg3 = data[4:]

    print(data)
    return arg1, arg2, arg3


def decode_NMEA_sentence(sentence):
    # Remove any bad expected characters
    sentence = sentence.strip('\n').strip('$')

    # Split out checksum from sentence
    nmeadata, cksum = sentence.split('*')

    # Calculate checksum
    calc_cksum = calc_NEMA_checksum(nmeadata)

    return nmeadata, '0x' + cksum, hex(calc_cksum)


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


def listener_serial(data):
    # Decode data
    REID, SEID, STATE = decode_SAMr34_UART(data)

    # Send to io-machine
    data_string = "AUTOPAX,{},{},{}".format(REID, SEID, STATE)
    # data_string = "WAGOHATCHFB,0,1,2,0,0,2,2,0,0"

    # Calculate checksum
    calc_cksum = calc_NEMA_checksum(data_string)

    NMEA_str = "${}*{}".format(data_string, hex(calc_cksum)[2:])
    print(NMEA_str)

    sock_tx.sendto(NMEA_str.encode('ascii'), (UDP_IP, UDP_PORT_TX))

    # Do something useful


# Main thread
if __name__ == '__main__':
    # Start listening thread to serial from SAM R34
    reader = ReaderThread(serial_port, SerialReaderProtocolRaw)
    reader.start()

    # listener_serial(b"D")

    # encode_SAMr34_UART(0x1,0x2,0x3)
    # decode_SAMr34_UART(b'100011')

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

    while True:
        payload, addr = sock_rx.recvfrom(1024)  # buffer size is 1024 bytes
        print("received message: %s" % payload)

        # Handel incoming packets
        try:
            # Decode packet
            NMEA_payload, cksum, cksum_calc = decode_NMEA_sentence(payload.decode())

            # Verify checksum (will report checksum error)
            if cksum != str(cksum_calc):
                raise ValueError("Error in checksum for incoming: {}".format(NMEA_payload))
        except Exception as e:
            print(e)

        else:
            # Checksum are ok
            print("Checksums are {} and {}".format(cksum, cksum_calc))

            # Send to terminal
            tag, receiver_id, sender_id, req = decode_NMEA_payload(NMEA_payload)

            bitstream = encode_SAMr34_UART(receiver_id, sender_id, req)

            # serial_port.write(bitstream)  # transmit (8bit) to SAM R34
            serial_port.write(b'01110010')  # transmit (8bit) to SAM R34

            # Do something useful

    reader.stop()
    serial_port.close()  # Close the port
