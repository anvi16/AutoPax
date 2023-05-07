import socket
from serial import Serial
from serial.threaded import ReaderThread, Protocol
import threading

# Set up serial
serial_port = Serial('COM5')  # COMxx   format on Windows
                              # ttyUSBx format on Linux

serial_port.baudrate = 115200  # set Baud rate to 115200
serial_port.bytesize = 8  # Number of data bits = 8
serial_port.parity = 'N'  # No parity
serial_port.stopbits = 1  # Number of Stop bits = 1
serial_port.timeout = 1

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

    def connection_made(self, transport):
        """Called when reader thread is started"""
        print("Connected, ready to receive data..." + '\n')

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        # Convert data from 1 byte to int
        packet = int.from_bytes(data, 'big')

        if packet > 255:  # Skip corrupt data, larger than 1 byte
            return

        # Convert Int to binary bytes and remove prefix 'b0'
        packet = bin(packet).removeprefix('0b')

        # Send packet to packet-handler
        packet_handler_serial(packet)


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
            raise Exception("Empty string")

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
        cksum = '0x'+cksum

        # Calculate checksum
        calc_cksum = calc_NEMA_checksum(nmeadata)

        # Verify checksum (will report checksum error)
        if cksum != str(calc_cksum):
            raise ValueError("Error: checksum not equal for incoming: {} {} != {}".format(nmeadata, cksum, calc_cksum))

    except Exception as e:
        print(e)

    else:
        # Checksum ok
        print("Checksums are {} and {}".format(cksum, calc_cksum))

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

    NMEA_str = "${}*{}\r\n".format(data_string, calc_cksum.removeprefix('0x'))
    print(NMEA_str)

    sock_tx.sendto(NMEA_str.encode('ascii'), (UDP_IP, UDP_PORT_TX))

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

    while True:
        payload, addr = sock_rx.recvfrom(1024)  # buffer size is 1024 bytes
        print("received message: %s" % payload)

        # Handel incoming packets
        NMEA_payload = decode_NMEA_sentence(payload)

        if NMEA_payload == "":  # Not a valid message
            continue

        # Get commands from string
        tag, receiver_id, sender_id, req = decode_NMEA_payload(NMEA_payload)

        # Check receiver
        if tag == 'AUTOPAX':
            # Send to request to terminal
            if req <= 0x15:  # 0x16 and above is reserved for Autopax pc
                byte_packet = encode_SAMr34_UART(receiver_id, sender_id, req)
                serial_reader.write(byte_packet)  # transmit (8bit) to SAM R34

            # Do something useful locally
            # 0x16 - play noise
            # 0x17 - stop noise
            # 0x18 - play warning (sensor blocked)
            else:
                1
                # Decode command and play audio
        else:
            print("Packet is not for us ")


# Main thread
if __name__ == '__main__':
    # Start listening thread to serial from SAM R34
    serial_reader = ReaderThread(serial_port, SerialReaderProtocolRaw)
    serial_reader.start()

    # Start listening thread to udp packets from Ethernet
    udp_reader = threading.Thread(target=packet_handler_UDP)
    udp_reader.start()

    # Wait until thread 1 is completely executed
    udp_reader.join()

    # Implement local events
    #   while True:
    #       Command reader
    #       Audio player
    #       Remove join() above

    # encode_SAMr34_UART(0x1,0x2,0x3)
    # decode_SAMr34_UART(b'100011')
    # serial_reader.write(b'01110010')

    serial_reader.close()  # Close the port
