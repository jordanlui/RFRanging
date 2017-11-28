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
from analysisFunctions import makeHeatmap, calcStats, errorStats

def plotSlopeIntercepts(slopes,intercepts, numTrials):
	numTrials = len(slopes)
	ind = np.arange(numTrials)
	width = 0.5
	fig, ax = plt.subplots()
	rects1 = ax.bar(ind,slopes,width,color='r')
	ax.set_title('Slope values for %i Trials'%numTrials,fontsize=16)
	ax.set_ylabel('slope value')
	ax.set_xlabel('Trial')
	plt.show()
	
	width = 0.5
	fig, ax = plt.subplots()
	rects1 = ax.bar(ind,intercepts,width,color='r')
	ax.set_title('Intercept values for %i Trials'%numTrials,fontsize=16)
	ax.set_ylabel('Intercept value, cm')
	ax.set_xlabel('Trial')
	plt.show()

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

def binPlot(x,y,bins=6, title='Binned Error'):
	# Accepts two lists, bins the data and plots
	# Also returns the values of the bin midpoint (ind) and a string describing bin span (ind2)
	x,y = cleanNaN(x,y) # Remove NaN values
	if len(x) == len(y):
		results = scipy.stats.binned_statistic(x,y,statistic='mean',bins=bins)

#		N = bins
		ind = []
		ind2 = []
		for i in range(len(results.bin_edges)-1):
			ind.append(np.mean((results.bin_edges[i:i+2])))
			ind2.append('%.0f-%.0f'%(results.bin_edges[i],results.bin_edges[i+1]))
		ind = np.round(ind,decimals=1)
		width = 3
		fig, ax = plt.subplots()
		ax.bar(ind,results.statistic,width,color='r')
		ax.set_title(title,fontsize=16)
#		ax.set_ylabel('Error (cm)')
#		ax.set_xlabel('Angle bin')
		plt.show()
		return results, ind, ind2
		
	else:
		print 'error! mismatch length!'
		return
def boxPlot(results,y,title='Error at different angles'):
	# Box plot of data that results from a binned_statistic results
	N = len(results.statistic) # number of bins
	data = []
	for i in range(N): # Loop through bins
		mask=results.binnumber-1 == i # Create mask
		binvalues = np.ma.array(y,mask=~mask) # Grab the values for that mask
		data.append(binvalues.compressed()) # Add values to a list
	
	fig,ax = plt.subplots()
	ax.boxplot(np.abs(data),labels=ind2)
	ax.set_title(title)
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
distances = range(5,41,5) # Distance axis

coeff = np.genfromtxt(path+fileCoeff,delimiter=',')
raw = np.genfromtxt(path+fileRaw,delimiter=',')
scaled = np.genfromtxt(path+fileScaled,delimiter=',')
camDistances = np.genfromtxt(path+fileCam,delimiter=',')
labels = np.genfromtxt(path+label,delimiter=',',skip_header=1)
angles = np.genfromtxt(path+angles,delimiter=',',skip_header=0)

# Derive and format values
slopes = coeff[0,:]
intercepts = coeff[1,:]
realDistances = np.reshape(camDistances,(camDistances.shape[0]*camDistances.shape[1],1))
realDistances = [i[0] for i in realDistances]

# Retrieve info from labels
trialLabel = labels[:,0]
#grossAngle = labels[:,1]
stationaryLabel = labels[:,4] # Designates whether arm was completely stationary or rocking motion
numTrials = len(labels) # Number of Trials

#print('slope stats: mean:%.2f stdev:%.2f min:%.2f max:%.2f'%(np.mean(slopes),np.std(slopes),np.max(slopes),np.min(slopes)))
calcStats(slopes)

#%% Plot Slope data
plotSlopeIntercepts(slopes,intercepts, numTrials)

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
errorAll = np.reshape(errorRoomAvg,(errorRoomAvg.shape[0]*errorRoomAvg.shape[1]),1) # All error for room avg, cm
errorAllRel = errorAll / realDistances

print 'Individually scaled: ', errorStats(np.abs(errorScaled))
print 'Room Avg: ', errorStats(np.abs(errorRoomAvg))
print 'Raw: ', errorStats(np.abs(errorRaw))

#%% Heatmaps - Different Scales
makeHeatmap(errorScaled/camDistances,distances,trialLabel,'Relative Individually Scaled',np.max(errorScaled/camDistances))
makeHeatmap(errorRoomAvgRel,distances,trialLabel,'Relative Scaled with Room Average',np.max(errorRoomAvgRel/camDistances))
makeHeatmap(errorRaw/camDistances,distances,trialLabel,'Relative Raw Data',np.max(errorRaw/camDistances))

#%% Histogram
fig1 = plt.figure()
plt.hist((errorRoomAvg),bins=3)
plt.title('Error Histogram')

#%% Examine error with distance
erroravgWDistance=np.mean(np.abs(errorRoomAvg),axis=1)

Ndistances = len(distances) # Number of distances
ind = np.arange(Ndistances) # List of indices
width = 0.5
fig, ax = plt.subplots()
rects1 = ax.bar(ind,erroravgWDistance,width,color='r')
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



title = 'Absolute error as a function of distance'
results, ind, ind2 = binPlot(realDistances,np.abs(errorAll),bins=8,title=title)
boxPlot(results,np.abs(errorAll),title=title)

title = 'Relative error as a function of distance'
results, ind, ind2 = binPlot(realDistances,np.abs(errorAllRel),bins=8,title=title)
boxPlot(results,np.abs(errorAllRel),title=title)



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
title = 'Absolute error (cm) as a function of angle'
results,ind,ind2 = binPlot(x,y,bins=bins,title=title) # Binned data, index midpoints, and index string names
boxPlot(results, y, title=title) # Box plot of results

#%% Angle effects, relative error

y=[]
if erroravgWAngle.shape[1] > 1:
	y = np.reshape(erroravgWAngle,(len(angles),)) # Grab y values again
erroravgWAngleRel=[]
for i in range(len(y)):
	erroravgWAngleRel.append(float(y[i] / realDistances[i]))
y = erroravgWAngleRel

x = angles

x,y = cleanNaN(x,y) # Remove NaN values
bins = 6
N = bins	
title='Relative error as a function of angle'
results,ind,ind2 = binPlot(x,y,bins=bins,title=title) # Binned data, index midpoints, and index string names
fig,ax = boxPlot(results, y, title=title) # Box plot of results


#%% Manual bin method
# Uses nice round numbers but this code is not currently extensible or easily customized
#bins = range(90,180)[::10]
#M = len(bins)
#errAngle = [[] for i in range(M)] # Preallocate list
#
#for i in range(len(x)): # Loop through all values
#	val = y[i]
#	angle = x[i]
#	for j in range(len(bins)-1): # Loop through bins
#		if angle < bins[0]:
#			errAngle[0].append(val)
#		elif angle > bins[-1]:
#			errAngle[-1].append(val)
#		elif angle >= bins[j] and angle < bins[j+1]:
#			errAngle[j].append(val)
#print 'check length', sum([len(row) for row in errAngle])
#
#ind = bins
#results = [np.mean(i) for i in errAngle]
#width = 7
#fig, ax = plt.subplots()
#rects1 = ax.bar(ind,results,width,color='r')
#title = 'Absolute error (cm) as a function of angle'
#ax.set_title(title,fontsize=16)
#ax.set_ylabel('Error (cm)')
#ax.set_xlabel('Angle bin')
#plt.show()