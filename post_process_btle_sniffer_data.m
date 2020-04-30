function [T, fig, s37, s38, s39] = post_process_btle_sniffer_data(filename)
% Post process a data file collected with the btle_sniffer.py script.  Plot
% data on a channel-by-channel basis.  Return values are:
%
%   T - Matlab table containing all data
%   fig - the figure handle containing plots
%   s37 - object containing stats for ch 37, index as 'min', 'max', etc.
%   s38 - object containing stats for ch 38, index as 'min', 'max', etc.
%   s39 - object containing stats for ch 39, index as 'min', 'max', etc.
%
    
% read csv data into table
T = readtable(filename, 'FileType', 'text');

% filter by BTLE channel
T_37=T(T.Var2 == 37,:);
T_38=T(T.Var2 == 38,:);
T_39=T(T.Var2 == 39,:);

% generate plots
fig = figure(1); 
subplot(3,1,1); 
plot(T_37.Var1, T_37.Var5); 
subplot(3,1,2); 
plot(T_38.Var1, T_38.Var5); 
subplot(3,1,3); 
plot(T_39.Var1, T_39.Var5);

s37 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(T_37.Var5), ...
                       max(T_37.Var5), ...
                       mean(T_37.Var5), ...
                       median(T_37.Var5), ...
                       mode(T_37.Var5), ...
                       std(T_37.Var5), ...
                       range(T_37.Var5)]);
disp('Ch 37 Stats')
disp(['min = ' int2str(s37('min'))])
disp(['max = ' int2str(s37('max'))])
disp(['mean = ' int2str(s37('mean'))])
disp(['median = ' int2str(s37('median'))])
disp(['mode = ' int2str(s37('mode'))])
disp(['std = ' int2str(s37('std'))])
disp(['range = ' int2str(s37('range'))])
fprintf('\n')
               
s38 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(T_38.Var5), ...
                       max(T_38.Var5), ...
                       mean(T_38.Var5), ...
                       median(T_38.Var5), ...
                       mode(T_38.Var5), ...
                       std(T_38.Var5), ...
                       range(T_38.Var5)]);
                   
disp('Ch 38 Stats')
disp(['min = ' int2str(s38('min'))])
disp(['max = ' int2str(s38('max'))])
disp(['mean = ' int2str(s38('mean'))])
disp(['median = ' int2str(s38('median'))])
disp(['mode = ' int2str(s38('mode'))])
disp(['std = ' int2str(s38('std'))])
disp(['range = ' int2str(s38('range'))])
fprintf('\n')

s39 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(T_39.Var5), ...
                       max(T_39.Var5), ...
                       mean(T_39.Var5), ...
                       median(T_39.Var5), ...
                       mode(T_39.Var5), ...
                       std(T_39.Var5), ...
                       range(T_39.Var5)]);
disp('Ch 39 Stats')
disp(['min = ' int2str(s39('min'))])
disp(['max = ' int2str(s39('max'))])
disp(['mean = ' int2str(s39('mean'))])
disp(['median = ' int2str(s39('median'))])
disp(['mode = ' int2str(s39('mode'))])
disp(['std = ' int2str(s39('std'))])
disp(['range = ' int2str(s39('range'))])
fprintf('\n')