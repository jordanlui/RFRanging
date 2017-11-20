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