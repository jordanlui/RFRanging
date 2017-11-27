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
from scipy import stats
import scipy
import math

# %% Custom Functions
from analysisFunctions import makeHeatmap

def errorStats(data):
	output = 'Error max,mean,median,min,stdev is %.2f,%.2f,%.2f,%.2f,%.2f'%(np.max(data),np.mean(data),np.median(data),np.min(data),np.std(data))
	return output

def cleanNaN(x,y):
	newx = []
	newy = []
	for i,j in zip(x,y):
		if i > 0:
			newx.append(i)
			newy.append(j)
		else:
			print 'found a NaN'
			pass
	x = newx
	y = newy
	return x,y

def binPlot(x,y,bins=6):
	# Accepts two vectors, bins the data and plots
	# Also returns the values of the bins (x-axis)
	if len(x) == len(y):
		results = scipy.stats.binned_statistic(x,y,statistic='mean',bins=bins)

#		N = bins
		ind = []
		ind2 = []
		for i in range(len(results.bin_edges)-1):
			ind.append(np.mean((results.bin_edges[i:i+2])))
			ind2.append('%.0f-%.0f'%(results.bin_edges[i],results.bin_edges[i+1]))
		ind = np.round(ind,decimals=1)
		width = 5
		fig, ax = plt.subplots()
		ax.bar(ind,results.statistic,width,color='r')
		ax.set_title('Average error at different angles %i Trials'%numTrials,fontsize=16)
		ax.set_ylabel('Error (cm)')
		ax.set_xlabel('Angle bin')
		plt.show()
		return results, ind, ind2
	
	
	else:
		print 'error! mismatch length!'
		return
def boxPlot(results):
	# Box plot of data that results from a binned_statistic
	data = []
	for i in range(N): # Loop through bins
		mask=results.binnumber-1 == i # Create mask
		binvalues = np.ma.array(y,mask=~mask) # Grab the values for that mask
		data.append(binvalues.compressed()) # Add values to a list
	
	fig,ax = plt.subplots()
	ax.boxplot(np.abs(data),labels=ind2)
	ax.set_title('Error at different angles')
	plt.show()
	return fig,ax

#%% Parameters, setup, file loading
path = '../Investigation3/'
fileCoeff = 'coeff.csv'
fileRaw = 'raw.csv'
fileScaled = 'scaled.csv'
fileCam = 'webcam_corrected.csv'
label = 'labels.csv'
angles = 'angles.csv' # Actual angles between two antenna

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
realDistances = np.reshape(camDistances,(camDistances.shape[0]*camDistances.shape[1],1))

# Retrieve info from labels
trials = labels[:,0]
#angles = labels[:,1]
stationary = labels[:,4]

print('slope stats: mean:%.2f stdev:%.2f min:%.2f max:%.2f'%(np.mean(slopes),np.std(slopes),np.max(slopes),np.min(slopes)))


#%% Plot Slope data
numTrials = len(slopes)
ind = np.arange(numTrials)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,slopes,width,color='r')
ax.set_title('Slope values for %i Trials'%numTrials,fontsize=16)
ax.set_ylabel('slope value')
ax.set_xlabel('Trial')
plt.show()

#N = len(intercepts)
#ind = np.arange(N)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,intercepts,width,color='r')
ax.set_title('Intercept values for %i Trials'%numTrials,fontsize=16)
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
errorRoomAvgRel = (roomScaled - camDistances)/camDistances # Relative error or % error
errorRaw = raw - camDistances # Error on raw data
maxError = np.max((errorScaled,errorRoomAvg,errorRaw)) # Max error, cm
#print 'Error max,mean,median,min,stdev for Room Avg Scaling is %.2f,%.2f,%.2f,%.2f,%.2f'%(np.max(errorRoomAvg),np.mean(errorRoomAvg),np.median(errorRoomAvg),np.min(errorRoomAvg),np.std(errorRoomAvg))

print 'Individually scaled: ', errorStats(np.abs(errorScaled))
print 'Room Avg: ', errorStats(np.abs(errorRoomAvg))
print 'Raw: ', errorStats(np.abs(errorRaw))

#%% Heatmaps - Different Scales

#makeHeatmap(errorScaled,distances,trialNo,'Individually Scaled',np.max(errorScaled))
#makeHeatmap(errorRoomAvg,distances,trialNo,'Scaled with Room Average',np.max(errorRoomAvg))
#makeHeatmap(errorRaw,distances,trialNo,'Raw Data',np.max(errorRaw))

makeHeatmap(errorScaled/camDistances,distances,trialNo,'Relative Individually Scaled',np.max(errorScaled/camDistances))
makeHeatmap(errorRoomAvgRel,distances,trialNo,'Relative Scaled with Room Average',np.max(errorRoomAvgRel/camDistances))
makeHeatmap(errorRaw/camDistances,distances,trialNo,'Relative Raw Data',np.max(errorRaw/camDistances))

# Heat maps - Matching Scale values

#makeHeatmap(errorScaled,distances,trialNo,'Individually Scaled',maxError)
#makeHeatmap(errorRoomAvg,distances,trialNo,'Scaled with Room Average',maxError)
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
ax.set_title('Error at different distances %i Trials'%numTrials,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Distance (cm)')
ax.set_xticklabels(distances)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

errorWDistanceRel=np.mean(np.abs(errorRoomAvg),axis=1) / distances * 100

Ndistances = len(distances) # Number of distances
ind = np.arange(Ndistances) # List of indices
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,errorWDistanceRel,width,color='r')
ax.set_title('Percent Error at different distances %i Trials'%numTrials,fontsize=16)
ax.set_ylabel('% error, cm')
ax.set_xlabel('Distance (cm)')
ax.set_xticklabels(distances)
ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

#results, ind, ind2 = binPlot(distances,errorWDistanceRel,bins=6)
#boxPlot(results)



#%% Distance  effects, relative error - INCOMPLETE
y=[]
if errorRoomAvg.shape[1] > 1:
	y = np.reshape(errorRoomAvg,(errorRoomAvg.shape[0]*errorRoomAvg.shape[1],1))
y = np.ndarray.tolist(y)
y = [i[0] for i in y]

x = np.ndarray.tolist(realDistances)
x = [i[0] for i in x]
#erroravgWAngleRel = np.asarray(erroravgWAngleRel)
#y = np.ndarray.tolist(erroravgWAngleRel)
#y = [i[0] for i in erroravgWAngleRel]
#x = np.ndarray.tolist(realDistances)
x,y = cleanNaN(x,y) # Remove NaN values
bins = 8
N = bins	
results,ind,ind2 = binPlot(x,y,bins=bins) # Binned data, index midpoints, and index string names
boxPlot(results) # Box plot of results

#%% Effects of tag-anchor angle

# Write angles out as vector
erroravgWAngle = np.copy(errorRoomAvg)

Ndistances = len(erroravgWAngle)

ind = np.arange(Ndistances)
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.scatter(angles,np.abs(erroravgWAngle),width,color='r')
ax.set_title('Error at different angles for %i Trials'%numTrials,fontsize=16)
ax.set_ylabel('Average error, cm')
ax.set_xlabel('Angle')
#ax.set_xticklabels(angleLabels)
#ax.set_xticks(np.arange(Ndistances), minor=False)
plt.show()

# Binned values
angles = np.reshape(angles,(len(angles),))
#x = np.copy(angles)

# Function Staging
if erroravgWAngle.shape[1] > 1:
	y = np.reshape(erroravgWAngle,(len(angles),))
x = np.copy(angles)

x,y = cleanNaN(x,y) # Remove NaN values
bins = 6
N = bins	
results,ind,ind2 = binPlot(x,y,bins=bins) # Binned data, index midpoints, and index string names
boxPlot(results) # Box plot of results

#%% Angle effects, relative error
#if erroravgWAngle.shape[1] > 1:
#	y = np.reshape(erroravgWAngle,(len(angles),))
y=[]
if erroravgWAngle.shape[1] > 1:
	y = np.reshape(erroravgWAngle,(len(angles),)) # Grab y values again
erroravgWAngleRel=[]
for i in range(len(y)):
	erroravgWAngleRel.append(float(y[i] / realDistances[i]))
y = erroravgWAngleRel
#x = np.ndarray.tolist(angles)
#x = [i[0] for i in x]
x = angles
#erroravgWAngleRel = np.asarray(erroravgWAngleRel)
#y = np.ndarray.tolist(erroravgWAngleRel)
#y = [i[0] for i in erroravgWAngleRel]
#x = np.ndarray.tolist(realDistances)
x,y = cleanNaN(x,y) # Remove NaN values
bins = 6
N = bins	
results,ind,ind2 = binPlot(x,y,bins=bins) # Binned data, index midpoints, and index string names
fig,ax = boxPlot(results) # Box plot of results
#ax.set_ylabel('hi')
#ax.set_xlabel('yes')
#ax.set_title('Error ')
#plt.show()

#%% Manual bin method
# Uses nice round numbers but this code is not currently extensible or easily customized
bins = range(90,180)[::10]
M = len(bins)
errAngle = [[] for i in range(M)] # Preallocate list

for i in range(len(x)): # Loop through all values
	val = y[i]
	angle = x[i]
	for j in range(len(bins)-1): # Loop through bins
		if angle < bins[0]:
			errAngle[0].append(val)
		elif angle > bins[-1]:
			errAngle[-1].append(val)
		elif angle >= bins[j] and angle < bins[j+1]:
			errAngle[j].append(val)
print 'check length', sum([len(row) for row in errAngle])

ind = bins
results = [np.mean(i) for i in errAngle]
width = 7
fig, ax = plt.subplots()
rects1 = ax.bar(ind,results,width,color='r')
ax.set_title('Average error at different angles %i Trials'%numTrials,fontsize=16)
ax.set_ylabel('Error (cm)')
ax.set_xlabel('Angle bin')
plt.show()