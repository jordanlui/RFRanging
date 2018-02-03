# -*- coding: utf-8 -*-
"""
Created on Sun Nov 05 21:20:13 2017

@author: Jordan
Results analysis on RF Results
Investigation of error in different rooms, investigation 1
Static tests, not body mounted
"""

from __future__ import division
import numpy as np
import glob, os
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go

path = '../Investigation1/'
#fileCoeff = 'coeff.csv'
#fileRaw = 'raw.csv'
#fileScaled = 'scaled.csv'
#fileCam = 'webcam.csv'

data = np.genfromtxt(path+'unscaledDataInvestigation1.csv',delimiter=',')
distances = range(5,101,5)
coeff = data[20:,:]
raw = data[0:20,:] # Raw distance

scaleData = np.genfromtxt(path+'scaledDataInvestigation1.csv',delimiter=',')
scaled = data[0:20,:] # Indvidually scaled distance
slopes = coeff[0,:]
intercepts = coeff[1,:]
trialNo = range(1,raw.shape[1]+1)

room = scaleData = np.genfromtxt(path+'room.csv',delimiter=',')
orientation= scaleData = np.genfromtxt(path+'orientation.csv',delimiter=',')

print('slope stats: mean:%.2f stdev:%.2f min:%.2f max:%.2f'%(np.mean(slopes),np.std(slopes),np.max(slopes),np.min(slopes)))

#%% Functions
def makeHeatmap(data,distances,trialNo,nameOut,vmax):
    data = np.abs(data)
    fig,axis = plt.subplots()
    heatmap = axis.pcolor(data,cmap=plt.cm.Blues,vmax=vmax)
    axis.set_yticks(np.arange(data.shape[0])+0.5, minor=False)
    axis.set_xticks(np.arange(data.shape[1])+0.5, minor=False)
    plt.title('Heatmap'+nameOut)
    plt.ylabel('Distance (cm)')
    plt.xlabel('Trial Number')
    axis.set_yticklabels(distances)
    axis.set_xticklabels(trialNo)
    plt.colorbar(heatmap)
    plt.savefig('Heatmap'+nameOut+'.png',dpi=100)


#%% Scale Data using a room average
avSlope = np.mean(slopes)
avIntercept = np.mean(intercepts)
roomScaled = (raw - avIntercept) / avSlope # Scale our values with an average slope and intercept value for the N trials
np.savetxt(path+'roomScaled.csv',roomScaled,delimiter=',')

print 'We will scale all values with an averaged slope %.4f and intercept %.4f'%(avSlope,avIntercept)

#%% Error calculation
errorScaled = (scaled.transpose() - distances).transpose()
errorRoomAvg = (roomScaled.transpose() - distances).transpose()
errorRoomAvgRel = ((roomScaled.transpose() - distances)/distances).transpose() # Relative error or % error
errorRaw = (raw.transpose() - distances).transpose()
maxError = np.max((errorScaled,errorRoomAvg,errorRaw))

np.savetxt(path+'errorRoomAvg.csv',errorRoomAvg,delimiter=',')
np.savetxt(path+'errorRoomAvgRel.csv',errorRoomAvgRel,delimiter=',')


# Error by room and orientation
data = errorRoomAvg
#dataOut = np.zeros((data.shape[0]*data.shape[1],3))
dataOut = [[], [], []]
# Loop through columns
for i in range(0,data.shape[1]): 
	col = data[:,i]
	for j in col:
		dataOut[0].append(j)
		dataOut[1].append(room[i])
		dataOut[2].append(orientation[i])
dataOut = np.array((dataOut)).transpose()

np.savetxt(path+'errorforDiffRoomOrientation.csv',dataOut,delimiter=',')
#%% Heatmaps

makeHeatmap(errorScaled,distances,trialNo,'Scaled',maxError)
makeHeatmap(errorRoomAvg,distances,trialNo,'Avg',maxError)
makeHeatmap(errorRaw,distances,trialNo,'Raw',maxError)

#%% Histogram
fig1 = plt.figure()
plt.hist(([i for row in errorRoomAvg for i in row]),bins=10)
plt.title('Error Histogram')

#%% Average error by room



#%% Error by orientation

