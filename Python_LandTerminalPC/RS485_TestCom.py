"""Ferry and Terminal indentifier"""
# Ferry identifier
FEID = 0xC0 #11000000

# Terminal A identifier
TEAID = 0x40 #010000000

# Terminal B identifier	
TEBID = 0x80 #10000000

# Ferry in transmit between terminals
IN_TRANSIT = 0xA0 #10100000

"""Gate states"""
# Terminal A Timeout
TEAID_GSTATE_TIMEOUT = 0xD1 #11010001

# Terminal A Open
TEAID_GSTATE_OPEN = 0xD2 #11010010

# Terminal A Close
TEAID_GSTATE_CLOSE = 0xD3 #11010011

# Terminal A Pause
TEAID_GSTATE_PAUSE = 0xD4 #11010100

#Terminal B Timeout
TEBID_GSTATE_TIMEOUT = 0xE1 #11100001

# Terminal B Open 
TEBID_GSTATE_OPEN = 0xE2 #11100010
 
# Terminal B Close
TEBID_GSTATE_CLOSE = 0xE3 #1110001

# Terminal B Pause
TEBID_GSTATE_PAUSE = 0xE4 #11100100

"""Docking ready"""
# Docking ready at terminal A
TEAID_DRDY_READY = 0xD5 #11010101

# Docking not ready at terminal A
TEAID_DRDY_NREADY = 0xD6 #11010110

# Docking ready at terminal B
TEBID_DRDY_READY = 0xE5 #11100101

# Docking not ready at terminal B
TEBID_DRDY_NREADY = 0xE6 #11100110

"""Gap Clear"""
# Cap clear at terminal A
TEAID_GPCLEAR_READY = 0xD7 #11010111

# Cap not clear at terminal A
TEAID_GPCLEAR_NREADY = 0xD8 #11011000

# Cap clear at terminal B 
TEBID_GPCLEAR_READY = 0xE7 #11100111

# Cap not clear at terminal B
TEBID_GPCLEAR_NREADY = 0xE8 #11101000

"""Manual Stop"""
# Manual stop pushed at terminal A
TEAID_MSTP_PUSHED = 0xD9 #11011001

# Manual stop pushed at terminal B 
TEBID_MSTP_PUSHED = 0xE9 #11101001


"""Manual Commands"""
# Manual open gate at terminal A
TEAID_MCMD_MOG = 0xDA #11011010

# Manual close gate at terminal A
TEAID_MCMD_MCG = 0xDB #11011011

# Manual open hatch at terminal A 
TEAID_MCMD_MOH = 0xDC #11011100

# Manual close hatch at terminal A
TEAID_MCMD_MCH = 0xDD #11011101

# Manual open gate at terminal B 
TEBID_MCMD_MOG = 0xEA #11101010

# Manual close gate at terminal B 
TEBID_MCMD_MCG = 0xEB #11101011

# Manual open hatch at terminal B 
TEBID_MCMD_MOH = 0xEC #11101100

# Manual close hatch at terminal B
TEBID_MCMD_MCH = 0xED #11101101


"""Gate commands for terminal A"""
# Reset gate at terminal A
TEAID_GCMD_RESET = 0x71 #01110001

# Open gate at terminal A 
TEAID_GCMD_OPEN = 0x72 #01110010

# Close gate at terminal A 
TEAID_GCMD_CLOSE = 0x73 #01110011

# Pause gate at terminal A
TEAID_GCMD_PAUSE = 0x74 #01110100

"""Gate commands for terminal B"""
# Reset gate at terminal B 
TEBID_GCMD_RESET = 0xB1 #10110001

# Open gate at terminal B
TEBID_GCMD_OPEN = 0xB2 #10110010

# Close gate at terminal B
TEBID_GCMD_CLOSE = 0xB3 #10110011

# Pause gate at terminal B
TEBID_GCMD_PAUSE = 0xB4 #10110100


# On-demand" request from Terminal A 
TEAID_REQF_REQUEST = 0xDE #11011110    

# "On-demand" request from Terminal B 
TEBID_REQF_REQUEST = 0xEE #11101110

# Queue update confirmed at Terminal A 
TEAID_CQUD_QCONF = 0x75     #01110101   

# Queue update confirmed at Terminal B
TEBID_CQUD_QCONF = 0xB5	 #10110101   


"""Ferry Request States """ 
# Request people counter at terminal A 
TEAID_FREQS_REQCNT = 0x76 #01110110

# Request docking ready at terminal A
TEAID_FREQS_REQDRDY = 0x77 #01110111

# Request gap clear at terminal A 
TEAID_FREQS_REQGCLR = 0x78 #01111000

# Request gate state at terminal A */
TEAID_FREQS_GSREQ = 0x79 #01111001

# Request people counter at terminal B */
TEBID_FREQS_REQCNT = 0xB6 #10110110

# Request docking ready at terminal B */
TEBID_FREQS_REQDRDY = 0xB7 #10110111

# Request gap clear at terminal B */
TEBID_FREQS_REQGCLR = 0xB8 #10111000

# Request gate state at terminal B */
TEBID_FREQS_GSREQ = 0xB9 #10111001


"""Ferry Process""" 
# Docking complete at terminal A 
TEAID_FPROC_DCOMP = 0x7A #01111010

# Boarding complete at terminal A 
TEAID_FPROC_BCOMP = 0x7B #01111011

# Docking complete at terminal B 
TEBID_FPROC_DCOMP = 0xBA #10111010

# Boarding complete at terminal B 
TEBID_FPROC_BCOMP = 0xBB #10111011

""""Amount of passenger"""
PASSENGERS_ZERO = 0xC0 #11000000
PASSENGERS_ONE = 0xC1  #11000001
PASSENGERS_TWO = 0xC2 #11000010
PASSENGERS_THREE = 0xC3 #11000011
PASSENGERS_FOUR = 0xC4 #11000100
PASSENGERS_FIVE = 0xC5 #11000101
PASSENGERS_SIX = 0xC6 #11000110
PASSENGERS_SEVEN = 0xC7 #11000111
PASSENGERS_EIGHT = 0xC8 #11001000
PASSENGERS_NINE = 0xC9 #11001001
PASSENGERS_TEN = 0xCA #11001010
PASSENGERS_ELEVEN = 0xCB #11001011
PASSENGERS_TWELVE = 0xCC #11001100
PASSENGERS_THRITEEN = 0xCD #11001101
PASSENGERS_FOURTEEN = 0xCE #11001110
PASSENGERS_FIFTEEN = 0xCF #11001111

# Send previous message again
SEND_MESSAGE_AGAIN = 0xAA #10101010

# Emergency
EMERGENCY = 0x0F #00001111

FERRY_GT_OPEN = 0x7E #01111110


import math

def decodePackage(dataStream):
    scale = 16
    numBits = 8



#encodePackage(hex(REID), HEX(SEID), HEX(CMD)):
#	Setter sammen pakker med inngående heksadesimaler.
#	return bitstream

#decodePackage(dataStream):
#	Decoder en pakke av type bitstrøm, decoder 
#	[7:6] - REID
#	[5:4] - SEID
#	[3:0] - STS
#	return reid, seid, sts

#evt.
#timeout():