# -*- coding: utf-8 -*-
"""
DECAWAVE DW1000 ANTENNA DELAY CALIBRATION SOFTWARE (x64)

NOTES: 
-This program uses the DecaWave DW1000 Arduino adapter board made by Wayne
 Holder to determine the anntena delay value of one anchor and one receiver
     -Note that this script is very preliminary; it currently requires the user
      to manually set the antenna delay to zero in DW1000.cpp (line:
      writeValueToBytes(antennaDelayBytes, 16384, LEN_STAMP);)
-The calibration method involves the following steps:
     1. Set the antenna delay to zero in DW1000.cpp
     2. Fix the anchor and tag 1 meter apart
     3. Run this script to determine the antenna delay values

Created: Mon June 5 15:37 2017
Last updated: Fri Aug 18 10:44 2017
Author: Alex Naylor

FUTURE ADDITIONS:
-Make antenna delay calibration automated
    -Means updating Arduino code
-Update the test cancellation feature to handle mid-test stoppage and to save
 data on quit
-------------------------------------------------------------------------------
    Executable:         N/A
    DW1000gui:          V0.5.0        
    DW1000test:         V0.5.0
    DW1000serial:       V0.4.0
-------------------------------------------------------------------------------

CHANGELOG (V0.5.0):
AN:
-When browsing for files, the browser now opens to the last opened directory
-Changed the way the start and stop distance spinboxes work
"""

#==========================================================================
# IMPORTS
#==========================================================================
import ast
import DW1000test
import os
import sys

from PyQt5 import (QtGui,QtCore,QtWidgets)
from scipy.stats import norm

#==========================================================================
# ANTENNA CALIBRATION THREAD
#==========================================================================
class distMeasThread(QtCore.QObject):
    """
    Must derive from QObject in order to emit signals, connect slots to other signals, and operate in a QThread.
    """

    sig_done = QtCore.pyqtSignal()  # ask the thread to end on completion
    sig_msg = QtCore.pyqtSignal(str, str)  # GUI field, GUI string

    def __init__(self, id : int, testInfoDict, plotInfoDict):
        super().__init__()
        self.__id = id
        self.__abort = False

        self.DW1000 = DW1000test.DW1000test(testInfoDict=testInfoDict) #make and instance of DW1000test        
        self.plotInfoDict = plotInfoDict #plot information
        self.testInfoDict = testInfoDict  #general test information
        self.anchorDict = {} #array for holding anchor distance values at each distance
        self.tagDict = {} #array for holding tag distance values at each distance
        self.loopTimeDict = {} #array for holding loop time at each distance

        #test variables
        self.curDist = self.testInfoDict["startDist"]

    def setup(self):
        """
        Pretend this worker method does work that takes a long time. During this time, the thread's
        event loop is blocked, except if the application's processEvents() is called: this gives every
        thread (incl. main) a chance to process events, which in this sample means processing signals
        received from GUI (such as abort).
        """

        if self.plotInfoDict["useFile"] == False:
            self.DW1000.clearBuffers() #Clear all the buffers in case they aren't empty
            
            anchorResult = self.DW1000.deviceConnect("anchor")
    
            #If there was an issue connecting to the anchor, throw a warning and return
            if not (anchorResult == True):
                self.sig_msg.emit("errGeneralMsgBox","Could not connect to {0}.".format(anchorResult))
                self.sig_done.emit()
                return
    
            tagResult = self.DW1000.deviceConnect("tag")
            
            #If there was an issue connecting to the devices, throw a warning and return
            if not (tagResult == True):
                self.sig_msg.emit("errGeneralMsgBox","Could not connect to {0}.".format(tagResult))
                self.sig_done.emit()
                return

            if not (self.DW1000.anchor.setAntennaDelay(self.testInfoDict["anchorAntDelayDec"])):               
                if not (self.DW1000.anchor.setAntennaDelay(self.testInfoDict["anchorAntDelayDec"])):
                    self.sig_msg.emit("errGeneralMsgBox","Error setting anchor\n"\
                                                         "antenna delay value")
                    self.sig_done.emit()
                    return

            if not (self.DW1000.tag.setAntennaDelay(self.testInfoDict["tagAntDelayDec"])):
                if not (self.DW1000.tag.setAntennaDelay(self.testInfoDict["tagAntDelayDec"])):            
                    self.sig_msg.emit("errGeneralMsgBox","Error setting tag\n"\
                                                         "antenna delay value")
                    self.sig_done.emit()
                    return 

            self.sig_msg.emit("infoThreadMsgBox","Please move the device to {0} cm\n"\
                                                 "and press 'OK' to continue.".format(self.testInfoDict["startDist"]))

        else:
            result = self.DW1000.fileRead(self.plotInfoDict["fileName"])

            self.sig_msg.emit("statusBar","STATUS: Reading CSV file...")
            
            if (result == None):
                self.sig_msg.emit("errGeneralMsgBox","Unexpected value in .csv file!")
                self.sig_done.emit()
                return
            
            try: distDict = ast.literal_eval(result["distDict"])
            except:
                self.sig_msg.emit("errGeneralMsgBox","Unexpected value in .csv file!")
                self.sig_done.emit()
                return                

            try: testInfoDict = ast.literal_eval(result["testInfoDict"])
            except:
                self.sig_msg.emit("errGeneralMsgBox","Unexpected value in .csv file!")
                self.sig_done.emit()
                return

            self.DW1000.testInfoDict = testInfoDict.copy()

            self.sig_msg.emit("statusBar","STATUS: Plotting data...")
                
            self.DW1000.makeErrorPlotDist(distDict.copy(),self.plotInfoDict.copy())
            self.DW1000.makeGaussianPlotDist(distDict.copy(),self.plotInfoDict.copy())

            if self.plotInfoDict["scaleData"] == True:
                self.plotInfoDict["scaleData"] = False
                
                self.DW1000.makeErrorPlotDist(distDict.copy(),self.plotInfoDict.copy())
                self.DW1000.makeGaussianPlotDist(distDict.copy(),self.plotInfoDict.copy())

            self.sig_msg.emit("infoGeneralMsgBox","Data plotting complete.")

            self.sig_done.emit()
        
    def innerLoop(self):
        self.sig_msg.emit("statusBar","STATUS: Collecting data...")

        while (len(self.DW1000.anchorRangeBuffer) < self.testInfoDict["numSamples"]):
            if not (self.DW1000.distMeasLoop()):
                self.sig_msg.emit("errGeneralMsgBox","Lost device connection, please try again.")
                self.sig_msg.emit("testProgressBar",str(0))
                self.sig_msg.emit("loopProgressBar",str(0))
                self.sig_msg.emit("loopProgressBar_Label","Loop time remaining: N/A")
                self.DW1000.clearBuffers()
                self.sig_done.emit()
                return

            loopProgressVal = int(len(self.DW1000.anchorRangeBuffer)*100/self.testInfoDict["numSamples"])
            
            totalNumSamples = (self.testInfoDict["numSteps"]+1)*self.testInfoDict["numSamples"]
            cumulativeSamples = (self.curDist - self.testInfoDict["startDist"])*self.testInfoDict["numSamples"]/self.testInfoDict["stepDist"]
            testProgressVal = int((len(self.DW1000.anchorRangeBuffer) + cumulativeSamples)*100/totalNumSamples)
            
            self.sig_msg.emit("testProgressBar",str(testProgressVal))                
            self.sig_msg.emit("loopProgressBar",str(loopProgressVal))
            self.sig_msg.emit("loopProgressBar_Label","Loop time remaining: {0}".format(self.DW1000.remainTimeStr))
        
        self.anchorDict["{0} cm".format(self.curDist)] = list(self.DW1000.anchorRangeBuffer)
        self.tagDict["{0} cm".format(self.curDist)] = list(self.DW1000.tagRangeBuffer)
        self.loopTimeDict["{0} cm".format(self.curDist)] = list(self.DW1000.loopTimeBuffer)

        if self.testInfoDict["testType"] == "distMeas":
            anchorMu, anchorSigma = norm.fit(sorted(self.anchorDict["{0} cm".format(self.curDist)]))
            tagMu, tagSigma = norm.fit(sorted(self.tagDict["{0} cm".format(self.curDist)]))
    
            self.sig_msg.emit("infoGeneralMsgBox","At {0} cm:\n"\
                                                  "Anchor average: {1:.3f} cm\n"\
                                                  "Anchor std dev: {2:.3f} cm\n"\
                                                  "Tag average: {3:.3f} cm\n"\
                                                  "Tag std dev: {4:.3f} cm\n".format(self.curDist,
                                                                                     anchorMu,
                                                                                     anchorSigma,
                                                                                     tagMu,
                                                                                     tagSigma))

        self.DW1000.clearBuffers() #clear buffers for next loop
        self.curDist += self.testInfoDict["stepDist"] #increase distance
        
        if not (self.curDist > self.testInfoDict["stopDist"]): #If we're at the last distance, don't print a message
            self.sig_msg.emit("statusBar","STATUS: Data collection at {0} cm complete.".format(self.curDist))
            self.sig_msg.emit("infoThreadMsgBox","Please move the device to {0} cm\n"\
                                                 "and press 'OK' to continue.".format(self.curDist))
        else:
            self.outerLoop()

    def outerLoop(self):
        if (self.curDist <= self.testInfoDict["stopDist"]):
            self.innerLoop()
        else:
            if (self.testInfoDict["testType"] == "antDelayCal"):
                anchorAntDelayDec,tagAntDelayDec = self.DW1000.getAntDelay((self.testInfoDict["startDist"]/100),
                                                                            self.anchorDict["{0} cm".format(self.testInfoDict["startDist"])],
                                                                            self.tagDict["{0} cm".format(self.testInfoDict["startDist"])])

                self.sig_msg.emit("infoGeneralMsgBox","Press 'OK' to find optimal \n"\
                                                      "antenna delay value...")
                self.sig_msg.emit("testProgressBar",str(0))
                self.sig_msg.emit("loopProgressBar",str(0))
                self.sig_msg.emit("loopProgressBar_Label","Loop time remaining: N/A")
                self.sig_msg.emit("statusBar","STATUS: Finding optimal antenna delay value...")
                
                anchorAntDelayDec = self.DW1000.antDelayCalLoop(anchorAntDelayDec)

                if (anchorAntDelayDec == None):
                    self.sig_msg.emit("errGeneralMsgBox","Error calibrating\n"\
                                                         "antenna delay")
                    self.sig_done.emit()
                    return
                else:
                    self.sig_msg.emit("infoGeneralMsgBox","Calibration complete.\n"\
                                                          "Anchor antenna delay: {0}\n"\
                                                          "Tag antenna delay: {1}\n".format(anchorAntDelayDec,tagAntDelayDec))                    

                self.sig_msg.emit("anchorDelaySpinBox",str(anchorAntDelayDec))
                self.sig_msg.emit("tagDelaySpinBox",str(tagAntDelayDec))

                self.testInfoDict["anchorAntDelayDec"] = anchorAntDelayDec
                self.testInfoDict["tagAntDelayDec"] = tagAntDelayDec

            self.DW1000.testInfoDict["device"] = "anchor"
            
            if self.testInfoDict["testType"] == "distMeas":
                self.sig_msg.emit("statusBar","STATUS: Plotting anchor data...")
                
                self.DW1000.makeErrorPlotDist(self.anchorDict.copy(),self.plotInfoDict.copy())
                self.DW1000.makeGaussianPlotDist(self.anchorDict.copy(),self.plotInfoDict.copy())
                
                if self.plotInfoDict["scaleData"] == True:
                    self.plotInfoDict["scaleData"] = False
                    self.DW1000.makeErrorPlotDist(self.anchorDict.copy(),self.plotInfoDict.copy())
                    self.DW1000.makeGaussianPlotDist(self.anchorDict.copy(),self.plotInfoDict.copy())
                    self.plotInfoDict["scaleData"] = True
                    
            self.DW1000.fileWrite(self.anchorDict,
                                  self.loopTimeDict)

            self.DW1000.testInfoDict["device"] = "tag"
            
            if self.testInfoDict["testType"] == "distMeas":
                self.sig_msg.emit("statusBar","STATUS: Plotting tag data...")
                
                self.DW1000.makeErrorPlotDist(self.tagDict.copy(),self.plotInfoDict.copy())
                self.DW1000.makeGaussianPlotDist(self.tagDict.copy(),self.plotInfoDict.copy())
                
                if self.plotInfoDict["scaleData"] == True:
                    self.plotInfoDict["scaleData"] = False
                    self.DW1000.makeErrorPlotDist(self.tagDict.copy(),self.plotInfoDict.copy())
                    self.DW1000.makeGaussianPlotDist(self.tagDict.copy(),self.plotInfoDict.copy())
                
            self.DW1000.fileWrite(self.tagDict,
                                  self.loopTimeDict)

            self.DW1000.deviceDisconnect("anchor")
            self.DW1000.deviceDisconnect("tag")

            if (self.testInfoDict["testType"] == "distMeas"):
                self.sig_msg.emit("infoGeneralMsgBox","Distance data collection complete.\n")

            self.sig_done.emit()

    def abort(self):
        self.__abort = True

#==========================================================================
# GUI CLASS
#==========================================================================
class DW1000testGUI(QtWidgets.QWidget):
    #==========================================================================
    # CLASS VARIABLES
    #==========================================================================
    verNum = "0.5.0"
    
    sig_abort_workers = QtCore.pyqtSignal() #Signal used to abort worker threads
    
    NUM_THREADS = 1 #Maximum number of threads

    #Initialize GUI parent
    def __init__(self):       
        #======================================================================
        # INSTANCE VARIABLES
        #======================================================================
        #Initializations
        self.remainTimeStr = "N/A"
        self.DW1000serial = DW1000test.DW1000serial.DW1000() #so we can query COM ports and populate comboboxes 
        self.baudRates = ["110",
                          "300",
                          "600",
                          "1200",
                          "2400",
                          "4800",
                          "9600",
                          "14400",
                          "19200",
                          "38400",
                          "57600",
                          "115200",
                          "230400",
                          "460800",
                          "921600"]

            #this is here more as a placeholder to show all of the available keys
        self.testInfoDict = {"testType":"antDelayCal",
                             "numSamples":100,   #number of sample to take
                             "startDist":5, #measurement start distance
                             "stopDist":100, #measurement stop distance
                             "stepDist":5, #measurement step distance
                             "device":None, #which device the test was for
                             "anchorPort":"COM14", #COM port for anchor (add to GUI)
                             "tagPort":"COM12", #COM port for tag (add to GUI)
                             "anchorBaud":115200,  #baud rate for anchor (add to GUI)
                             "tagBaud":115200, #baud rate for tag (add to GUI)
                             "anchorAntDelayDec":32900, #anchor antenna delay in decimal
                             "tagAntDelayDec":0, #tag antenna delay in decimal
                             "enableDebug":False} #Whether or not to enable debug mode
        self.plotInfoDict = {"makeGaussPlot":True, #whether or not to make the gaussian part of the average plot
                             "makeHistPlot":True, #whether or not to make the histogram part of the average plot
                             "makeRefPlot":True, #whether or not to add the curve fit line to the plot
                             "scaleData":False, #Whether or not to scale data based on reference curve
                             "truncateData":False, #whether or not to truncate distance array when making graphs
                             "fileName":"", #Name of the file to read data from
                             "useFile":False, #Whether or not to use a file for data plotting
                             "show":False, #Whether or not to display the plot
                             "minTruncDist":5, #lower limit for truncation
                             "maxTruncDist":5} #upper limit for truncation
 
        self.testInfoDict["numSteps"] = (self.testInfoDict["stopDist"] - self.testInfoDict["startDist"])/self.testInfoDict["stepDist"]


        #spinbox values
        self.distMin = 0   #minimum distance in cm
        self.stepDistMin = 1 #obviously can't have a step distance of 0
        self.distMax = 2000#maximum distance in cm
        self.startDistDef = 5 #default start distance in cm
        self.stopDistDef = 100 #default stop distance in cm
        self.stepDistDef = 5 #default step distance in cm
        self.calDistDef = 5 #default calibration distance in cm
        
        self.numSamplesMax = 10000 #maximum number of samples at each distance 
        self.numSamplesMin = 1 #minimum number of samples at each distance
        self.numSamplesDef = 100 #default number of samples

        self.antDelayMin = 0  #minimum antenna delay value
        self.antDelayMax = 2**16-1  #maximum antenna delay value
        self.antDelayDef = 32900    #reasonable default value for antenna delay

        super().__init__()
        
        if getattr(sys, 'frozen', False):
            # we are running in a |PyInstaller| bundle
            self.basedir = sys._MEIPASS #Temp directory
        else:
            # we are running in a normal Python environment
            self.basedir = os.path.dirname(__file__)  #Temp directory                
        
        self.guiOnly = False   #Set true if you want to test the GUI without the DW1000

        #Initialize threads
        QtCore.QThread.currentThread().setObjectName('mainThread')  # threads can be named, useful for log output
        self.__workers_done = None
        self.__threads = None
    
        self.initWidgets()

        self.refreshComPorts()
    #==========================================================================
    # GUI-RELATED INITALIZATION FUNCTIONS
    #==========================================================================
    #Initialize GUI widgets
    def initWidgets(self):
        #FRAMES
        self.Vframe1 = QtWidgets.QFrame(self)
        self.Vframe1.setFrameStyle(QtWidgets.QFrame.VLine)

        self.Vframe2 = QtWidgets.QFrame(self)
        self.Vframe2.setFrameStyle(QtWidgets.QFrame.VLine)

        self.mainHframe = QtWidgets.QFrame(self)
        self.mainHframe.setFrameStyle(QtWidgets.QFrame.HLine)
        
        self.deviceSetupHframe = QtWidgets.QFrame(self)
        self.deviceSetupHframe.setFrameStyle(QtWidgets.QFrame.HLine)

        self.calConfigHframe = QtWidgets.QFrame(self)
        self.calConfigHframe.setFrameStyle(QtWidgets.QFrame.HLine)

        #Information widgets
        self.guiStatusBar = QtWidgets.QStatusBar(self)  
            #Need separate message boxes as the thread box triggers the thread's outer loop
        self.generalMsgBox = QtWidgets.QMessageBox(self)
        
            #Deals with messages involving the thread
        self.threadMsgBox = QtWidgets.QMessageBox(self)
        self.threadMsgBox.buttonClicked.connect(self.workerLoop)
        self.threadMsgBox.closeEvent = self.msgBoxCloseEvent

        #Labels
        self.setupSec_Label = QtWidgets.QLabel("<b>Device setup</b>", self)
        self.setupSec_Label.setObjectName('setupSec_Label')
        
        self.testSec_Label = QtWidgets.QLabel("<b>Test Progress</b>", self)
        self.testSec_Label.setObjectName('testSec_Label')

        self.calConfigSec_Label = QtWidgets.QLabel("<b>Calibration Configuration</b>", self)
        self.calConfigSec_Label.setObjectName('calConfigSec_Label')

        self.distConfigSec_Label = QtWidgets.QLabel("<b>Distance Test Configuration</b>", self)
        self.distConfigSec_Label.setObjectName('distConfigSec_Label')
        
        self.deviceConfigSec_Label = QtWidgets.QLabel("<b>Device Configuration</b>", self)
        self.deviceConfigSec_Label.setObjectName('deviceConfigSec_Label')

        self.plotSettingsSec_Label = QtWidgets.QLabel("<b>Plot settings</b>", self)
        self.plotSettingsSec_Label.setObjectName('plotSettingsSec_Label')

        self.filePlotSec_Label = QtWidgets.QLabel("<b>Plot from file</b>", self)
        self.filePlotSec_Label.setObjectName('filePlotSec_Label')

        #Buttons
        #Refresh icon to use
        self.refreshIconDir = os.path.join(self.basedir,'refresh.ico')
        self.refreshIcon = QtGui.QIcon(self.refreshIconDir)
        self.refreshIconSizes = self.refreshIcon.availableSizes()   #Get all .ico sizes
        self.refreshIconWidth = self.refreshIconSizes[0].width()    #Choose the smallest size
        self.refreshIconHeight = self.refreshIconSizes[0].height()    #Choose the smallest size

        #Button to refresh COM ports        
        self.refreshComPorts_PushButton = QtWidgets.QPushButton()
        self.refreshComPorts_PushButton.clicked.connect(self.refreshComPorts) 
        self.refreshComPorts_PushButton.setObjectName("refreshComPorts_PushButton")
        self.refreshComPorts_PushButton.setIcon(QtGui.QIcon(self.refreshIconDir))
        self.refreshComPorts_PushButton.setIconSize(self.refreshIconSizes[0])
        self.refreshComPorts_PushButton.setFixedWidth(int(round(self.refreshIconHeight*1.1))) #add a little border around the icon
        self.refreshComPorts_PushButton.setFixedHeight(int(round(self.refreshIconHeight*1.1))) #add a little border around the icon

        #Button to calibrate the antenna delay
        self.antDelayCal_PushButton = QtWidgets.QPushButton("Calibrate")
        self.antDelayCal_PushButton.setFixedWidth(75)        
        self.antDelayCal_PushButton.clicked.connect(self.startThread) 
        self.antDelayCal_PushButton.setObjectName("antDelayCal_PushButton")

        #Button to run a distance test
        self.distMeas_PushButton = QtWidgets.QPushButton("Measure")
        self.distMeas_PushButton.setFixedWidth(75)        
        self.distMeas_PushButton.clicked.connect(self.startThread) 
        self.distMeas_PushButton.setObjectName("distMeas_PushButton")

        #Button to select distance file to plot from
        self.filePlot_PushButton = QtWidgets.QPushButton("Browse")
        self.filePlot_PushButton.setFixedWidth(75)
        self.filePlot_PushButton.setObjectName("filePlot_PushButton")
        self.filePlot_PushButton.clicked.connect(self.startThread)

        #Check boxes
        #Check box to make gaussian plot
        self.makeGauss_CheckBox = QtWidgets.QCheckBox()
        self.makeGauss_CheckBox.setObjectName('makeGauss_CheckBox')
        self.makeGauss_CheckBox.setChecked(True)
        self.makeGauss_CheckBox.setToolTip("Sets whether or not to make a\n"\
                                          "gaussian plot when running the\n"\
                                          "distance test.")
            #Make gaussian plot check box label
        self.makeGauss_CheckBox_Label = ExtendedQLabel("Make gaussian plot", self)
        self.makeGauss_CheckBox_Label.setObjectName('makeGauss_CheckBox_Label')
        self.makeGauss_CheckBox_Label.clicked.connect(lambda: self.configureWidgets({self.makeGauss_CheckBox_Label.objectName():None}))
        
        #Check box to make histogram plot
        self.makeHist_CheckBox = QtWidgets.QCheckBox()
        self.makeHist_CheckBox.setObjectName('makeHist_CheckBox')
        self.makeHist_CheckBox.setChecked(True)
        self.makeHist_CheckBox.setToolTip("Sets whether or not to make a\n"\
                                          "histogram plot when running the\n"\
                                          "distance test.")
            #Make histogram plot check box label
        self.makeHist_CheckBox_Label = ExtendedQLabel("Make histogram plot", self)
        self.makeHist_CheckBox_Label.setObjectName('makeHist_CheckBox_Label')
        self.makeHist_CheckBox_Label.clicked.connect(lambda: self.configureWidgets({self.makeHist_CheckBox_Label.objectName():None}))

        #Check box to plot the reference curve
        self.makeRef_CheckBox = QtWidgets.QCheckBox()
        self.makeRef_CheckBox.setObjectName('makeRef_CheckBox')
        self.makeRef_CheckBox.setChecked(True)
        self.makeRef_CheckBox.setToolTip("Sets whether or not to plot the\n"\
                                         "reference curve on the distance\n"\
                                         "test plot.")
            #Make histogram plot check box label
        self.makeRef_CheckBox_Label = ExtendedQLabel("Make reference plot", self)
        self.makeRef_CheckBox_Label.setObjectName('makeRef_CheckBox_Label')
        self.makeRef_CheckBox_Label.clicked.connect(lambda: self.configureWidgets({self.makeRef_CheckBox_Label.objectName():None}))

        #Check box to scale the data to a reference curve
        self.scaleData_CheckBox = QtWidgets.QCheckBox()
        self.scaleData_CheckBox.setObjectName('scaleData_CheckBox')
        self.scaleData_CheckBox.setChecked(True)
        self.scaleData_CheckBox.setToolTip("Sets whether or not to make a plot\n"\
                                           "with the data scaled to a reference\n"\
                                           "curve.")
            #Make histogram plot check box label
        self.scaleData_CheckBox_Label = ExtendedQLabel("Scale data", self)
        self.scaleData_CheckBox_Label.setObjectName('scaleData_CheckBox_Label')
        self.scaleData_CheckBox_Label.clicked.connect(lambda: self.configureWidgets({self.scaleData_CheckBox_Label.objectName():None}))

        #Check box to truncate plot data
        self.truncData_CheckBox = QtWidgets.QCheckBox()
        self.truncData_CheckBox.setObjectName('truncData_CheckBox')
        self.truncData_CheckBox.stateChanged.connect(lambda: self.configureWidgets({self.minTruncDist_SpinBox.objectName():self.truncData_CheckBox.isChecked(),
                                                                                    self.maxTruncDist_SpinBox.objectName():self.truncData_CheckBox.isChecked(),
                                                                                    self.minTruncDist_SpinBox_Label.objectName():self.truncData_CheckBox.isChecked(),
                                                                                    self.maxTruncDist_SpinBox_Label.objectName():self.truncData_CheckBox.isChecked()}))
        self.truncData_CheckBox.setToolTip("Sets whether or not to truncate\n"\
                                           "the dataset when making a plot.")
            #Truncate plot data check box label
        self.truncData_CheckBox_Label = ExtendedQLabel("Truncate data", self)
        self.truncData_CheckBox_Label.setObjectName('truncData_CheckBox_Label')
        self.truncData_CheckBox_Label.clicked.connect(lambda: self.configureWidgets({self.truncData_CheckBox_Label.objectName():None}))
        
        #Progress bars
        #Loop progress bar 
        self.loopProgressBar = QtWidgets.QProgressBar(self)
        self.loopProgressBar.setFixedWidth(150)
        self.loopProgressBar.setValue(0)
        self.loopProgressBar.setObjectName("loopProgressBar")
            #Loop progress bar labels
        self.loopProgressBar_Label = QtWidgets.QLabel("Loop time remaining: {0}".format(self.remainTimeStr), self)
        self.loopProgressBar_Label.setFixedWidth(175)        
        self.loopProgressBar_Label.setObjectName("loopProgressBar_Label")

        #Test progress bar 
        self.testProgressBar = QtWidgets.QProgressBar(self)
        self.testProgressBar.setFixedWidth(150)
        self.testProgressBar.setObjectName("testProgressBar")
        self.testProgressBar.setValue(0)

        #Comboboxes
        #Combobox for anchor COM port
        self.anchorComPort_ComboBox = QtWidgets.QComboBox(self)
        self.anchorComPort_ComboBox.setObjectName("anchorComPort_ComboBox")
            #Anchor COM port combobox label
        self.anchorComPort_ComboBox_Label = QtWidgets.QLabel("Anchor Port:", self)
        self.anchorComPort_ComboBox_Label.setObjectName("anchorComPort_ComboBox_Label")
        
        #Combobox for tag COM port
        self.tagComPort_ComboBox = QtWidgets.QComboBox(self)
        self.tagComPort_ComboBox.setObjectName("tagComPort_ComboBox")
            #Tag COM port combobox label
        self.tagComPort_ComboBox_Label = QtWidgets.QLabel("Tag Port:", self)
        self.tagComPort_ComboBox_Label.setObjectName("tagComPort_ComboBox_Label") 

        #Combobox for baud rate
        self.baudRate_ComboBox = QtWidgets.QComboBox(self)
        self.baudRate_ComboBox.addItems(self.baudRates)
        self.baudRate_ComboBox.setCurrentIndex(6)
        self.baudRate_ComboBox.setObjectName("baudRate_ComboBox")
        self.baudRate_ComboBox.setEnabled(False) #disabled because everything breaks if incorrect baud rate is chosen 
            #Baud rate combobox label
        self.baudRate_ComboBox_Label = QtWidgets.QLabel("Baud rate:", self)
        self.baudRate_ComboBox_Label.setObjectName("baudRate_ComboBox_Label")
        self.baudRate_ComboBox_Label.setToolTip("Sets baud rate for both the\n"\
                                                "anchor and the tag.")
        
        #Spinboxes
        #Spinbox for calibration distance
        self.calDist_SpinBox = QtWidgets.QSpinBox(self)
        self.calDist_SpinBox.setMaximumHeight(25)
        self.calDist_SpinBox.setMaximumWidth(60)
        self.calDist_SpinBox.setObjectName('stepDist_SpinBox')
        self.calDist_SpinBox.setRange(self.stepDistMin,self.distMax)
        self.calDist_SpinBox.setValue(self.calDistDef)
        self.calDist_SpinBox.setToolTip("Sets distance between the anchor\n"\
                                        "and tag to be used for antenna\n"\
                                        "delay calibration. Make sure to\n"\
                                        "set the antenna delay value on\n"\
                                        "the DecaWave boards to zero\n"\
                                        "before running this procedure.")

            #step distance spinbox label
        self.calDist_SpinBox_Label = QtWidgets.QLabel("Cal distance (cm):", self)
        self.calDist_SpinBox_Label.setObjectName('calDist_SpinBox_Label')

        #Spinbox for calibration number of samples per distance
        self.calNumSamples_SpinBox = QtWidgets.QSpinBox(self)
        self.calNumSamples_SpinBox.setMaximumHeight(25)
        self.calNumSamples_SpinBox.setMaximumWidth(60)
        self.calNumSamples_SpinBox.setObjectName('calNumSamples_SpinBox')
        self.calNumSamples_SpinBox.setRange(self.numSamplesMin,self.numSamplesMax)
        self.calNumSamples_SpinBox.setValue(self.numSamplesDef)
        self.calNumSamples_SpinBox.setToolTip("Sets the number of samples to\n"\
                                              "take when performing antenna\n"\
                                              "delay calibration. Make sure to\n"\
                                              "set the antenna delay value on\n"\
                                              "the DecaWave boards to zero\n"\
                                              "before running this procedure.")

            #calibration samples spinbox label
        self.calNumSamples_SpinBox_Label = QtWidgets.QLabel("Number of samples:", self)
        self.calNumSamples_SpinBox_Label.setObjectName('calNumSamples_SpinBox_Label')

        #Spinbox for start distance
        self.startDist_SpinBox = QtWidgets.QSpinBox(self)
        self.startDist_SpinBox.setMaximumHeight(25)
        self.startDist_SpinBox.setMaximumWidth(60)
        self.startDist_SpinBox.setObjectName('startDist_SpinBox')
        self.startDist_SpinBox.setRange(self.distMin,self.distMax)
        self.startDist_SpinBox.setSingleStep(self.stepDistDef)
        self.startDist_SpinBox.setValue(self.startDistDef)
        self.startDist_SpinBox.valueChanged.connect(self.spinboxChecker)
        self.startDist_SpinBox.setToolTip("Sets the start distance for a\n"\
                                          "distance measurement test in\n"\
                                          "centimeters.")
        
            #start distance spinbox label
        self.startDist_SpinBox_Label = QtWidgets.QLabel("Start distance (cm):", self)
        self.startDist_SpinBox_Label.setObjectName('startDist_SpinBox_Label')

        #Spinbox for stop distance
        self.stopDist_SpinBox = QtWidgets.QSpinBox(self)
        self.stopDist_SpinBox.setMaximumHeight(25)
        self.stopDist_SpinBox.setMaximumWidth(60)
        self.stopDist_SpinBox.setObjectName('stopDist_SpinBox')
        self.stopDist_SpinBox.setRange(self.distMin,self.distMax)
        self.stopDist_SpinBox.setSingleStep(self.stepDistDef)
        self.stopDist_SpinBox.setValue(self.stopDistDef)
        self.stopDist_SpinBox.valueChanged.connect(self.spinboxChecker)
        self.stopDist_SpinBox.setToolTip("Sets the stop distance for a\n"\
                                          "distance measurement test in\n"\
                                          "centimeters.")

            #stop distance spinbox label
        self.stopDist_SpinBox_Label = QtWidgets.QLabel("Stop distance (cm):", self)
        self.stopDist_SpinBox_Label.setObjectName('stopDist_SpinBox_Label')
        
        #Spinbox for step distance
        self.stepDist_SpinBox = QtWidgets.QSpinBox(self)
        self.stepDist_SpinBox.setMaximumHeight(25)
        self.stepDist_SpinBox.setMaximumWidth(60)
        self.stepDist_SpinBox.setObjectName('stepDist_SpinBox')
        self.stepDist_SpinBox.setRange(self.stepDistMin,self.distMax)
        self.stepDist_SpinBox.setValue(self.stepDistDef)
        self.stepDist_SpinBox.valueChanged.connect(self.spinboxChecker)
        self.stepDist_SpinBox.setToolTip("Sets the step distance for a\n"\
                                         "distance measurement test in\n"\
                                         "centimeters.")

            #step distance spinbox label
        self.stepDist_SpinBox_Label = QtWidgets.QLabel("Step distance (cm):", self)
        self.stepDist_SpinBox_Label.setObjectName('stepDist_SpinBox_Label')

        #Spinbox for distance test number of samples per distance
        self.distNumSamples_SpinBox = QtWidgets.QSpinBox(self)
        self.distNumSamples_SpinBox.setMaximumHeight(25)
        self.distNumSamples_SpinBox.setMaximumWidth(60)
        self.distNumSamples_SpinBox.setObjectName('distNumSamples_SpinBox')
        self.distNumSamples_SpinBox.setRange(self.numSamplesMin,self.numSamplesMax)
        self.distNumSamples_SpinBox.setValue(self.numSamplesDef)
        self.distNumSamples_SpinBox.setToolTip("Sets the number of samples to\n"\
                                               "take at each distance in the\n"\
                                               "distance measurement test.\n")

            #distance test samples spinbox label
        self.distNumSamples_SpinBox_Label = QtWidgets.QLabel("Number of samples:", self)
        self.distNumSamples_SpinBox_Label.setObjectName('distNumSamples_SpinBox_Label')

        #Spinbox for minimum distance to truncate plot data to 
        self.minTruncDist_SpinBox = QtWidgets.QSpinBox(self)
        self.minTruncDist_SpinBox.setMaximumHeight(25)
        self.minTruncDist_SpinBox.setMaximumWidth(60)
        self.minTruncDist_SpinBox.setObjectName('minTruncDist_SpinBox')
        self.minTruncDist_SpinBox.setRange(self.distMin,self.distMax)
        self.minTruncDist_SpinBox.setValue(self.startDistDef)
        self.minTruncDist_SpinBox.setToolTip("Sets the minimum distance to\n"\
                                             "truncate plot data\n")
        self.minTruncDist_SpinBox.setEnabled(False)

            #distance test samples spinbox label
        self.minTruncDist_SpinBox_Label = QtWidgets.QLabel("Minimum distance (cm):", self)
        self.minTruncDist_SpinBox_Label.setObjectName('minTruncDist_SpinBox_Label')
        self.minTruncDist_SpinBox_Label.setEnabled(False)

        #Spinbox for maximum distance to truncate plot data to 
        self.maxTruncDist_SpinBox = QtWidgets.QSpinBox(self)
        self.maxTruncDist_SpinBox.setMaximumHeight(25)
        self.maxTruncDist_SpinBox.setMaximumWidth(60)
        self.maxTruncDist_SpinBox.setObjectName('maxTruncDist_SpinBox')
        self.maxTruncDist_SpinBox.setRange(self.distMin,self.distMax)
        self.maxTruncDist_SpinBox.setValue(self.stopDistDef)
        self.maxTruncDist_SpinBox.setToolTip("Sets the maximum distance to\n"\
                                             "truncate plot data\n")
        self.maxTruncDist_SpinBox.setEnabled(False)

            #distance test samples spinbox label
        self.maxTruncDist_SpinBox_Label = QtWidgets.QLabel("Maximum distance (cm):", self)
        self.maxTruncDist_SpinBox_Label.setObjectName('maxTruncDist_SpinBox_Label')
        self.maxTruncDist_SpinBox_Label.setEnabled(False)

        #Spinbox for anchor antenna delay
        self.anchorDelay_SpinBox = QtWidgets.QSpinBox(self)
        self.anchorDelay_SpinBox.setMaximumHeight(25)
        self.anchorDelay_SpinBox.setMaximumWidth(60)
        self.anchorDelay_SpinBox.setObjectName('anchorDelay_SpinBox')
        self.anchorDelay_SpinBox.setRange(self.antDelayMin,self.antDelayMax)
        self.anchorDelay_SpinBox.setValue(self.antDelayDef)
        self.anchorDelay_SpinBox.setToolTip("Sets the anchor antenna delay\n"\
                                             "value\n")

            #distance test samples spinbox label
        self.anchorDelay_SpinBox_Label = QtWidgets.QLabel("Anchor delay:", self)
        self.anchorDelay_SpinBox_Label.setObjectName('anchorDelay_SpinBox_Label')

        #Spinbox for tag antenna delay
        self.tagDelay_SpinBox = QtWidgets.QSpinBox(self)
        self.tagDelay_SpinBox.setMaximumHeight(25)
        self.tagDelay_SpinBox.setMaximumWidth(60)
        self.tagDelay_SpinBox.setObjectName('tagDelay_SpinBox')
        self.tagDelay_SpinBox.setRange(self.antDelayMin,self.antDelayMax)
        self.tagDelay_SpinBox.setValue(self.antDelayMin)
        self.tagDelay_SpinBox.setToolTip("Sets the tag antenna delay\n"\
                                         "value\n")

            #distance test samples spinbox label
        self.tagDelay_SpinBox_Label = QtWidgets.QLabel("Tag delay:", self)
        self.tagDelay_SpinBox_Label.setObjectName('tagDelay_SpinBox_Label')

        #Initial Stuff
        self.Main = QtWidgets.QGridLayout()     
        self.Main.addWidget(self.Vframe1,0,2,12,1)
        self.Main.addWidget(self.Vframe2,0,5,12,1)

        #Setup and test section
        #######################################################################
        self.Main.addWidget(self.setupSec_Label,0,0,1,2)
        self.Main.addWidget(self.refreshComPorts_PushButton,0,1,
                            alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignHCenter)
        
        self.Main.addWidget(self.anchorComPort_ComboBox_Label,1,0)
        self.Main.addWidget(self.anchorComPort_ComboBox,1,1)
        
        self.Main.addWidget(self.tagComPort_ComboBox_Label,2,0)
        self.Main.addWidget(self.tagComPort_ComboBox,2,1)
        
        self.Main.addWidget(self.baudRate_ComboBox_Label,3,0)
        self.Main.addWidget(self.baudRate_ComboBox,3,1)

        self.Main.addWidget(self.deviceSetupHframe,4,0,1,2)
        
        self.Main.addWidget(self.testSec_Label,5,0,1,2)

        self.Main.addWidget(self.testProgressBar,6,0,1,2)
        self.Main.addWidget(self.loopProgressBar,7,0,1,2)
        self.Main.addWidget(self.loopProgressBar_Label,8,0,1,2)
        
        self.Main.addWidget(self.antDelayCal_PushButton,9,0)
        self.Main.addWidget(self.distMeas_PushButton,9,1)
        
        #Configure section
        #######################################################################
        self.Main.addWidget(self.calConfigSec_Label,0,3,1,2)        
        self.Main.addWidget(self.calDist_SpinBox_Label,1,3)
        self.Main.addWidget(self.calDist_SpinBox,1,4)
        
        self.Main.addWidget(self.calNumSamples_SpinBox_Label,2,3)
        self.Main.addWidget(self.calNumSamples_SpinBox,2,4)
        
        self.Main.addWidget(self.calConfigHframe,3,3,1,2)
        
        self.Main.addWidget(self.distConfigSec_Label,4,3,1,2)         
        self.Main.addWidget(self.startDist_SpinBox_Label,5,3)
        self.Main.addWidget(self.startDist_SpinBox,5,4)

        self.Main.addWidget(self.stopDist_SpinBox_Label,6,3)        
        self.Main.addWidget(self.stopDist_SpinBox,6,4)

        self.Main.addWidget(self.stepDist_SpinBox_Label,7,3)
        self.Main.addWidget(self.stepDist_SpinBox,7,4)
        
        self.Main.addWidget(self.distNumSamples_SpinBox_Label,8,3)
        self.Main.addWidget(self.distNumSamples_SpinBox,8,4)
        
        self.Main.addWidget(self.deviceConfigSec_Label,9,3,1,2)
        
        self.Main.addWidget(self.anchorDelay_SpinBox_Label,10,3)
        self.Main.addWidget(self.anchorDelay_SpinBox,10,4)
        
        self.Main.addWidget(self.tagDelay_SpinBox_Label,11,3)
        self.Main.addWidget(self.tagDelay_SpinBox,11,4)

        #Plot settings section
        #######################################################################
        self.Main.addWidget(self.plotSettingsSec_Label,0,6,1,2)    

        self.Main.addWidget(self.makeGauss_CheckBox,1,6)
        self.Main.addWidget(self.makeGauss_CheckBox_Label,1,7,1,2)

        self.Main.addWidget(self.makeHist_CheckBox,2,6)
        self.Main.addWidget(self.makeHist_CheckBox_Label,2,7,1,2)

        self.Main.addWidget(self.makeRef_CheckBox,3,6)
        self.Main.addWidget(self.makeRef_CheckBox_Label,3,7,1,2)

        self.Main.addWidget(self.scaleData_CheckBox,4,6)
        self.Main.addWidget(self.scaleData_CheckBox_Label,4,7,1,2)

        self.Main.addWidget(self.truncData_CheckBox,5,6)
        self.Main.addWidget(self.truncData_CheckBox_Label,5,7,1,2)

        self.Main.addWidget(self.minTruncDist_SpinBox_Label,6,7)
        self.Main.addWidget(self.minTruncDist_SpinBox,6,8)
                
        self.Main.addWidget(self.maxTruncDist_SpinBox_Label,7,7)
        self.Main.addWidget(self.maxTruncDist_SpinBox,7,8)

        self.Main.addWidget(self.filePlotSec_Label,8,6,1,2)
        self.Main.addWidget(self.filePlot_PushButton,9,6,1,2)

        self.Main.addWidget(self.mainHframe,12,0,1,9)

        #Status bar
        self.Main.addWidget(self.guiStatusBar,13,0,1,11,alignment = QtCore.Qt.AlignBottom)  
        
        if self.guiOnly == True:  
            self.guiStatusBar.showMessage("***NOTE: DW1000 control disabled***")
        elif self.guiOnly == False:
            self.guiStatusBar.showMessage("STATUS: Idle.")

        #Instantiate main widget      
        self.setLayout(self.Main)

    #==========================================================================
    # GUI-RELATED SUPPORTING FUNCTIONS
    #==========================================================================
    #Error-checking for spinboxes
    def spinboxChecker(self):
        widgetInfo = self.widgetInfo()

        startValue = self.startDist_SpinBox.value()
        stopValue = self.stopDist_SpinBox.value()
        stepValue = self.stepDist_SpinBox.value()
        
        if (widgetInfo["widgetName"] == "stepDist"):
            newStepValue =  self.stepDist_SpinBox.value()
            self.startDist_SpinBox.setSingleStep(newStepValue)
            self.stopDist_SpinBox.setSingleStep(newStepValue)
            
            newStartValue = int(stepValue*round(float(startValue)/stepValue))
            newStopValue = int(stepValue*round(float(stopValue)/stepValue))

            self.startDist_SpinBox.setValue(newStartValue)
            self.stopDist_SpinBox.setValue(newStopValue)
            
        elif ((widgetInfo["widgetName"] == "startDist") or
             (widgetInfo["widgetName"] == "minTruncDist")):

            if (startValue >= stopValue) and (startValue < self.distMax):
                self.stopDist_SpinBox.setValue(startValue+stepValue)
            elif (startValue >= stopValue) and (startValue >= self.distMax):
                self.startDist_SpinBox.setValue(stopValue-stepValue)

            stopValue = self.stopDist_SpinBox.value()
            startValue = self.startDist_SpinBox.value()

#            if not ((stopValue - startValue) == stepValue):
#                newStopValue = int(stepValue*round(float(stopValue)/stepValue))
#                self.stopDist_SpinBox.setValue(newStopValue)

        elif ((widgetInfo["widgetName"] == "stopDist") or
             (widgetInfo["widgetName"] == "maxTruncDist")):

            if (stopValue <= startValue) and (stopValue > self.distMin):
                self.startDist_SpinBox.setValue(stopValue-stepValue)
            elif (stopValue <= startValue) and (stopValue <= self.distMin):
                self.stopDist_SpinBox.setValue(startValue+stepValue)

            stopValue = self.stopDist_SpinBox.value()
            startValue = self.startDist_SpinBox.value()

#            if not ((stopValue - startValue) == stepValue):
#                newStartValue = int(stepValue*round(float(startValue)/stepValue))
#                self.startDist_SpinBox.setValue(newStartValue)

    #Update various GUI-related widgets
    def updateGui(self,field,value):
        if field == "errThreadMsgBox":
            self.threadMsgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.threadMsgBox.setWindowTitle("Error")
            self.threadMsgBox.setText(value)
            self.threadMsgBox.show()
        elif field == "infoThreadMsgBox":
            self.threadMsgBox.setIcon(QtWidgets.QMessageBox.Information)
            self.threadMsgBox.setWindowTitle("Information")
            self.threadMsgBox.setText(value)
            self.threadMsgBox.show()
        
        elif field == "confirmMsgBox":
            self.confirmMsgBox.show()
        
        elif field == "errGeneralMsgBox":
            self.generalMsgBox.warning(self,"Error",value)
        elif field == "infoGeneralMsgBox":
            self.generalMsgBox.information(self,"Information",value)
        elif field == "infoGeneralMsgBoxNoBtns":
            self.generalMsgBox.setIcon(QtWidgets.QMessageBox.Information)
            self.generalMsgBox.setWindowTitle("Information")
            self.generalMsgBox.setText(value)
            self.generalMsgBox.removeButton(QtWidgets.QMessageBox.Ok)
            self.generalMsgBox.show()
        elif field == "closeGeneralMsgBox":
            self.generalMsgBox.done(1)

        
        elif field == "testProgressBar":
            self.testProgressBar.setValue(int(value))
        elif field == "loopProgressBar":
            self.loopProgressBar.setValue(int(value))
        elif field == "loopProgressBar_Label":
            self.loopProgressBar_Label.setText(value)
        
        elif field == "anchorDelaySpinBox":
            self.anchorDelay_SpinBox.setValue(int(value))
        elif field == "tagDelaySpinBox":
            self.tagDelay_SpinBox.setValue(int(value))
        
        elif field == "statusBar":
            self.guiStatusBar.showMessage(value)

    #Configure various GUI-related widgets
    def configureWidgets(self,widgetDict):
        for widget,state in widgetDict.items():
            widgetInfo = self.widgetInfo(widget=widget)
            
            #Note that clickable labels are currently only connected to check
            #boxes and radio buttons and either check or uncheck them. Whenever
            #the state argument is "None", the attached widget will change to the
            #opposite state. However, if a state is specified, the "state" variable
            #sets whether or not the label is enabled
            if (widgetInfo["widgetType"] == "Label"): 
                if (state == None):
                    checkState = eval("self.{0}.isChecked()".format(widget.rstrip("_Label")))
                    eval("self.{0}.setChecked({1})".format(widget.rstrip("_Label"),(not checkState))) # change the check box to its opposite state
                else:
                    eval("self.{0}.setEnabled({1})".format(widget,state))
            else:
                eval("self.{0}.setEnabled({1})".format(widget,state))

    #Get the name and type of the most recently clicked widget
    def widgetInfo(self,widget=None):
        if (widget == None):
            widget = self.sender().objectName()

        widgetList = widget.split("_")        
        widgetName = widgetList[0]
        widgetType = widgetList[-1]
        
        if (widgetType == "Label") and (len(widgetList) >= 3):
            connWidgetType = widgetList[-2] #Some labels are connected to 
        else:
            connWidgetType = None
        
        return {"widget":widget,
                "widgetType":widgetType,
                "connWidgeType":connWidgetType,
                "widgetName":widgetName}

    #Update the testInfoDict being sent to the backend with the most recent values
    def updateTestInfoDict(self):
        widgetInfo = self.widgetInfo()
        
        #Test type (calibration or distance measurement)
        self.testInfoDict["testType"] = widgetInfo["widgetName"]
        
        #Device variables
        self.testInfoDict["anchorPort"] = self.anchorComPort_ComboBox.currentText()
        self.testInfoDict["anchorBaud"] = self.baudRate_ComboBox.currentText()
        self.testInfoDict["tagPort"] = self.tagComPort_ComboBox.currentText()
        self.testInfoDict["tagBaud"] = self.baudRate_ComboBox.currentText()

        #Plot variables
        self.plotInfoDict["makeGaussPlot"] = self.makeGauss_CheckBox.isChecked()
        self.plotInfoDict["makeHistPlot"] = self.makeHist_CheckBox.isChecked()
        self.plotInfoDict["scaleData"] = self.scaleData_CheckBox.isChecked()
        self.plotInfoDict["truncateData"] = self.truncData_CheckBox.isChecked()
        self.plotInfoDict["minTruncDist"] = self.minTruncDist_SpinBox.value()
        self.plotInfoDict["maxTruncDist"] = self.maxTruncDist_SpinBox.value()

        self.Main.addWidget(self.calDist_SpinBox,1,4)
        
        self.Main.addWidget(self.calNumSamples_SpinBox_Label,2,3)
        self.Main.addWidget(self.calNumSamples_SpinBox,2,4)
        
        if (widgetInfo["widgetName"] == "antDelayCal"):
            self.testInfoDict["numSamples"] = self.calNumSamples_SpinBox.value()
            self.testInfoDict["startDist"] = self.calDist_SpinBox.value()
            self.testInfoDict["stopDist"] = self.calDist_SpinBox.value()
            self.testInfoDict["stepDist"] = 1
            self.testInfoDict["numSteps"] = (self.testInfoDict["stopDist"] - self.testInfoDict["startDist"])/self.testInfoDict["stepDist"]
            self.testInfoDict["anchorAntDelayDec"] = 0
            self.testInfoDict["tagAntDelayDec"] = 0

            self.plotInfoDict["useFile"] = False

        elif (widgetInfo["widgetName"] == "distMeas"):
            self.testInfoDict["numSamples"] = self.distNumSamples_SpinBox.value()
            self.testInfoDict["startDist"] = self.startDist_SpinBox.value()
            self.testInfoDict["stopDist"] = self.stopDist_SpinBox.value()
            self.testInfoDict["stepDist"] = self.stepDist_SpinBox.value()
            self.testInfoDict["numSteps"] = (self.testInfoDict["stopDist"] - self.testInfoDict["startDist"])/self.testInfoDict["stepDist"]
            self.testInfoDict["anchorAntDelayDec"] = self.anchorDelay_SpinBox.value()
            self.testInfoDict["tagAntDelayDec"] = self.tagDelay_SpinBox.value()

            self.plotInfoDict["useFile"] = False
            
            print("Done")
            
        elif (widgetInfo["widgetName"] == "filePlot"):
            if (self.plotInfoDict["fileName"] == ""):
                curDir = os.path.dirname(os.path.realpath(__file__))
            else:
                csvName = self.plotInfoDict["fileName"].split("/")[-1]
                curDir = self.plotInfoDict["fileName"].rstrip(csvName)
            
            fileName = QtWidgets.QFileDialog.getOpenFileName(self,
                                                             "Select data file", 
                                                             curDir,
                                                             "CSV files (*.csv)")
            
            self.plotInfoDict["useFile"] = True
            self.plotInfoDict["fileName"] = fileName[0]
            
            print(self.plotInfoDict["fileName"])

    #==========================================================================
    # THREAD-RELATED FUNCTIONS
    #==========================================================================
    #Start thread based on button clicked
    def startThread(self):

        self.updateTestInfoDict()
#        if self.plotInfoDict["fileName"] == "": #why is this here?
#            return

        self.configureWidgets({self.antDelayCal_PushButton.objectName():False,
                               self.distMeas_PushButton.objectName():False,
                               self.filePlot_PushButton.objectName():False,
                               self.anchorComPort_ComboBox.objectName():False,
                               self.anchorComPort_ComboBox_Label.objectName():False,
                               self.tagComPort_ComboBox.objectName():False,
                               self.tagComPort_ComboBox_Label.objectName():False,
                               self.baudRate_ComboBox.objectName():False,
#                               self.baudRate_ComboBox_Label.objectName():False,
                               self.anchorDelay_SpinBox.objectName():False,
                               self.anchorDelay_SpinBox_Label.objectName():False,
                               self.tagDelay_SpinBox.objectName():False,
                               self.tagDelay_SpinBox_Label.objectName():False}) #Disable widgets to avoid errors

        self.__workers_done = 0
        self.__threads = []
        for idx in range(self.NUM_THREADS):
            thread = QtCore.QThread()
            thread.setObjectName(self.testInfoDict["testType"])
            worker = distMeasThread(idx,self.testInfoDict,self.plotInfoDict)
            self.__threads.append((thread, worker))  # need to store worker too otherwise will be gc'd
            worker.moveToThread(thread)

            # get progress messages from worker:
            worker.sig_done.connect(self.abortWorkers) #For now, exit all threads when one is finished; we only use one at a time for now
            worker.sig_msg.connect(self.updateGui)

            # control worker:
            self.sig_abort_workers.connect(worker.abort)

            # get read to start worker:
            thread.started.connect(worker.setup)
            thread.start()  # this will emit 'started' and start thread's event loop

    def workerLoop(self,button):
        for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing        
            worker.outerLoop()
        
    #Ask all threads to end
    def abortWorkers(self):
        self.sig_abort_workers.emit()
        for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
            thread.quit()  # this will quit **as soon as thread event loop unblocks**
            thread.wait()  # <- so you need to wait for it to *actually* quit

        self.configureWidgets({self.antDelayCal_PushButton.objectName():True,
                               self.distMeas_PushButton.objectName():True,
                               self.filePlot_PushButton.objectName():True,
                               self.anchorComPort_ComboBox.objectName():True,
                               self.anchorComPort_ComboBox_Label.objectName():True,
                               self.tagComPort_ComboBox.objectName():True,
                               self.tagComPort_ComboBox_Label.objectName():True,
                               self.baudRate_ComboBox.objectName():True,
#                               self.baudRate_ComboBox_Label.objectName():True,
                               self.anchorDelay_SpinBox.objectName():True,
                               self.anchorDelay_SpinBox_Label.objectName():True,
                               self.tagDelay_SpinBox.objectName():True,
                               self.tagDelay_SpinBox_Label.objectName():True}) #Disable widgets to avoid errors
            
        self.updateGui("testProgressBar",str(0))
        self.updateGui("loopProgressBar",str(0))
        self.updateGui("loopProgressBar_Label","Loop time remaining: N/A")
        self.updateGui("statusBar","STATUS: Idle.")

    #==========================================================================
    # SUPPORTING FUNCTIONS
    #========================================================================== 
    #Populates combox with COM ports 
    def refreshComPorts(self):
        comPortListTypes = {}

        comPortList = sorted(self.DW1000serial.getSerialUSBPorts())

        baudrate = self.baudRate_ComboBox.currentText()

        self.anchorComPort_ComboBox.clear()
        self.tagComPort_ComboBox.clear()
        
        #If there are no COM ports detected or only one is found
        if len(comPortList) == 0:
            self.updateGui("errGeneralMsgBox","No USB serial COM ports detected!\n"\
                                              "Testing requires two USB serial COM ports!")

        else:            
            for port in comPortList:
                try: self.DW1000serial.connectToDUT(selPort=port,baudrate=baudrate)
                except:
                    comPortListTypes[port] = None
                    continue
                
                deviceType = self.DW1000serial.getDeviceType()
                
                #Close the serial port; no longer needed
                try: 
                    self.DW1000serial.ser.isOpen()
                    self.DW1000serial.closeDW1000port()
                except:
                    pass
                
                if deviceType == None: 
                    comPortListTypes[port] = None
                    continue
                else:
                    comPortListTypes[port] = deviceType
            
            numAnchors = sum(1 for x in comPortListTypes.values() if x == "anchor")
            numTags = sum(1 for x in comPortListTypes.values() if x == "tag")
            
            if (numAnchors == 0):
                self.updateGui("errGeneralMsgBox","No anchor COM ports discovered.\n"\
                                                  "Please check devices, refresh\n"\
                                                  "the COM port list, and check\n"\
                                                  "the baud rate.")
            if (numTags == 0):
                self.updateGui("errGeneralMsgBox","No tag COM ports discovered.\n"\
                                                  "Please check devices, refresh\n"\
                                                  "the COM port list, and check\n"\
                                                  "the baud rate.")
            if not (numAnchors == 0) and not (numTags == 0):
                self.updateGui("infoGeneralMsgBox","{0} anchor COM port(s) and\n"\
                                                   "{1} tag COM port(s) discovered.".format(numAnchors,numTags))
            
            for port,deviceType in comPortListTypes.items():
                try: eval("self.{0}ComPort_ComboBox.addItem('{1}')".format(deviceType,port))
                except: continue

    def msgBoxCloseEvent(self,event):
        reply = QtWidgets.QMessageBox.question(self,
                                               "Confirm",
                                               "Are you sure you want to\n"\
                                               "quit data collection? Data\n"\
                                               "will NOT be saved!",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Cancel)
        
        if reply == QtWidgets.QMessageBox.Ok:
            self.abortWorkers()
            event.accept()
        else:
            event.ignore()        

#==========================================================================
# CLICKABLE QLABEL CLASS
#========================================================================== 
class ExtendedQLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    
    def __init(self, parent):
        QtWidgets.QLabel.__init__(self, parent)
 
    def mouseReleaseEvent(self, event):
        self.clicked.emit()

#==========================================================================
# SCROLLBAR GUI CLASS
#==========================================================================       
class Scroll(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            # we are running in a |PyInstaller| bundle
            self.basedir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            self.basedir = os.path.dirname(__file__) 
        self.tglIconDir = os.path.join(self.basedir,'menrva.ico')
        self.showMaximized()
        self.setWindowTitle("DW1000 Test GUI") 
        self.setWindowIcon(QtGui.QIcon(self.tglIconDir))        
        self.ex = DW1000testGUI()
        self.setWidget(self.ex)        
        self.setEnabled(True)
        
    def closeEvent(self, event):       
        super(Scroll, self).closeEvent(event)

#==========================================================================
# MAIN CODE
#==========================================================================
if __name__ == '__main__':
    
    app = QtWidgets.QApplication(sys.argv)
    ex = Scroll()
    sys.exit(app.exec_())