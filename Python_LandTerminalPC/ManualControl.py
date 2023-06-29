#
# Manuell styring av porter
#
#
import socket

from serial import Serial
from serial.threaded import ReaderThread, Protocol


# Set up serial
serial_port = Serial('COM9')  # COMxx   format on Windows
                              # ttyUSBx format on Linux

serial_port.baudrate = 115200  # set Baud rate to 115200
serial_port.bytesize = 8  # Number of data bits = 8
serial_port.parity = 'N'  # No parity
serial_port.stopbits = 1  # Number of Stop bits = 1

# -----------------------------------------------------


def manual_ferry_hatch_open(terminal, s1, sclopenhatch, bytearray_hatchopen, bytearray_hatchopened):
    if terminal == 'A':
        # Manual open hatch at terminal A 
        #TEAID_MCMD_MOH = 0xDC #11011100
        if s1 or sclopenhatch:
            if bytearray_hatchopened != b'hatchstate-opened':
                serial_port.write(b'11011100')
                serial_port.close()


def manual_ferry_hatch_close(terminal, s2, sclclosehatch, bytearray_hatchclose, bytearray_hatchclosed, bytearray_ferrygatestate):
    if terminal == 'A':
        if s2 or sclclosehatch:
            # Breaks if ferry gate is open, prevent collision
            if bytearray_ferrygatestate != b'01111110':
                # If hatch is not already closed, close it
                if bytearray_hatchclosed != b'hatshstate-open':
                    serial_port.write(b'')
                    serial_port.close()
               
def manual_gate_open(terminal, s3, sclopengate, bytearray_hatchopen, bytearray_ferrygatestate):
    if terminal == 'A':
        if s3 or sclopengate:
            # If hatch is open, you can go further
            if bytearray_hatchopen == b'open':
                # If gate is already open, breaks loop
                if bytearray_ferrygatestate != b'01111110':
                    serial_port.write(b'')
                    serial_port.close()  

def manual_gate_close(terminal, s4, sclclosegate, bytearray_ferrygatestate):
    if terminal == 'A':
        if s4 or sclclosegate:
            if bytearray_ferrygatestate != b'01111111':
                serial_port.write(b'')
                serial_port.close()
    
