# Testing serial communication over Advantech USB-5830
import sys
sys.path.append('..')
import time
from Automation.BDaq import *
from Automation.BDaq.InstantDiCtrl import InstantDiCtrl
from Automation.BDaq.InstantDoCtrl import InstantDoCtrl
from Automation.BDaq.BDaqApi import AdxEnumToString, BioFailed
from Automation.BDaq.CommonUtils import kbhit

deviceDescription = "USB-5830,BID#0"
profilePath = u"../../profile/DemoDevice.xml"

startPort = 0
portCount = 2
portCountOutput = 1

inputList = ['0x1', '0x2', '0x4', '0x8', '0x10', '0x20', '0x40', '0x80']
outputList = ['0x1', '0x2', '0x4', '0x8', '0x10', '0x20', '0x40', '0x80']

outputListDec = [[0], [1], [2], [4], [8], [16], [32], [64], [128]]


IN_port0_0 = inputList[0]  #"mainswitch"
IN_port0_1 = inputList[1]  #"opp_port-open"
IN_port0_2 = inputList[2]  #"ned_port-close"
IN_port0_3 = inputList[3] #"opp_luke"
IN_port0_3 = inputList[4] #"ned_luke"

OUT_port0_0 = outputList[0] # Simulere åpne port
OUT_port0_1 = outputList[1] # Simulere åpne luke

# Manual open gate at terminal A
TEAID_MCMD_MOG = 0xDA #b'11011010'

# Manual close gate at terminal A
TEAID_MCMD_MCG = 0xDB #b'11011011'

# Manual open hatch at terminal A 
TEAID_MCMD_MOH = 0xDC #b'11011100'

# Manual close hatch at terminal A
TEAID_MCMD_MCH = 0xDD #b'11011101'

# Docking ready at terminal A
TEAID_DRDY_READY = 0xD5 #b'11010101'




def writingToOutput(device, profilePath, outList, startPort, portCount, outPin):
    ret = ErrorCode.Success
    
    instantDoCtrl = InstantDoCtrl(device)
    instantDoCtrl.loadProfile = profilePath
        
    ret = instantDoCtrl.writeAny(startPort, portCount, outList[outPin])
    instantDoCtrl.dispose()
    return 0

def readingFromInput(device, profilePath, inputList, startPort, portCount):
    ret = ErrorCode.Success
    
    instantDiCtrl = InstantDiCtrl(device)
    instantDiCtrl.loadProfile = profilePath
    
    while not kbhit():
        ret, data = instantDiCtrl.readAny(startPort, portCount)
        if BioFailed(ret):
            break

        if data[0] != 0:
            indexPort = inputList.index(hex(data[0]))
            #print(indexPort)
            return indexPort
        
        if data[1] != 0:
            indexPort = inputList.index(hex(data[1])) + 8
            #print(indexPort)
            return indexPort
    
    instantDiCtrl.dispose()
    
    if data[0] or data[1] == 0:
        return 0
    
   
# Manual gate-control
def manualGateControl(argInput, argPort, argFerryAtDock):
    if argFerryAtDock:
            # write.to.serial.com -> TEAID_MCMD_MOG
        writingToOutput(deviceDescription, profilePath, outputListDec, startPort, portCountOutput, argPort)
        
 # Manual gate-control   
#def manualSignalToFerry(terminal, signal):


    
def main():
    testvalue = readingFromInput(deviceDescription, profilePath, outputList, startPort, portCount)
    print(testvalue)
    
    if testvalue == 0:
        manualGateControl(0, 1, True)
    else:
        writingToOutput(deviceDescription, profilePath, outputListDec, startPort, portCountOutput, 0)
    


if __name__ == "__main__":
    while True:
        main()
