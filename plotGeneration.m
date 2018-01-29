% Plots and results from RF Study
% Recordings by Jordan Lui and Marilyn Zhou. jdlui@sfu.ca
% 2017 - 2018 Simon Fraser University
clc
clear all
close all
%% Load Files
roomOrientation = csvread('Effect of Room and Orientation.csv',2,2); % Slope effects for different rooms (rows) and different Orientations (columns)
errorRoomAVGInv3 = csvread('error by Trial and Distance - Investigation 2 - errorRoomAvg.csv');
errorRoomAVGRelInv3 = csvread('Relative error by Trial and Distance - Investigation 2 - errorRoomAvgRel.csv');
errorAngle = csvread('errorAngle.csv');
errorAngleRel = csvread('errorAngleRel.csv');
errorCovered = csvread('errorCovered.csv');
errorJitter = csvread('errorJitter.csv'); % Relative error at various distances. Col 2 denotes whether wrist is moving or not. 1 = stationary. 0 = jitter
%% Data Correction

roomOrientation(roomOrientation==0) = nan;
%% Generate Plots
orientationLabel = {'A';'B';'C';'D';'E';'F'};
roomLabel = {'Apartment','Uni Room 1','Uni Room 2','Uni Room 3','Office'};

figure(7)
boxplot(roomOrientation)
ylim([0.9 2.1]);
title('Figure 7 Linearization parameter for different antenna orientations')
set(gca,'xticklabel',orientationLabel)
ylabel('Linearization Parameter')
xlabel('Polarization')

figure(8)
boxplot(roomOrientation')
% ylim([0.9 2.1]);
title('Figure 8 Linearization parameter for different rooms')
set(gca,'xticklabel',roomLabel)
ylabel('Linearization Parameter')
xlabel('Room')

distanceLabel = {'5','10','15','20','25','30','35','40'};
figure(9)
boxplot(abs(errorRoomAVGInv3'));
set(gca,'xticklabel',distanceLabel)
title('Fig 9 Absolute error w/ Distance')
ylabel('Error (cm)')
xlabel('Distance (cm)')

figure(10)
boxplot(100*abs(errorRoomAVGRelInv3'));
set(gca,'xticklabel',distanceLabel)
title('Fig 10 Relative error w/ Distance')
ylabel('Percent Error')
ylim([0 300])
xlabel('Distance (cm)')

angleLabel = {'90-100','100-110','110-120','120-130','130-140','140-150','150-160'};
figure(11)
boxplot(abs(errorAngle(:,2)),errorAngle(:,3))
title('Error with angle')
xlabel('Angle Range')
ylabel('Error (mm)')
ylim([0 20])
set(gca,'xticklabel',angleLabel)

figure(12)
boxplot(abs(100*errorAngleRel(:,2)),errorAngleRel(:,3))
title('Relative Error with angle')
xlabel('Angle Range')
ylabel('Relative Error (%)')
ylim([0 120])
set(gca,'xticklabel',angleLabel)

coverLabel = {'Uncovered', 'Covered'};
figure(13)
boxplot(errorCovered(:,1),errorCovered(:,2))
title('Error effect of Obstruction, 8mm foam')
ylabel('Error (mm)')
set(gca,'xticklabel',coverLabel)

jitterLabel = {'Stationary', 'Jitter'};
figure(13)
boxplot(100*errorJitter(:,1),errorJitter(:,2))
title('Error effect of Jitter')
ylabel('Percent Error (%)')
set(gca,'xticklabel',jitterLabel)
ylim([0 100])