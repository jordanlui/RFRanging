# -*- coding: utf-8 -*-
"""
Created on Sun Nov 05 21:20:13 2017

@author: Jordan
Results analysis on RF Results
"""

from __future__ import division
import numpy as np
import glob, os
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go

# %% Custom Functions
from analysisFunctions import makeHeatmap

def errorStats(data):
	output = 'Error max,mean,median,min,stdev is %.2f,%.2f,%.2f,%.2f,%.2f'%(np.max(data),np.mean(data),np.median(data),np.min(data),np.std(data))
	return output

#%% Parameters, setup, file loading
path = '../Investigation3/'
fileCoeff = 'coeff.csv'
fileRaw = 'raw.csv'
fileScaled = 'scaled.csv'
fileCam = 'webcam_corrected.csv'
label = 'labels.csv'
angles = 'angles.csv'

coeff = np.genfromtxt(path+fileCoeff,delimiter=',')
raw = np.genfromtxt(path+fileRaw,delimiter=',')
scaled = np.genfromtxt(path+fileScaled,delimiter=',')
camDistances = np.genfromtxt(path+fileCam,delimiter=',')
labels = np.genfromtxt(path+label,delimiter=',',skip_header=1)
angles = np.genfromtxt(path+angles,delimiter=',',skip_header=0)
slopes = coeff[0,:]
intercepts = coeff[1,:]

distances = range(5,41,5) # Distance axis
trialNo = range(1,raw.shape[1]+1)

# Retrieve info from labels
trials = labels[:,0]
#angles = labels[:,1]
stationary = labels[:,4]

print('slope stats: mean:%.2f stdev:%.2f min:%.2f max:%.2f'%(np.mean(slopes),np.std(slopes),np.max(slopes),np.min(slopes)))


#%% Plot Slope data
N = len(slopes)
ind = np.arange(N)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,slopes,width,color='r')
ax.set_title('Slope values for %i Trials'%N,fontsize=16)
ax.set_ylabel('slope value')
ax.set_xlabel('Trial')
plt.show()

N = len(intercepts)
ind = np.arange(N)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,intercepts,width,color='r')
ax.set_title('Intercept values for %i Trials'%N,fontsize=16)
ax.set_ylabel('Intercept value, cm')
ax.set_xlabel('Trial')
plt.show()

#%% Scale Data using a room average
avSlope = np.mean(slopes)
avIntercept = np.mean(intercepts)
roomScaled = (raw - avIntercept) / avSlope # Scale raw data with average trial data
np.savetxt(path+'roomScaled.csv',roomScaled,delimiter=',')

#%% Error comparison
errorScaled = scaled - camDistances # Error of data scaled on per-trial basis
errorRoomAvg = roomScaled - camDistances # Error of data scaled with trial average
errorRaw = raw - camDistances # Error on raw data
maxError = np.max((errorScaled,errorRoomAvg,errorRaw)) # Max error, cm
#print 'Error max,mean,median,min,stdev for Room Avg Scaling is %.2f,%.2f,%.2f,%.2f,%.2f'%(np.max(errorRoomAvg),np.mean(errorRoomAvg),np.median(errorRoomAvg),np.min(errorRoomAvg),np.std(errorRoomAvg))

print 'Individually scaled: ', errorStats(np.abs(errorScaled))
print 'Room Avg: ', errorStats(np.abs(errorRoomAvg))
print 'Raw: ', errorStats(np.abs(errorRaw))

#%% Heatmaps - Different Scales

makeHeatmap(errorScaled,distances,trialNo,'Individually Scaled',np.max(errorScaled))
makeHeatmap(errorRoomAvg,distances,trialNo,'Scaled with Room Average',np.max(errorRoomAvg))
makeHeatmap(errorRaw,distances,trialNo,'Raw Data',maxError)


# Heat maps - Matching Scale values

makeHeatmap(errorScaled,distances,trialNo,'Individually Scaled',maxError)
makeHeatmap(errorRoomAvg,distances,trialNo,'Scaled with Room Average',maxError)
#%% Histogram
fig1 = plt.figure()
plt.hist((errorRoomAvg),bins=3)
plt.title('Error Histogram')

#%% Examine error with distance
errorWDistance=np.mean(np.abs(errorRoomAvg),axis=1)


Ndistances = len(distances) # Number of distances
ind = np.arange(Ndistances) # List of indices
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,errorWDistance,width,color='r')
ax.set_title('Error at different distances %i Trials'%N,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Distance (cm)')
ax.set_xticklabels(distances)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

#%% Error as a function of gross arm angle
errorWTrials = np.mean(np.abs(errorRoomAvg),axis=0)

#fig2 = plt.figure()
#plt.scatter(angles,errorWTrials)
#plt.title('Error With Angle')

##%% Averaged bar charts - Angles
## Calculate the error as a function of angle
## This code needs to be made more extensible in the future
#
#indAngle = []
#for angle in angles:
#	indAngle.append(angle/22.5)
#angleLabels=['0','22.5','45','67.5']
#e1=[]
#e2=[]
#e3=[]
#e4=[]
#errorWAngle=[e1,e2,e3,e4]
#
#for i in range(len(indAngle)): # Iterate through angles
#	ind = int(indAngle[i]) # Grab the index value
#	val = errorWTrials[i]  # Grab the average error for that angle
#	errorWAngle[ind].append(val) # Sort it into the appropriate bin
#
#erroravgWAngle = []
#for angle in errorWAngle:
#	erroravgWAngle.append(np.mean(angle)) # Average error at each angle
#
#Ndistances = len(erroravgWAngle)
#
#ind = np.arange(Ndistances)
#width = 0.5
#fig, ax = plt.subplots()
#rects1 = ax.bar(ind,erroravgWAngle,width,color='r')
#ax.set_title('Error at different angles for %i Trials'%N,fontsize=16)
#ax.set_ylabel('Average error, cm')
#ax.set_xlabel('Angle')
#ax.set_xticklabels(angleLabels)
#ax.set_xticks(np.arange(Ndistances), minor=False)
#plt.show()

#%% Effects of tag-anchor angle


erroravgWAngle = np.reshape(errorRoomAvg,(288,1))

Ndistances = len(erroravgWAngle)

ind = np.arange(Ndistances)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.scatter(angles,erroravgWAngle,width,color='r')
ax.set_title('Error at different angles for %i Trials'%N,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Angle')
#ax.set_xticklabels(angleLabels)
#ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()
