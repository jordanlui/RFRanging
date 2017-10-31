# -*- coding: utf-8 -*-
"""
DECAWAVE DW1000 TEST SOFTWARE (x64)

Created: Thurs July 20 10:43 2017
Last updated: Wed Aug 9 14:57 2017
Author: Alex Naylor

FUTURE ADDITIONS:
-[Nothing of note]

CHANGELOG (V0.5.0):
AN:
-Fixed plot title strings to deal with +/- properly
"""

#==========================================================================
# IMPORTS
#==========================================================================
import collections
import csv
import DW1000serial
import inspect
import sys

import math
import matplotlib.pyplot as plt
import numpy as np

from scipy.stats import norm
from scipy.optimize import curve_fit
from serial.tools import list_ports
from datetime import datetime

plt.ioff()  #Don't show plots until plt.show() is called

maxInt = sys.maxsize
decrement = True

while decrement:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.
    decrement = False
    try:
        csv.field_size_limit(maxInt)
    except OverflowError:
        maxInt = int(maxInt/10)
        decrement = True

#==========================================================================
# CLASS
#==========================================================================
class DW1000test(object):
    #==========================================================================
    # CLASS VARIABLES
    #==========================================================================    
    verNum = "0.5.0"

    #Constants
    speedOfLight = 299792458.0    #speed of light in a vacuum in m/s
    speedOfLightCm = speedOfLight*100
    antDelayLSB = 1/(499.2e6*128) #LSB of antenna delay reg. value; about 15.65 ps
    maxAntDelaySec = antDelayLSB*2**16  #maximum antenna delay in seconds
    
    #Close any existing plots
    plt.close("all")

    #Object initialization        
    def __init__(self,testInfoDict=None):    
        #======================================================================
        # INSTANCE VARIABLES
        #======================================================================       
        #Various variables
        if testInfoDict == None: #use some default values
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
            #Only here as an example of what keys are available
            self.plotInfoDict = {"makeGaussPlot":True, #whether or not to make the gaussian part of the average plot
                                 "makeHistPlot":True, #whether or not to make the histogram part of the average plot
                                 "makeRefPlot":True, #whether or not to add the curve fit line to the plot
                                 "scaleData":True, #Whether or not to scale data based on reference curve
                                 "truncateData":False, #whether or not to truncate distance array when making graphs
                                 "fileName":"", #Name of the file to read data from
                                 "useFile":False, #Whether or not to use a file for data plotting
                                 "show":False, #Whether or not to display the plot
                                 "minTruncDist":5, #lower limit for truncation
                                 "maxTruncDist":5} #upper limit for truncation          

            self.testInfoDict["numSteps"] = (self.testInfoDict["stopDist"] - self.testInfoDict["startDist"])/self.testInfoDict["stepDist"]

        else:
            self.testInfoDict = testInfoDict #use values from external source (most likely GUI)

        #Various strings
        self.remainTimeStr = "N/A"  #String for how much time is left in a test loop
        
        #Buffers
        self.anchorRangeBuffer = collections.deque(maxlen=self.testInfoDict["numSamples"])
        self.tagRangeBuffer = collections.deque(maxlen=self.testInfoDict["numSamples"])
        self.loopTimeBuffer = collections.deque(maxlen=self.testInfoDict["numSamples"])  
    
        #Timing-related
        self.startDelay = 5 #How long to wait after pressing enter to start the calibration

        #Plot-related
        self.figRes = [19.20,10.80]   #figure resolution (relative)
        self.histBinWidth = 1   #width of the histogram bins

        #Antenna calibration variables
        self.antDelayTol = 1  #tolerance to iteratively calibrate to in cm
        self.adjustSteps = [10,5,1] #delay value adjustment step in cm
        
        #DW1000 objects
        self.anchorPort = self.testInfoDict["anchorPort"]   #Anchor COM port number
        self.anchorBaud = self.testInfoDict["anchorBaud"]   #Anchor baud rate
        self.tagPort = self.testInfoDict["tagPort"]      #Tag COM port number
        self.tagBaud = self.testInfoDict["tagBaud"]      #Tag baud rate
        
        self.anchor = DW1000serial.DW1000()
        self.tag = DW1000serial.DW1000()
        
        self.anchor.enableDebugPrint(self.testInfoDict["enableDebug"])
        self.tag.enableDebugPrint(self.testInfoDict["enableDebug"])
        
        self.enableDebugPrint(self.testInfoDict["enableDebug"])

    #==========================================================================
    # DEVICE FUNCTIONS
    #==========================================================================
    #Connect to either the 'anchor' or 'tag'
    def deviceConnect(self,device):        
        if device == "anchor":
            try: self.anchor.ser
            except:
                if not self.anchor.connectToDUT(selPort=self.anchorPort,
                                                baudrate=self.anchorBaud):
                    return self.anchorPort            

            if not self.anchor.ser.isOpen():
                self.anchor.openDW1000port()

        elif device == "tag":
            try: self.tag.ser
            except:
                if not self.tag.connectToDUT(selPort=self.tagPort,
                                             baudrate=self.tagBaud):
                    return self.tagPort
            
    
            if not self.tag.ser.isOpen():
                self.tag.openDW1000port()
        
        return True
    
    #Disconnect from either the 'anchor' or 'tag'
    def deviceDisconnect(self,device):
        if device == "anchor":
            try: self.anchor.ser
            except: return True

            if self.anchor.ser.isOpen():
                self.anchor.closeDW1000port()

        if device == "tag":
            try: self.tag.ser
            except: return True

            if self.tag.ser.isOpen():
                self.tag.closeDW1000port()
        
        return True

    #==========================================================================
    # TESTING FUNCTIONS
    #==========================================================================
    #Distance measurement loop
    def distMeasLoop(self):        
        startTime = datetime.now()
        
        anchorRange = self.anchor.getRangeCentimeters()
        tagRange = self.tag.getRangeCentimeters()

        if (anchorRange == None) or (tagRange == None):
            self.deviceDisconnect("anchor")
            self.deviceDisconnect("tag")
            return None
        
        self.anchorRangeBuffer.append(anchorRange)
        self.tagRangeBuffer.append(tagRange)

        elapsedTime = (datetime.now()-startTime).total_seconds()*1000   #total milliseconds
        self.loopTimeBuffer.append(elapsedTime)
        avgLoopTime = np.average(self.loopTimeBuffer)
        remainMillis = (self.testInfoDict["numSamples"] - len(self.anchorRangeBuffer))*avgLoopTime
        
        (hours,
         minutes,
         seconds,
         millis) = self.convertTime(remainMillis)
        
        self.remainTimeStr = "{0}:{1}:{2}.{3}".format(format(hours,"02"),
                                                      format(minutes,"02"),
                                                      format(seconds,"02"),
                                                      format(millis,"03"))
        
        return True

    #Antenna delay calibration loop (for anchor; keep tag antenna delay at zero)
    def antDelayCalLoop(self,initAnchorDelay,calSamples=None):
        if (calSamples == None):
            calSamples = self.testInfoDict["numSamples"]
            

        anchorDelay = initAnchorDelay
        adjustIndex = 0
        adjustStep = self.adjustSteps[adjustIndex]
        
        #Sometimes you have to set the antenna delay twice?
        if not (self.tag.setAntennaDelay(0)):
            if not (self.tag.setAntennaDelay(0)):            
                self.debugPrint("Error setting tag antenna delay.")
                self.clearBuffers()
                return None       
        if not (self.anchor.setAntennaDelay(anchorDelay)):
            if not (self.anchor.setAntennaDelay(anchorDelay)):
                self.debugPrint("Error setting anchor antenna delay.")
                self.clearBuffers()
                return None 

        while (len(self.anchorRangeBuffer) < calSamples):
            if not (self.distMeasLoop()):
                self.debugPrint("Lost device connection, please try again.")
                self.clearBuffers()
                return None
            
        distAvg = np.average(self.anchorRangeBuffer)
        self.clearBuffers()
            
        print("distAvg: {0}".format(distAvg))
        
        if (distAvg > self.testInfoDict["startDist"]):
            lastAdjust = "add"
        elif (distAvg < self.testInfoDict["startDist"]):
            lastAdjust = "sub"            
        
        while ((distAvg > self.testInfoDict["startDist"]+self.antDelayTol) or
               (distAvg < self.testInfoDict["startDist"]-self.antDelayTol)):
            
            if ((distAvg > self.testInfoDict["startDist"]) and
               (lastAdjust == "add")):
                anchorDelay += adjustStep
                lastAdjust = "add"
                print("Adding {0} to get {1}".format(adjustStep,anchorDelay))
            elif ((distAvg < self.testInfoDict["startDist"]) and
                 (lastAdjust == "sub")):
                anchorDelay -= adjustStep
                lastAdjust = "sub"
                print("Subtracting {0} to get {1}".format(adjustStep,anchorDelay))
            else:
                adjustIndex += 1 
                adjustStep = self.adjustSteps[adjustIndex]
                
                if (distAvg > self.testInfoDict["startDist"]):
                    lastAdjust = "add"
                elif (distAvg < self.testInfoDict["startDist"]):
                    lastAdjust = "sub"
                
                print("Changing adjust step to {0}".format(adjustStep))
                continue
                
            if not (self.anchor.setAntennaDelay(anchorDelay)):
                if not (self.anchor.setAntennaDelay(anchorDelay)):
                    self.debugPrint("Error setting anchor antenna delay.")
                    self.clearBuffers()
                    return None 
                
            while (len(self.anchorRangeBuffer) < calSamples):
                if not (self.distMeasLoop()):
                    self.debugPrint("Lost device connection, please try again.")
                    self.clearBuffers()
                    return None
            
            distAvg = np.average(self.anchorRangeBuffer)
            print("distAvg: {0}".format(distAvg))
            self.clearBuffers()
            
        return anchorDelay

    #==========================================================================
    # PLOTTING FUNCTIONS
    #==========================================================================
    #Create a plot showing the difference between average calculated distance and actual distance
    def makeErrorPlotDist(self,
                          distDict,
                          plotInfoDict):

        xVals = []
        yVals = []
        measErrors = []

        #Used for y-bound
        upperMax = -1e9
        lowerMax = 1e9
        
        if (plotInfoDict["truncateData"] == True):
            distDict = self.truncateData(distDict,
                                         plotInfoDict)

        if (plotInfoDict["makeRefPlot"] == True):
            curveFitDict = self.linearCurveFit(distDict)

        if ((plotInfoDict["scaleData"] == True) and
            (plotInfoDict["makeRefPlot"] == True)):
            distDict = self.scaleLinearData(distDict,
                                             curveFitDict["m"],
                                             curveFitDict["b"])
       
        for actualDist,measDist in distDict.items():
            actualDistanceInt = int(actualDist.split(" cm")[0])
            measDistAvg = (np.average(measDist))
    
            xVals.append(actualDistanceInt) 
            yVals.append(measDistAvg)
    
            measErrors.append(measDistAvg - actualDistanceInt)
    
            upperMaxCur = measDistAvg
            lowerMaxCur = measDistAvg
            
            if upperMaxCur > upperMax:
                upperMax = upperMaxCur
            if lowerMaxCur < lowerMax:
                lowerMax = lowerMaxCur

        if (upperMax < self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]):
            upperMax = self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]

        if (lowerMax > self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]):
            lowerMax = self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]

        upperMax = self.baseRound(upperMax,self.testInfoDict["stepDist"],method="ceil")
        lowerMax = self.baseRound(lowerMax,self.testInfoDict["stepDist"],method="floor")

        # major ticks every step size                                     
        major_xticks = np.arange((self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]),
                                (self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]),
                                self.testInfoDict["stepDist"])

        # major y ticks every step size                                     
        major_yticks = np.arange((lowerMax-self.testInfoDict["stepDist"]),
                                 (upperMax+self.testInfoDict["stepDist"]),
                                 self.testInfoDict["stepDist"])
        
        #Create a plot of calculated distance vs. actual distance
        plt.figure(figsize=self.figRes)
        if plotInfoDict["scaleData"]:
            plt.title("Error plot for Calculated distance vs. Actual distance moving in "\
                      "{0} cm steps for {1} scaled to y={2:.2f}x{3:+.2f}".format(self.testInfoDict["stepDist"],
                                                                                 self.testInfoDict["device"],
                                                                                 curveFitDict["m"],
                                                                                 curveFitDict["b"],
                                                                                 fontsize=30))
        else:
            plt.title("Error plot for Calculated distance vs. Actual distance moving in "\
                      "{0} cm steps for {1}".format(self.testInfoDict["stepDist"],
                                                    self.testInfoDict["device"],
                                                    fontsize=30))
            
        plt.xlabel('Actual Distance (cm)')
        plt.ylabel('Calculated Distance (cm)')
        plt.xlim((self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]),
                 (self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]))
        plt.ylim((lowerMax-self.testInfoDict["stepDist"]),
                 (upperMax+self.testInfoDict["stepDist"]))
        plt.xticks(major_xticks)
        plt.yticks(major_yticks)
        
        #highlight the axes
        plt.axhline(0, color = 'k')
        
        plt.axvline(0, color = 'k')

        index = 0
        
        #Plot lines between the measured and actual distances
        for xVal in sorted(xVals):
            plt.plot([xVal,xVal],
                     [xVal,yVals[index]],
                     label="$\Delta$ = {0} cm".format(round(measErrors[index],2)))
            
            index += 1

        plt.legend(bbox_to_anchor=(1.00625, 1), loc=2, borderaxespad=0.)
        plt.grid(which='major',ls="dotted")

        #Ideal curve: measured distance equals actual distance        
        plt.plot(xVals,
                 xVals,
                 color="b")
        
        #5 cm below ideal curve
        plt.plot(xVals,
                 np.asarray(xVals)-5,
                 color="k",
                 ls="dotted",
                 label="$\pm$5 cm threshold")
        
        #5 cm above ideal curve
        plt.plot(xVals,
                 np.asarray(xVals)+5,
                 color="k",
                 ls="dotted")
        
        #Ideal curve as scatter plot
        plt.scatter(sorted(xVals),
                    sorted(xVals),
                    color="b",
                    label="Actual dist.")

        #Average measured value at each distance
        plt.scatter(sorted(xVals),
                    yVals,
                    color="r",
                    label="Avg. meas. dist.")

        if not plotInfoDict["scaleData"]:
            #Plot the curve fit data
            plt.plot(curveFitDict["actualDistVals"],
                     curveFitDict["refDistVals"],
                     color="g",
                     label="Curve fit\n(y={0:.2f}x{1:+.2f})".format(curveFitDict["m"],
                                                                    curveFitDict["b"]))
        

        if (plotInfoDict["show"] == True):
            plt.show()
            
        plt.legend(bbox_to_anchor=(1.00625, 1), loc=2, borderaxespad=0.)
        plt.grid(which='major',ls="dotted")
        
        a = datetime.now()
        if plotInfoDict["scaleData"]:
            plt.savefig("Distance error plot (scaled) - {0} - {1}".format(self.testInfoDict["device"],
                                                                          a.strftime("(%Y-%m-%d_%H-%M-%S)")))
        else:
            plt.savefig("Distance error plot - {0} - {1}".format(self.testInfoDict["device"],
                                                                 a.strftime("(%Y-%m-%d_%H-%M-%S)")))

    #Make a Gaussian plot of calculated vs. actual distance
    def makeGaussianPlotDist(self,
                             distDict,
                             plotInfoDict,
                             histBinWidth = None):
        
        if (histBinWidth == None):
            histBinWidth = self.histBinWidth
        
        xVals = []  
        yVals = []
        
        #Used for y-bound
        upperMax = -1e9
        lowerMax = 1e9
        
        if (plotInfoDict["truncateData"] == True):
            distDict = self.truncateData(distDict,
                                          plotInfoDict)

        if (plotInfoDict["makeRefPlot"] == True):
            curveFitDict = self.linearCurveFit(distDict)
            
        if ((plotInfoDict["scaleData"] == True) and
            (plotInfoDict["makeRefPlot"] == True)):
            distDict = self.scaleLinearData(distDict,
                                            curveFitDict["m"],
                                            curveFitDict["b"])

            histBinWidth = (self.histBinWidth)/curveFitDict["m"]
            
            if (histBinWidth < 0):
                histBinWidth = 1
              
        for actualDist,measDist in distDict.items():
            xVals.append(int(actualDist.split(" cm")[0])) 
    
            upperMaxCur = np.max(measDist)
            lowerMaxCur = np.min(measDist)
            
            if upperMaxCur > upperMax:
                upperMax = upperMaxCur
            if lowerMaxCur < lowerMax:
                lowerMax = lowerMaxCur

        if (upperMax < self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]):
            upperMax = self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"]

        if (lowerMax > self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]):
            lowerMax = self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]

        upperMax = self.baseRound(upperMax,self.testInfoDict["stepDist"],method="ceil")
        lowerMax = self.baseRound(lowerMax,self.testInfoDict["stepDist"],method="floor")

        # major ticks every step size                                     
        major_xticks = np.arange((self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]),
                                (self.testInfoDict["stopDist"]+2*self.testInfoDict["stepDist"]),
                                self.testInfoDict["stepDist"])

        # major y ticks every step size (use one past the last distance to
        # accomodate the final gaussian width)                                  
        major_yticks = np.arange((lowerMax-self.testInfoDict["stepDist"]),
                                 (upperMax+self.testInfoDict["stepDist"]),
                                 self.testInfoDict["stepDist"])
        
        #Create a plot of calculated distance vs. actual distance
        plt.figure(figsize=self.figRes)

        if plotInfoDict["scaleData"]:
            plt.title("Gaussian distribution for Calculated distance vs. Actual distance moving in "\
                      "{0} cm steps for {1} scaled to y={2:.2f}x{3:+.2f}".format(self.testInfoDict["stepDist"],
                                                                                 self.testInfoDict["device"],
                                                                                 curveFitDict["m"],
                                                                                 curveFitDict["b"],
                                                                                 fontsize=30))
        else:
            plt.title("Gaussian distribution for Calculated distance vs. Actual distance moving in "\
                      "{0} cm steps for {1}".format(self.testInfoDict["stepDist"],
                                                    self.testInfoDict["device"],
                                                    fontsize=30))

        plt.xlabel('Actual Distance (cm)')
        plt.ylabel('Calculated Distance (cm)')
        plt.xlim((self.testInfoDict["startDist"]-self.testInfoDict["stepDist"]),
                 (self.testInfoDict["stopDist"]+2*self.testInfoDict["stepDist"]))
        plt.ylim((lowerMax-self.testInfoDict["stepDist"]),
                 (upperMax+self.testInfoDict["stepDist"]),)
        plt.xticks(major_xticks)
        plt.yticks(major_yticks)
        
        statColorsIndex = 0

        for step in range(self.testInfoDict["startDist"],self.testInfoDict["stopDist"]+self.testInfoDict["stepDist"],self.testInfoDict["stepDist"]):
            distMu, distSigma = norm.fit(sorted(distDict["{0} cm".format(step)]))
            
            yVals.append(distMu)
            
            if not distSigma == 0:
                distGauss = norm.pdf(np.asarray(sorted(distDict["{0} cm".format(step)])),round(distMu,2),round(distSigma,2))
                distGaussScaled = [(distGauss[index]/np.max(distGauss))*(self.testInfoDict["stepDist"]-1) for index in range(0,len(distGauss))]  #Scale to the distance axis
        
                if statColorsIndex == 4:
                    statColorsIndex = 0
               
                if plotInfoDict["makeGaussPlot"] == True:
                    plt.plot(np.asarray(distGaussScaled)+step,sorted(distDict["{0} cm".format(step)]),
                             #color=statColors[statColorsIndex],
                             linewidth = 3,
                             label = "$\mu$ = {0} cm\n$\sigma$ = {1} cm".format(round(distMu,2),round(distSigma,2)))
                    
                if plotInfoDict["makeHistPlot"] == True:
                    #Plot the histogram to compare the Gaussian distribution to
                    distHist, distBinEdges = np.histogram(distDict["{0} cm".format(step)],
                                                                          bins=np.arange(np.min(distDict["{0} cm".format(step)]),
                                                                                         np.max(distDict["{0} cm".format(step)]), 
                                                                                         histBinWidth))
    
                    distHistScaled = np.asarray([(float(distHist[index])/np.max(distHist))*(self.testInfoDict["stepDist"]-1) for index in range(0,len(distHist))])
                
                    plt.barh(distBinEdges[:-1],
                             distHistScaled,
                             histBinWidth,
                             left=step,
                             edgecolor='k',
                             #color=statColors[statColorsIndex],
                             alpha=0.5)
            else:
                distMu, distSigma = 0,0
                          
            statColorsIndex += 1

        #highlight the axes
        plt.axhline(0, color = 'k')
        plt.axvline(0, color = 'k')

        #Ideal curve: measured distance equals actual distance        
        plt.plot(xVals,
                 xVals,
                 color="b")
        
        #5 cm below ideal curve
        plt.plot(xVals,
                 np.asarray(xVals)-5,
                 color="k",
                 ls="dotted",
                 label="$\pm$5 cm threshold")
        
        #5 cm above ideal curve
        plt.plot(xVals,
                 np.asarray(xVals)+5,
                 color="k",
                 ls="dotted")
        
        #Ideal curve as scatter plot
        plt.scatter(sorted(xVals),
                    sorted(xVals),
                    color="b",
                    label="Actual dist.")

        #Average measured value at each distance
        plt.scatter(sorted(xVals),
                    yVals,
                    color="r",
                    label="Avg. meas. dist.")
        
        if not plotInfoDict["scaleData"]:
            #Plot the curve fit data
            plt.plot(curveFitDict["actualDistVals"],
                     curveFitDict["refDistVals"],
                     color="g",
                     label="Curve fit\n(y={0:.2f}x{1:+.2f})".format(curveFitDict["m"],
                                                                    curveFitDict["b"]))

        plt.legend(bbox_to_anchor=(1.00625, 1), loc=2, borderaxespad=0.)
        plt.grid(which='major',ls="dotted")

        if (plotInfoDict["show"] == True):
            plt.show()
        
        a = datetime.now()
        if plotInfoDict["scaleData"]:
            plt.savefig("Distance gaussian plot (scaled) - {0} - {1}".format(self.testInfoDict["device"],
                                                                             a.strftime("(%Y-%m-%d_%H-%M-%S)")))
        else:
            plt.savefig("Distance gaussian plot - {0} - {1}".format(self.testInfoDict["device"],
                                                                    a.strftime("(%Y-%m-%d_%H-%M-%S)")))
            
    #Curve fit the data to 
    def linearCurveFit(self,distDict):
        xVals = []
        yVals = []
        
        for actualDist,measDist in distDict.items():
            measDistAvg = np.average(measDist)
            actualDistVal = int(actualDist.split(" cm")[0])
            if (actualDistVal == 0):
                xVals.append(actualDistVal+0.1)
            else:
                xVals.append(actualDistVal)
            yVals.append(measDistAvg)
            
        nOpt,nCov = curve_fit(lambda x,m,b: (m*x+b), xVals, yVals)
        nSigma = np.sqrt(np.diag(nCov))
        
        m = nOpt[0]
        b = nOpt[1]
        
#        ###TEMP###
#        m = np.float64(1.23)
#        b = np.float64(-0.59)
#        ##########   
        
        del yVals[:]
        
        for xVal in xVals:
            yVal = m*xVal+b
            yVals.append(yVal)
        
        return {"nOpt":nOpt,
                "nSigma":nSigma,
                "m":m,
                "b":b,
                "actualDistVals":xVals,
                "refDistVals":yVals} 
    
    #==========================================================================
    # SUPPORTING FUNCTIONS
    #==========================================================================
    #Write relevant data to file
    def fileWrite(self,
                  distDict,
                  loopTimeDict):
        Data_OP_Time = datetime.now()
        Data_OP = open(('DW1000_{0}_{1}_data_Output_{2}.csv'.format(self.testInfoDict["device"],
                                                                   self.testInfoDict["testType"],
                                                                   Data_OP_Time.strftime('(%Y-%m-%d_%H-%M-%S)'))),'w')
        
        Data_OP_Write = csv.writer(Data_OP, dialect = 'excel', lineterminator = '\n')

        valueDict = {"distDict":distDict,
                     "loopTimeDict":loopTimeDict,
                     "testInfoDict":self.testInfoDict}
        
    
        for key, value in valueDict.items():
            Data_OP_Write.writerow([key, value])
            
        Data_OP.close()

    def fileRead(self,filename):
        extension = filename.split(".")[-1]
       
        if not (extension == "csv"):
            self.debugPrint("Incorrect file type selected; expected .csv")
            return None
        
        Data_IP = open(filename,'r')    
        Data_IP_Read = csv.reader(Data_IP, dialect = 'excel', lineterminator = '\n')
        
        try:
            valueDict = dict(Data_IP_Read)
        except:
            self.debugPrint("Unexpected value in .csv file.")
            return None
        
        Data_IP.close()
        
        return valueDict

    #Find the antenna delay values for the anchor and tag
    def getAntDelay(self,sepDistCentimeters,
                         anchorRangeBuffer,
                         tagRangeBuffer):
        
        anchorRangeAvg = np.average(anchorRangeBuffer)
#        tagRangeAvg = np.average(tagRangeBuffer)
        
        anchorAntDelay = self.getAvgAntDelay(anchorRangeAvg,sepDistCentimeters)
#        tagAntDelay = self.getAvgAntDelay(tagRangeAvg,sepDistCentimeters)
        tagAntDelay = 0 #use aggregate antenna delay on each anchor instead; then only anchors will have non-zero antenna delay values
        
        anchorAntDelayDec = self.convertAntDelay(anchorAntDelay)
        tagAntDelayDec = self.convertAntDelay(tagAntDelay)

        return anchorAntDelayDec,tagAntDelayDec

    #Get the average antenna delay value in seconds (do not divide by two 
    #because antenna delay is taken after both a packet transmit and receive,
    #and we want the aggregate antenna delay)
    def getAvgAntDelay(self,avgRange,sepDistCentimeters):
        avgAntDelay = (avgRange-sepDistCentimeters)/(self.speedOfLightCm)
        
        return avgAntDelay
    
    #Convert average antenna delay in seconds to decimal value corresponding to
    #16-bit value required for DecaWave module (LSB is about 15.65 ps)
    def convertAntDelay(self,antDelaySec):
        antDelayDec = int(round(antDelaySec/self.antDelayLSB))
        
        return antDelayDec
    
    #Convert milliseconds to hours:minutes:seconds.milliseconds
    def convertTime(self,millis):
        millis = int(millis)
        seconds=(millis/1000)%60
        seconds = int(seconds)
        minutes=(millis/(1000*60))%60
        minutes = int(minutes)
        hours=(millis/(1000*60*60))%24
        hours = int(hours)
        millis = int(millis - int(millis/1000)*1000)
        
        return (hours,
                minutes,
                seconds,
                millis)

    #Clear all buffer contents
    def clearBuffers(self):
        self.anchorRangeBuffer.clear()
        self.tagRangeBuffer.clear()
        self.loopTimeBuffer.clear()        

    #Remove unwanted distances from existing distance data
    def truncateData(self,
                     distDict,
                     plotInfoDict):
        distDictTrunc = {}
    
        self.testInfoDict["startDist"] = self.baseRound(plotInfoDict["minTruncDist"],
                                                    self.testInfoDict["stepDist"],
                                                    method="ceil")
        self.testInfoDict["stopDist"] = self.baseRound(plotInfoDict["maxTruncDist"],
                                                   self.testInfoDict["stepDist"],
                                                   method="floor")
    
        for distance,values in distDict.items():
            distanceVal = int(distance.split(" cm")[0])
            
            if not (distanceVal > self.testInfoDict["stopDist"]) and not (distanceVal < self.testInfoDict["startDist"]):
                distDictTrunc[distance] = values
                
        return distDictTrunc

    #Scale linear data from a known equation of the form y=m*x+b to fit to y=x
    def scaleLinearData(self,distDict,m,b):
        for actualDist,measDist in distDict.items():
            distDict[actualDist] = (measDist-b)/m
    
        return distDict

    #Scale linear value from a known equation of the form y=m*x+b to fit to y=x
    def scaleLinearValue(self,distValue,m,b):
        distValue = (distValue-b)/m
        return distValue

    def baseRound(self,value,base,method=None):
        if method == None:
            return int(base * round(float(value)/base))
        elif method == "ceil":
            return int(base * math.ceil(float(value)/base))
        elif method == "floor":
            return int(base * math.floor(float(value)/base)) 
       
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