% Plots and results from RF Study
% Recordings by Jordan Lui and Marilyn Zhou. jdlui@sfu.ca
% 2017 - 2018 Simon Fraser University
clc
clear all
close all
%% Load Files
slopesByRoomOrientation = csvread('slopesByRoomOrientation.csv',2,2); % Slope effects for different rooms (rows) and different Orientations (columns)
slopeInterceptByRoomOrientation = csvread('parameters_Investigation1')
errorRoomAVGInv3 = csvread('error by Trial and Distance - Investigation 2 - errorRoomAvg.csv');
errorRoomAVGRelInv3 = csvread('Relative error by Trial and Distance - Investigation 2 - errorRoomAvgRel.csv');
errorAngle = csvread('errorAngle.csv'); % [angle, error(cm), angle bin]
errorAngleRel = csvread('errorAngleRel.csv'); % [angle, error(%), angle bin]
errorCovered = csvread('errorCovered.csv'); % Col 2 denotes whether obstructed or not. 0 = not obstructed, 1=obstructed.
errorJitter = csvread('errorJitter.csv'); % Error (cm) at various distances. Col 2 denotes whether wrist is moving or not. 1 = stationary. 0 = jitter
errorRoomAVGInv1 = csvread('errorforDiffRoomOrientation_Investigation1.csv')'; % Error values from Investigation 1. Col 1 is error, col 2 room type, col 3 orientation
%% Data Correction
slopesByRoomOrientation(slopesByRoomOrientation==0) = nan;
orientationLabel = {'A';'B';'C';'D';'E';'F'};
roomLabel = {'Apartment','Uni Room 1','Uni Room 2','Uni Room 3','Office'};

[M N] = size(slopesByRoomOrientation);
normality_Orientation = ones(1,N) .* -1;
ttestOrientation = ones(N,N) * -1;
%% Effect of different Rooms
% Box plot average
figure(3)
boxplot(slopesByRoomOrientation')
title('Linearization parameter for different rooms')
set(gca,'xticklabel',roomLabel)
ylabel('Linearization Parameter')
xlabel('Room')
saveas(gcf,'RoomsSlopeBoxPlot.jpg')

% Box plot on all
figure(4)
boxplot((errorRoomAVGInv1(:,1)),errorRoomAVGInv1(:,2))
title('Error in different rooms')
set(gca,'xticklabel',roomLabel)
ylabel('Error (cm)')
xlabel('Room')
saveas(gcf,'RoomsBoxPlot.jpg')


% Norm plot with linear characteristics indicates that we may have normal
% data.
figure(5)
normplot(errorRoomAVGInv1(:,1))
title('Check Normality for orientations')
saveas(gcf,'RoomsNormalDistribution.jpg')


% Power Testing on slope values by room
normality_Room = ones(1,M) .* -1;
figure(8)
normplot(slopesByRoomOrientation([1 2 4],:)')
title('Check Normality for Rooms')
saveas(gcf,'RoomsSlopeNormalDistribution.jpg')
ttestRoom = ones(M,M) * -1;
for i=1:M % Check Lillie normal distribution test for samples of 4 or more
    x = slopesByRoomOrientation(i,:);
    if length(x(~isnan(x))) > 3
        normality_Room(i) = lillietest(x);
    end
end

for i =1:M % stat power test on all different rooms
    for j = 1:M
        if i ~= j
            x = slopesByRoomOrientation(i,:);
            y = slopesByRoomOrientation(j,:);
            [h,sig,ci] = ttest2(x,y);
            if h == 1
                sprintf('Rejected null hypothesis for t-test between room %i,%i',i,j)
            end
            ttestRoom(j,i) = h;
            [p,h] = ranksum(x,y);
            if h==1
                sprintf('Rejected null hypothesis for Wilcoxon test between room %i,%i',i,j)
            end
        end
    end
end

% Statistical analysis on error values of different rooms
statTestRooms = []; % 'room1, room2, t-test outcome h0/h1, significance t-test, Wilcoxon outcom h0/h1, p Wilcoxon, N1, N2, lillie(x), lillie(y)'
numRooms = max(errorRoomAVGInv1(:,2));
medianErrorRooms = [];
for i = 1:numRooms
    for j = 1:numRooms
        if i ~= j
            x = errorRoomAVGInv1(find(errorRoomAVGInv1(:,2)==i),1);
            y = errorRoomAVGInv1(find(errorRoomAVGInv1(:,2)==j),1);
            [h1,sig,ci] = ttest2(x,y);
            [p h2] = ranksum(x,y);
%             [sig p] = powerTests(x,y);
            statTestRooms = [statTestRooms; i j h1 sig h2 p length(x) length(y) lillietest(x) lillietest(y)];
            medianErrorRooms(i) = median(x);
            
        end
    end
end


%% Different Orientations
% Box plot on average data
figure(6);
boxplot(slopesByRoomOrientation)
ylim([0.9 2.1]);
title('Figure 7 Linearization parameter for different antenna orientations')
set(gca,'xticklabel',orientationLabel)
ylabel('Linearization Parameter')
xlabel('Orientation')
saveas(gcf,'OrientationSlopeBoxPlot.jpg')

% Box plot on all data
figure(7)
boxplot((errorRoomAVGInv1(:,1)),errorRoomAVGInv1(:,3))
title('Error for different antenna orientations')
set(gca,'xticklabel',orientationLabel)
ylabel('Error (cm)')
xlabel('Orientation')
saveas(gcf,'OrientationBoxPlot.jpg')

% Power testing on slope values by orientation

for i=1:N % Check Lillie normal distribution test for samples of 4 or more
    x = slopesByRoomOrientation(:,i);
    if length(x(~isnan(x))) > 3
        normality_Orientation(i) = lillietest(x);
    end
end

for i =1:N % stat power test on all different orientations
    for j = 1:N
        if i ~= j
            x = slopesByRoomOrientation(:,i);
            y = slopesByRoomOrientation(:,j);
            [h,sig,ci] = ttest2(x,y);
            if h == 1
                sprintf('Rejected null hypothesis for t-test between orientation %i,%i',i,j)
            end
            ttestOrientation(j,i) = h;
            [p,h] = ranksum(x,y);
            if h==1
                sprintf('Rejected null hypothesis for Wilcoxon test between orientation %i,%i',i,j)
            end
        end
    end
end

% Statistical analysis on error values of different Orientation 
statTestOrientation = []; % 'orientation1, orientation2, t-test outcome h0/h1, significance t-test, Wilcoxon outcom h0/h1, p Wilcoxon, N1, N2, lillie(x), lillie(y)'
numOrientations = max(errorRoomAVGInv1(:,3));
medianErrorOrientation = [];
for i = 1:numOrientations
    for j = 1:numOrientations
        if i ~= j
            x = errorRoomAVGInv1(find(errorRoomAVGInv1(:,3)==i),1);
            y = errorRoomAVGInv1(find(errorRoomAVGInv1(:,3)==j),1);
%             x = abs(x); y = abs(y);
            [h1,sig,ci] = ttest2(x,y);
            [p h2] = ranksum(x,y);
%             [sig p] = powerTests(x,y);
            statTestOrientation = [statTestOrientation; i j h1 sig h2 p length(x) length(y) lillietest(x) lillietest(y)];
            medianErrorOrientation(i) = median(x);
        end
    end
end

%% Generate Box Plots

distanceLabel = {'5','10','15','20','25','30','35','40'};
figure(9)
boxplot(abs(errorRoomAVGInv3'));
set(gca,'xticklabel',distanceLabel)
title('Fig 9 Absolute error w/ Distance')
ylabel('Error (cm)')
xlabel('Distance (cm)')
saveas(gcf,'effectDistance.png')

figure(10)
boxplot(100*abs(errorRoomAVGRelInv3'));
set(gca,'xticklabel',distanceLabel)
title('Fig 10 Relative error w/ Distance')
ylabel('Percent Error')
ylim([0 300])
xlabel('Distance (cm)')
saveas(gcf,'effectDistanceRelative.png')

angleLabel = {'90-100','100-110','110-120','120-130','130-140','140-150','150-160'};
figure(11)
boxplot(abs(errorAngle(:,2)),errorAngle(:,3))
title('Error with angle')
xlabel('Angle Range')
ylabel('Error (mm)')
ylim([0 20])
set(gca,'xticklabel',angleLabel)
saveas(gcf,'effectAngle.png')

figure(12)
boxplot(abs(100*errorAngleRel(:,2)),errorAngleRel(:,3))
title('Relative Error with angle')
xlabel('Angle Range')
ylabel('Relative Error (%)')
ylim([0 120])
set(gca,'xticklabel',angleLabel)
saveas(gcf,'effectAngleRelative.png')

coverLabel = {'Uncovered', 'Covered'};
figure(13)
boxplot(errorCovered(:,1),errorCovered(:,2))
title('Error effect of Obstruction, 8mm foam')
ylabel('Error (mm)')
set(gca,'xticklabel',coverLabel)
saveas(gcf,'effectObstruction.png')

jitterLabel = {'Stationary', 'Jitter'};
figure(14)
boxplot(errorJitter(:,1),errorJitter(:,2))
title('Error effect of Jitter')
ylabel('Error (mm)')
set(gca,'xticklabel',jitterLabel)
% ylim([0 100])
saveas(gcf,'effectJitter.png')

%% Power tests on obstruction and jitter
% Obstruction
uncovered = find(errorCovered(:,2)==0); % Bare wrist data indices
covered = find(errorCovered(:,2)==1); % Covered wrist data indices

% Grab the data
x = errorCovered(uncovered,1);
y = errorCovered(covered,1);
figure(15)
suptitle('Obstruction Histograms')
subplot(1,2,1)
hist(x)
subplot(1,2,2)
hist(y)
saveas(gcf,'HistogramObstruction.png')
% Power test
sprintf('Obstruction test')
[sig p] = powerTests(x,y);

% Jitter
jitter = find(errorJitter(:,2)==0); % Jitter data indices
stationary = find(errorJitter(:,2)==1); % Stationary data indices
% Grab data
x = errorJitter(stationary,1);
y = errorJitter(jitter,1);
figure(16)
suptitle('Jitter Histograms')
subplot(1,2,1)
hist(x)
subplot(1,2,2)
hist(y)
sprintf('Jitter test')
[sig p] = powerTests(x,y);
saveas(gcf,'HistogramJitter.png')


%% Calculate Overall error mean/median
overallErrorAbsMean = mean(mean(abs(errorRoomAVGInv3)));
overallErrorAbsMedian = median(median(abs(errorRoomAVGInv3)));

overallErrorAbsMeanRel = mean(mean(abs(errorRoomAVGRelInv3)));
overallErrorAbsMedianRel = median(median(abs(errorRoomAVGRelInv3)));

sprintf('System Median error is %.2f cm. Relative median error %.2f%%',overallErrorAbsMedian,100*overallErrorAbsMedianRel)
sprintf('System Mean error is %.2f cm. Relative mean error %.2f%%',overallErrorAbsMean,100*overallErrorAbsMeanRel)

sprintf('Median error (cm) by room is %.2f, %.2f, %.2f, %.2f, %.2f',medianErrorRooms(1),medianErrorRooms(2),medianErrorRooms(3),medianErrorRooms(4),medianErrorRooms(5))
sprintf('Median error (cm) by Orientation is %.2f,%.2f, %.2f, %.2f, %.2f, %.2f',medianErrorOrientation(1),medianErrorOrientation(2),medianErrorOrientation(3),medianErrorOrientation(4),medianErrorOrientation(5),medianErrorOrientation(6))

%% Show Error Distribution
figure(17)
histogram(abs(errorRoomAVGInv3))
title('Histogram on error')
xlabel('Error (cm)')
saveas(gcf,'HistogramError.png')

figure(18)
histogram(100*abs(errorRoomAVGRelInv3))
title('Histogram on relative error')
xlabel('Error (%)')
xlim([0 200])
saveas(gcf,'HistogramErrorRelative.png')

%% Functions
function [sig p] = powerTests(x,y)
    sprintf('Checking normality. Hypothesis test yields %i,%i',lillietest(x),lillietest(y))
    [h,sig,ci] = ttest2(x,y);
    if h==0
        sprintf('Fail to reject null in t-test with significance %.2f',sig)
    elseif h==1
        sprintf('Reject null in t-test with significance %.2f',sig)
    end
    [p,h] = ranksum(x,y);
    if h==0
        sprintf('Fail to reject null in Wilcoxon rank test with = %.2f',p)
    elseif h==1
        sprintf('Reject null in Wilcoxon rank test with = %.2f',p)
    end
end