function [metadata, btle, fig, s37, s38, s39] = post_process_btle_sniffer_data(filename)
% Post process a data file collected with the btle_sniffer.py script.  Plot
% data on a channel-by-channel basis.  Return values are:
%
%   T - Matlab table containing all data
%   fig - the figure handle containing plots
%   s37 - object containing stats for ch 37, index as 'min', 'max', etc.
%   s38 - object containing stats for ch 38, index as 'min', 'max', etc.
%   s39 - object containing stats for ch 39, index as 'min', 'max', etc.
%

fid = fopen(filename,'r');

% read all line from the file
tline = fgetl(fid);
btleCnt = 1;
while ischar(tline)
    fields = split(tline,',');
    if strcmp(fields{2},'Environment')
        % This is an info field containing metadata
        metadata.timestamp = fields{1};
        metadata.env = fields{3};
    elseif strcmp(fields{2},'Device')
        % This is an info field containing metadata
        metadata.device = fields{3};
    elseif strcmp(fields{2},'Range')
        % This is an info field containing metadata
        metadata.range = fields{3};
    elseif strcmp(fields{2},'Angle')
        % This is an info field containing metadata
        metadata.angle = fields{3};
    elseif strcmp(fields{2},'TxPower')
        % This is an info field containing metadata
        metadata.txPower = fields{3};
    elseif strcmp(fields{2},'GPS')
        % This is an info field containing metadata
        metadata.gps = fields{3};
    elseif strcmp(fields{2},'Bluetooth')
        % extract data from cell array, handle both ver 1 and ver 2.  Ver 1 has
        % 7 total fields and does not include the device name plus the TX TxPower
        % is the anticipated power not the actual power.  Ver 2 has 8 fields and 
        % contains the device name as well as the actual TX Power as reporred in
        % each BLE packet.
        if length(fields) == 7
            btle.timestamp{btleCnt} = fields{1};
            btle.addr{btleCnt} = fields{3};
            btle.rssi(btleCnt) = str2double(fields{4});
            btle.txPower(btleCnt) = str2double(fields{5});
            btle.time(btleCnt) = str2double(fields{6});
            btle.chan(btleCnt) = str2double(fields{7});
            btle.deviceName{btleCnt} = 'NA';
            btleCnt = btleCnt + 1;
        elseif length(fields) == 8
            btle.timestamp{btleCnt} = fields{1};
            btle.addr{btleCnt} = fields{3};
            btle.rssi(btleCnt) = str2double(fields{4});
            btle.deviceName{btleCnt} = fields{5};
            btle.time(btleCnt) = str2double(fields{6});
            btle.txPower(btleCnt) = str2double(fields{7});
            btle.chan(btleCnt) = str2double(fields{8});
            btleCnt = btleCnt + 1;
            
        else
            disp('Error, incorrect numer of fields in btle record!')
        end
    end
    tline = fgetl(fid);
end

fclose(fid);

% filter by BTLE channel
btle.rssiCh37=btle.rssi(btle.chan == 37);
btle.rssiCh38=btle.rssi(btle.chan == 38);
btle.rssiCh39=btle.rssi(btle.chan == 39);
btle.timeCh37=btle.time(btle.chan == 37);
btle.timeCh38=btle.time(btle.chan == 38);
btle.timeCh39=btle.time(btle.chan == 39);

% average each rssi in the 3-channel group
for i=1:length(btle.rssiCh37)
    if i <= length(btle.rssiCh38) && i <= length(btle.rssiCh39)
        btle.avgRssi(i) = (btle.rssiCh37(i) + btle.rssiCh38(i) + btle.rssiCh39(i))/3;
        btle.avgTime(i) = (btle.timeCh37(i))/3;
    end
end

% generate plots
fig = figure; 
subplot(3,1,1); 
plot(btle.rssiCh37); 
subplot(3,1,2); 
plot(btle.rssiCh38); 
subplot(3,1,3); 
plot(btle.rssiCh39);

s37 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(btle.rssiCh37), ...
                       max(btle.rssiCh37), ...
                       mean(btle.rssiCh37), ...
                       median(btle.rssiCh37), ...
                       mode(btle.rssiCh37), ...
                       std(btle.rssiCh37), ...
                       range(btle.rssiCh37)]);
disp('Ch 37 Stats')
disp(['min = ' num2str(s37('min'))])
disp(['max = ' num2str(s37('max'))])
disp(['mean = ' num2str(s37('mean'))])
disp(['median = ' num2str(s37('median'))])
disp(['mode = ' num2str(s37('mode'))])
disp(['std = ' num2str(s37('std'))])
disp(['range = ' num2str(s37('range'))])
fprintf('\n')
               
s38 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(btle.rssiCh38), ...
                       max(btle.rssiCh38), ...
                       mean(btle.rssiCh38), ...
                       median(btle.rssiCh38), ...
                       mode(btle.rssiCh38), ...
                       std(btle.rssiCh38), ...
                       range(btle.rssiCh38)]);
                   
disp('Ch 38 Stats')
disp(['min = ' num2str(s38('min'))])
disp(['max = ' num2str(s38('max'))])
disp(['mean = ' num2str(s38('mean'))])
disp(['median = ' num2str(s38('median'))])
disp(['mode = ' num2str(s38('mode'))])
disp(['std = ' num2str(s38('std'))])
disp(['range = ' num2str(s38('range'))])
fprintf('\n')

s39 = containers.Map({'min','max','mean','median','mode','std','range'}, ...
                       [min(btle.rssiCh39), ...
                       max(btle.rssiCh39), ...
                       mean(btle.rssiCh39), ...
                       median(btle.rssiCh39), ...
                       mode(btle.rssiCh39), ...
                       std(btle.rssiCh39), ...
                       range(btle.rssiCh39)]);
disp('Ch 39 Stats')
disp(['min = ' num2str(s39('min'))])
disp(['max = ' num2str(s39('max'))])
disp(['mean = ' num2str(s39('mean'))])
disp(['median = ' num2str(s39('median'))])
disp(['mode = ' num2str(s39('mode'))])
disp(['std = ' num2str(s39('std'))])
disp(['range = ' num2str(s39('range'))])
fprintf('\n')