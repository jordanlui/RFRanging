# -*- coding: utf-8 -*-
"""
DECAWAVE DW1000 CONTROL SOFTWARE (x64)

Created: Tues July 18 15:25 2017
Last updated: Wed Aug 9 14:58 2017
Author: Alex Naylor

FUTURE ADDITIONS:
-Add ability to configure more DW1000 parameters

CHANGELOG (V0.5.0):
AN:
-
"""

#==========================================================================
# IMPORTS
#==========================================================================
import inspect
import serial
import time

from serial.tools import list_ports
from datetime import datetime

#==========================================================================
# CLASS
#==========================================================================
class DW1000(object):
    verNum = "0.5.0"

    #Object initialization        
    def __init__(self):        
        #serial variables
        self.comStr = "USB Serial Port"     #string for BIT devices in device manager
        self.readbackTimeout = 0.5          #how long to wait after writing a command to read the response
        self.openTimeout = 2                #serial open timeout in seconds
        self.readTimeout = 5                #serial read timeout in seconds
        
        #strings printed to serial
        self.antDelayStr = "antDelay: "     #string printed to UART when requesting the antenna delay value
        self.deviceTypeStr = "t:"     #string printed to UART when distance is streamed and we want the device type
        self.peerAddrStr = "f:"         #string printed to UART when distance is streamed and we want the peer device address
        self.rangeStr = "d:"           #string printed to UART when distance is streamed and we want the range
        self.rxPowerStr = "p:"      #string printed to UART when distance is streamed and we want the RX power
        
        #limits
        self.antDelayMin = 0                #minimum antenna delay value 
        self.antDelayMax = (2**16)-1        #maximum antenna delay value 
        
        #other
        self.printDebug = False             #Whether or not to print the debug data to the console

    #==========================================================================
    # CONNECTIVITY FUNCTIONS
    #==========================================================================
    #Connect to the Device Under Test    
    def connectToDUT(self,selPort=None,baudrate=115200):
        if selPort == None:
            self.commonPrint("Trying to establish DUT connection...")
            ports = self.getSerialUSBPorts()
    
            if not ports:          
                self.commonPrint("ERROR: No USB-to-Serial ports available!\n") 
                self.ser = ""            
                return None
            for port in ports:
                tmp = self.initDW1000serial(port,baudrate)
                if tmp:
                    self.commonPrint("DUT connection established.\n")
                    break
                else:
                    return None
        elif selPort != None:
            self.commonPrint("Trying to establish DUT connection on {0}...".format(selPort))         
            tmp = self.initDW1000serial(selPort,baudrate)
            if tmp:
                self.commonPrint("DUT connection established.\n")
            else:
                return None

        return True

    #Find the USB COM ports whose names matching that of the DW1000
    def getSerialUSBPorts(self):
        self.commonPrint("Querying USB ports...")

        ports = []    
        for port in list(serial.tools.list_ports.comports()):
            if self.comStr in port.description:
                ports.append(port.device)
        self.commonPrint("Querying USB ports complete.")       
        self.commonPrint("Ports list = {0}".format(ports))    
        return ports
            
    #Initialize the BIT serial connection
    def initDW1000serial(self,port,baudrate):
        self.commonPrint("Initializing DUT serial connection...")

        try:
            ser = serial.Serial(port, baudrate, timeout=self.openTimeout)
        except Exception as exception:
            self.commonPrint("Could not initialize the serial port...")
            self.commonPrint("ERROR: {0}".format(exception))
            return None
        
        self.ser = ser
        
        self.commonPrint("DUT serial connection initialization complete.")   
        return True

    #Open the BIT serial port
    def openDW1000port(self):
        self.commonPrint("Opening DW1000 serial port...")        

        try:
            self.ser.open()
        except Exception as exception:
            self.commonPrint("Could not open the serial port...")
            self.commonPrint("ERROR: {0}".format(exception))
            return None

        self.commonPrint("Opening DW1000 serial port complete.") 
        return True        

    #Close the BIT serial port
    def closeDW1000port(self):
        self.commonPrint("Closing DW1000 serial port...")

        try: self.ser.close()
        except Exception as exception:
            self.commonPrint("Could not close the serial port...")
            self.commonPrint("ERROR: {0}".format(exception))
            return None

        self.commonPrint("Closing DW1000 serial port complete.") 
        return True     

    #==========================================================================
    # DEVICE INFORMATION FUNCTIONS
    #==========================================================================
    #Read the peer address
    def getPeerAddress(self,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
        
        self.debugPrint("Parsing peer address...")
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None        

        self.ser.reset_input_buffer()   #flush the contents of the input buffer

        startTime = datetime.now()
       
        while True:
            elapsedTime = (datetime.now() - startTime).total_seconds()
            
            if (elapsedTime > timeout):
                self.debugPrint("ERROR: Timeout expired waiting for peer address")
                return None
            
            try: newLine = self.ser.readline().decode(errors="ignore")
            except:
                self.debugPrint("ERROR: Problem reading peer address")
                return None
            
            if (self.peerAddrStr in newLine):
                try: tmp = newLine.split(self.peerAddrStr)[1]
                except: continue
                
                try: peerAddr = tmp.split(" ")[0]
                except: continue
                
                self.debugPrint("Peer address is {0}".format(peerAddr))
                self.debugPrint("Peer address query complete.")

                break

        return peerAddr

    #Read the range value
    def getDeviceType(self,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
        
        self.debugPrint("Parsing devce type...")
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None        

        self.ser.reset_input_buffer()   #flush the contents of the input buffer

        startTime = datetime.now()
       
        while True:
            elapsedTime = (datetime.now() - startTime).total_seconds()
            
            if (elapsedTime > timeout):
                self.debugPrint("ERROR: Timeout expired waiting for device type")
                return None
            
            try: newLine = self.ser.readline().decode(errors="ignore")
            except:
                self.debugPrint("ERROR: Problem reading device type")
                return None
            
            if (self.deviceTypeStr in newLine):
                try: tmp = newLine.split(self.deviceTypeStr)[1]
                except: continue
            
                try: deviceType = tmp.split(" ")[0]
                except: continue
                
                self.debugPrint("Device type is {0}".format(deviceType))
                self.debugPrint("Device type query complete.")

                break

        return deviceType

    #Read the RX power value
    def getRxPowerdBm(self,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
        
        self.debugPrint("Parsing RX power value...")
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None        

        self.ser.reset_input_buffer()   #flush the contents of the input buffer

        startTime = datetime.now()
       
        while True:
            elapsedTime = (datetime.now() - startTime).total_seconds()
            
            if (elapsedTime > timeout):
                self.debugPrint("ERROR: Timeout expired waiting for RX power value")
                return None
            
            try: newLine = self.ser.readline().decode(errors="ignore")
            except:
                self.debugPrint("ERROR: Problem reading RX power value")
                return None
            
            if (self.rxPowerStr in newLine):
                try: tmp = newLine.split(self.rxPowerStr)[1]
                except: continue
                
                try: rxPowerVal = float(tmp.split(" ")[0])
                except: continue
                
                self.debugPrint("RX power is {0} dBm".format(rxPowerVal))
                self.debugPrint("RX power query complete.")

                break

        return rxPowerVal

    #Read the range value in centimeters
    def getRangeCentimeters(self,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
        
        self.debugPrint("Parsing range value...")
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None        

        self.ser.reset_input_buffer()   #flush the contents of the input buffer

        startTime = datetime.now()
       
        while True:
            elapsedTime = (datetime.now() - startTime).total_seconds()
            
            if (elapsedTime > timeout):
                self.debugPrint("ERROR: Timeout expired waiting for range value")
                return None
            try: newLine = self.ser.readline().decode(errors="ignore")
            except:
                self.debugPrint("ERROR: Problem reading range value")
                return None
            
            if (self.rangeStr in newLine):
                try: tmp = newLine.split(self.rangeStr)[1]
                except: continue
                
                try: rangeVal = float(tmp.split(" ")[0])*100
                except: continue
                
                self.debugPrint("Range is {0} cm".format(rangeVal))
                self.debugPrint("Range query complete.")

                break

        return rangeVal

    #Set the antenna delay
    def getAntennaDelay(self,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
        
        self.debugPrint("Getting antenna delay...")
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None
        
        self.ser.reset_input_buffer()   #flush the contents of the input buffer
        self.sendMessage("get,antDelay\r")

        time.sleep(self.readbackTimeout)
        
        startTime = datetime.now()
       
        while True:
            elapsedTime = (datetime.now() - startTime).total_seconds()
            
            if (elapsedTime > timeout):
                self.debugPrint("ERROR: Timeout expired waiting for antenna delay value check")
                return None
            
            try: newLine = self.ser.readline().decode(errors="ignore")
            except:
                self.debugPrint("ERROR: Problem getting antenna delay value")
                return None
            
            if (self.antDelayStr in newLine):
                try: antDelayParsed = newLine.split(self.antDelayStr)[1]
                except: continue
            
                try: antDelayVal = int(antDelayParsed)
                except:    
                    self.debugPrint("ERROR: Antenna delay value not read! "\
                                    "Make sure the device is connected properly and try again")
                    return None                 
                    
                break
            
        return antDelayVal

    #==========================================================================
    # DEVICE CONFIGURATION FUNCTIONS
    #==========================================================================
    #Set the antenna delay
    def setAntennaDelay(self,value,timeout=None):
        if (timeout == None):
            timeout = self.readTimeout
            
        if (value > self.antDelayMax) or (value < self.antDelayMin):
            self.debugPrint("ERROR: Command failed! Please choose an antenna delay value "\
                            "between {0} and {1}".format(self.antDelayMin,self.antDelayMax))            
            return None

        self.debugPrint("Setting antenna delay value to {0}...".format(value))
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None
        
        self.ser.reset_input_buffer()   #flush the contents of the input buffer
        self.sendMessage("set,antDelay,{0}\r".format(value))
       
        antDelayVal = self.getAntennaDelay()

        if (antDelayVal == value):
            self.debugPrint("Antenna delay value is: {0}".format(value))
            self.debugPrint("Antenna delay value changed.")
        else:
            self.debugPrint("ERROR: Antenna delay value not changed! Make sure the device is connected properly and try again")
            return None                    
            
        return True        

    #Send a message over the serial port
    #NOTE: each command is of the form [get|set],[command][,value] and ends
    #      with either a line feed or carriage return
    def sendMessage(self,string):
        self.debugPrint("Sending command '{0}'...".format(string))
        
        try:
            self.ser.readline()  #Clear the input buffer
        except:
            self.debugPrint("ERROR: Not connected to DUT!")  
            return None
        
        self.ser.reset_input_buffer()   #flush the contents of the input buffer
        
        for char in string:
            self.ser.write(char.encode())

        return True

    #==========================================================================
    # DEBUGGING FUNCTIONS
    #==========================================================================
    #Function to print common messages
    def commonPrint(self,string):
        (frame,
         filename,
         line_number,
         function_name,
         lines,
         index) = inspect.getouterframes(inspect.currentframe())[1]

        a = datetime.now()
        
        if not string:
            print("")
        else:
            if (self.printDebug == True):
                print("{0} {1} [Notice: {2}]: {3}".format(filename.split("\\")[-1],
                                                          line_number,
                                                          a.strftime("%Y/%m/%d %H:%M:%S.%f"),
                                                          string))            
            else:
                print("[Notice: {0}]: {1}".format(a.strftime("%Y/%m/%d %H:%M:%S.%f"),
                                                  string))            

    #Enable the debug output
    def enableDebugPrint(self,state):
        self.printDebug = state
        
        if (state):
            self.commonPrint("Debug output enabled.")
        else:
            self.commonPrint("Debug output disabled.")

    #Function to print debug messages
    def debugPrint(self,string):
        (frame,
         filename,
         line_number,
         function_name,
         lines,
         index) = inspect.getouterframes(inspect.currentframe())[1]

        if (self.printDebug == True):
            a = datetime.now()
            print("{0} {1} [Notice: {2}]: {3}".format(filename.split("\\")[-1],
                                                       line_number,
                                                       a.strftime("%Y/%m/%d %H:%M:%S.%f"),
                                                       string))