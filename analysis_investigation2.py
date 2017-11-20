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

# Custom Functions
from analysisFunctions import makeHeatmap

path = '../Investigation2/'
fileCoeff = 'coeff.csv'
fileRaw = 'raw.csv'
fileScaled = 'scaled.csv'
fileCam = 'webcam.csv'

coeff = np.genfromtxt(path+fileCoeff,delimiter=',')
raw = np.genfromtxt(path+fileRaw,delimiter=',')
scaled = np.genfromtxt(path+fileScaled,delimiter=',')
camDistances = np.genfromtxt(path+fileCam,delimiter=',')

slopes = coeff[0,:]
intercepts = coeff[1,:]

distances = range(5,55,5) # Distance axis
trialNo = range(1,raw.shape[1]+1)


print('slope stats: mean:%.2f stdev:%.2f min:%.2f max:%.2f'%(np.mean(slopes),np.std(slopes),np.max(slopes),np.min(slopes)))

#%% Functions

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
roomScaled = (raw - avIntercept) / avSlope
np.savetxt(path+'roomScaled.csv',roomScaled,delimiter=',')

#%% Error comparison
errorScaled = scaled - camDistances
errorRoomAvg = roomScaled - camDistances
errorRaw = raw - camDistances
maxError = np.max((errorScaled,errorRoomAvg,errorRaw))

#%% Heatmaps

makeHeatmap(errorScaled,distances,trialNo,'Scaled',maxError)
makeHeatmap(errorRoomAvg,distances,trialNo,'Avg',maxError)
makeHeatmap(errorRaw,distances,trialNo,'Raw',maxError)

#%% Histogram
fig1 = plt.figure()
plt.hist((errorRoomAvg),bins=3)
plt.title('Error Histogram')

#%% Examine error with distance
errorWDistance=np.mean(np.abs(errorRoomAvg),axis=1)


Ndistances = len(errorWDistance)
ind = np.arange(Ndistances)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,errorWDistance,width,color='r')
ax.set_title('Error at different distances %i Trials'%N,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Distance (cm)')
ax.set_xticklabels(distances)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

# Error as a function of angle
errorWTrials = np.mean(np.abs(errorRoomAvg),axis=0)
angles=[0,0,22.5,22.5,45,45,67.5,67.5,0,0,22.5,22.5,45,45,67.5,67.5,0,22.5,45,67.5]
covered=[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0]
fig2 = plt.figure()
plt.scatter(angles,errorWTrials)
plt.title('Error With Angle')

fig3 = plt.figure()
plt.scatter(covered,errorWTrials)
plt.title('Error of covered and non covered antenna')

#%% Averaged bar charts - Angles
indAngle = []
for angle in angles:
	indAngle.append(angle/22.5)
angleLabels=['0','22.5','45','67.5']
e1=[]
e2=[]
e3=[]
e4=[]
errorWAngle=[e1,e2,e3,e4]

for i in range(len(indAngle)):
	ind = int(indAngle[i])
	val = errorWTrials[i]
	errorWAngle[ind].append(val)

erroravgWAngle = np.mean(errorWAngle,axis=1)

Ndistances = len(erroravgWAngle)
ind = np.arange(Ndistances)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,erroravgWAngle,width,color='r')
ax.set_title('Error at different distances for %i Trials'%N,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Angle')
ax.set_xticklabels(angleLabels)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

#%% Averaged bar charts - Covered vs Uncovered

angleLabels=['Uncovered','Covered']
e1=[]
e2=[]
errorWCover=[e1,e2]

for i in range(len(covered)):
	ind = int(covered[i])
	val = errorWTrials[i]
	errorWCover[ind].append(val)

erroravgWCover=[]
erroravgWCover.append(np.mean(errorWCover[0]))
erroravgWCover.append(np.mean(errorWCover[1]))

Ndistances = len(angleLabels)
ind = np.arange(Ndistances)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,erroravgWCover,width,color='r')
ax.set_title('Covered and uncovered Antenna, for %i Trials'%N,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Angle')
ax.set_xticklabels(angleLabels)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()