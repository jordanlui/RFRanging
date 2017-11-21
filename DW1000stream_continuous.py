# -*- coding: utf-8 -*-
"""
DECAWAVE DW1000 DISTANCE STREAMING SOFTWARE (x64)

Uses a basic calibration and curve fitting algorithm to stream and display
DW1000 distance data

Created: Thurs July 20 10:43 2017
Last updated: Thurs July 27 17:57 2017
Author: Alex Naylor

FUTURE ADDITIONS:
- Change update rate to be more continuous

CHANGELOG (V0.0.0):
AN:
-First usable version
"""

import DW1000test
import sys
import numpy as np

calInfoDict = {"testType":"antDelayCal",
               "numSamples":5,   #number of samples. This  influences sample buffer size of the DW1000 object.
               "numSamplesRT":1, # Display samples in realtime
               "numCalSamples":20, # Number of samples required in calibration loop
               "startDist":5, #measurement start distance
               "stopDist":15, #measurement stop distance
               "stepDist":5, #measurement step distance
               "anchorPort":"COM4", #COM port for anchor (add to GUI)
               "tagPort":"COM15", #COM port for tag (add to GUI)
               "anchorBaud":9600,  #baud rate for anchor (add to GUI)
               "tagBaud":9600, #baud rate for tag (add to GUI)
               "enableDebug":False} #Whether or not to enable debug mode
plotInfoDict = {"makeGaussPlot":True, #whether or not to make the gaussian part of the average plot
                "makeHistPlot":True, #whether or not to make the histogram part of the average plot
                "makeRefPlot":True, #whether or not to add the curve fit line to the plot
                "scaleData":False, #Whether or not to scale data based on reference curve
                "truncateData":False, #whether or not to truncate distance array when making graphs
                "fileName":"", #Name of the file to read data from
                "useFile":False, #Whether or not to use a file for data plotting
                "show":True, #Whether or not to display the plot
                "minTruncDist":5, #lower limit for truncation
                "maxTruncDist":5} #upper limit for truncation

calInfoDict["numSteps"] = (calInfoDict["stopDist"] - calInfoDict["startDist"])/calInfoDict["stepDist"]

anchorDict = {}
tagDict = {}

#anchorDist = {}
#tagDist = {}

DW1000 = DW1000test.DW1000test(testInfoDict=calInfoDict)
curDist = 0

anchorResult = DW1000.deviceConnect("anchor")

#If there was an issue connecting to the anchor, throw a warning and return
if not (anchorResult == True):
    print("ERROR CONNECTING TO ANCHOR")
    sys.exit()

tagResult = DW1000.deviceConnect("tag")

if not (tagResult == True):
    print("ERROR CONNECTING TO TAG")
    sys.exit()

print("Prepare to start antenna delay calibration")
input("Move device to {0} cm and press enter to start...".format(calInfoDict["startDist"]))

DW1000.anchor.setAntennaDelay(0)
DW1000.tag.setAntennaDelay(0)

#Antenna delay calibration loop
while (len(DW1000.anchorRangeBuffer) < calInfoDict["numCalSamples"]):
    if not (DW1000.distMeasLoop()):
        print("ERROR READING DISTANCES")
        sys.exit()

    loopProgressVal = int(len(DW1000.anchorRangeBuffer)*100/calInfoDict["numCalSamples"])
    
    totalNumSamples = (calInfoDict["numCalSamples"]+1)*calInfoDict["numCalSamples"]
    cumulativeSamples = (curDist - calInfoDict["startDist"])*calInfoDict["numCalSamples"]/calInfoDict["stepDist"]
    testProgressVal = int((len(DW1000.anchorRangeBuffer) + cumulativeSamples)*100/totalNumSamples)

anchorAntDelayDec,tagAntDelayDec = DW1000.getAntDelay((calInfoDict["startDist"]/100),
                                                       DW1000.anchorRangeBuffer,
                                                       DW1000.tagRangeBuffer)

calInfoDict["anchorAntDelayDec"] = anchorAntDelayDec
calInfoDict["tagAntDelayDec"] = tagAntDelayDec

#Keep the tag delay at 0 and set anchor delay to the aggregate
#DW1000.anchor.setAntennaDelay(anchorAntDelayDec)
DW1000.clearBuffers() #clear buffers for next loop

DW1000.antDelayCalLoop(anchorAntDelayDec)

#DW1000.antDelayCalLoop(32900) #for a test

#Scaling calibration loop
for curDist in range(calInfoDict["startDist"],
                     calInfoDict["stopDist"]+calInfoDict["stepDist"],
                     calInfoDict["stepDist"]):

    input("Move tag to {0} cm and press enter to continue calibration...".format(curDist))
    
    while (len(DW1000.anchorRangeBuffer) < calInfoDict["numCalSamples"]):
        if not (DW1000.distMeasLoop()):
            print("ERROR READING DISTANCES")
            sys.exit()
    
    anchorDict["{0} cm".format(curDist)] = list(DW1000.anchorRangeBuffer)
    tagDict["{0} cm".format(curDist)] = list(DW1000.tagRangeBuffer)
    DW1000.clearBuffers() #clear buffers for next loop
 
anchorFitDict = DW1000.linearCurveFit(anchorDict.copy())
tagFitDict = DW1000.linearCurveFit(tagDict.copy())

DW1000.testInfoDict["device"] = "anchor"

DW1000.makeErrorPlotDist(anchorDict.copy(),plotInfoDict.copy())
DW1000.makeGaussianPlotDist(anchorDict.copy(),plotInfoDict.copy())

if plotInfoDict["scaleData"] == True:
    plotInfoDict["scaleData"] = False
    DW1000.makeErrorPlotDist(anchorDict.copy(),plotInfoDict.copy())
    DW1000.makeGaussianPlotDist(anchorDict.copy(),plotInfoDict.copy())
    plotInfoDict["scaleData"] = True

DW1000.testInfoDict["device"] = "tag"

DW1000.makeErrorPlotDist(tagDict.copy(),plotInfoDict.copy())
DW1000.makeGaussianPlotDist(tagDict.copy(),plotInfoDict.copy())

if plotInfoDict["scaleData"] == True:
    plotInfoDict["scaleData"] = False
    DW1000.makeErrorPlotDist(anchorDict.copy(),plotInfoDict.copy())
    DW1000.makeGaussianPlotDist(anchorDict.copy(),plotInfoDict.copy())
    plotInfoDict["scaleData"] = True

while True:
    try:
        if not (DW1000.distMeasLoop()):
            print("ERROR READING DISTANCES")
            sys.exit()

#        anchorDist["N/A"] = DW1000.anchorRangeBuffer[-1]        
#        tagDist["N/A"] = DW1000.tagRangeBuffer[-1]
#        
#        anchorDist = DW1000.scaleLinearData(anchorDist.copy(),
#                                            anchorFitDict["m"],
#                                            anchorFitDict["b"])
#        tagDist = DW1000.scaleLinearData(tagDist.copy(),
#                                         tagFitDict["m"],
#                                         tagFitDict["b"])
#
#        print("Anchor distance: {0} cm".format(anchorDist["N/A"]))
#        print("Tag distance: {0} cm".format(tagDist["N/A"]))

        anchorDist = DW1000.anchorRangeBuffer[-1]
        tagDist = DW1000.tagRangeBuffer[-1]
        
        anchorDist = DW1000.scaleLinearValue(anchorDist,
                                             anchorFitDict["m"],
                                             anchorFitDict["b"])
        tagDist = DW1000.scaleLinearValue(tagDist,
                                          tagFitDict["m"],
                                          tagFitDict["b"])

        print("Anchor distance: {0} cm".format(anchorDist))
        print("Tag distance: {0} cm".format(tagDist))

    except KeyboardInterrupt:
        sys.exit()