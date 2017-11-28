# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 15:15:05 2017

@author: Jordan

Analysis Functions

"""
#%% Libraries
import matplotlib.pyplot as plt
import numpy as np

#import plotly.plotly as py
#import plotly.graph_objs as go


#%% Visualizations
def makeHeatmap(data,distances,trialNo,nameOut,vmax):
	# Creates a 2D heatmap to easily visualize error across different trials, distances
	data = np.abs(data)
	fig,axis = plt.subplots()
	if vmax ==0:
		vmax = np.max(data)
	heatmap = axis.pcolor(data,cmap=plt.cm.Blues,vmax=vmax)
	axis.set_yticks(np.arange(data.shape[0])+0.5, minor=False)
	axis.set_xticks(np.arange(data.shape[1])+0.5, minor=False)
	plt.title('Heatmap, '+nameOut)
	plt.ylabel('Distance (cm)')
	plt.xlabel('Trial Number')
	axis.set_yticklabels(distances)
	axis.set_xticklabels(trialNo)
	plt.colorbar(heatmap)
	plt.savefig('Heatmap'+nameOut+'.png',dpi=100)

def errorStats(data):
	output = 'Error max,mean,median,min,stdev is %.2f,%.2f,%.2f,%.2f,%.2f'%(np.max(data),np.mean(data),np.median(data),np.min(data),np.std(data))
	return output

def calcStats(x):
	outputString = 'max %.2f, min %.2f, mean: %.2f, median: %.2f, stdev: %.2f'%(np.max((x)), np.min((x)),np.mean((x)), np.median((x)), np.std(x))
	print outputString
	return np.max((x)), np.min((x)),np.mean((x)), np.median((x)), np.std(x)

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