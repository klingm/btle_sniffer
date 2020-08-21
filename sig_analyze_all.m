close all;
fileList = dir('*.csv');

num = length(fileList)

rssi = {};
Tv = {};
for i=1:num
    [metadata, btle, fig, s37, s38, s39] = post_process_btle_sniffer_data(fileList(i).name); 
    rssi(i) = {btle.rssi};
    rssi37(i) = {btle.rssiCh37};
    rssi38(i) = {btle.rssiCh38};
    rssi39(i) = {btle.rssiCh39};
    
    Tv(i) = {btle.time};
    Tv37(i) = {btle.timeCh37};
    Tv38(i) = {btle.timeCh38};
    Tv39(i) = {btle.timeCh39};
    ftitle = [metadata.device '-' metadata.txPower 'dBm -' metadata.range 'ft -' metadata.angle];
    fh = gcf;
    fh.WindowState = 'maximized';
    pause(1);
    axh=get(gcf,'Children');
    ch = 37;
    for a=1:numel(axh)
        set(axh(a), 'TitleFontSizeMultiplier', 0.9)
        titlea = [ftitle '- Ch ' num2str(ch)];
        ch = ch + 1;
        titleh=get(axh(a),'title');
        set(titleh,'String', titlea);
        
    end
    
    fname = strrep(ftitle, '/', '');
    fname = strrep(fname, '. ', '-');
    fname = strrep(fname, '.', '');
    saveas(gcf,[fname '.jpg']);
    close(fig);
    
    fig = figure();
    fig.WindowState = 'maximized';
    pause(1);
    subplot(3,1,1);
    histogram(btle.rssiCh37, 'Normalization', 'pdf');
    titlea = [ftitle '- Ch ' num2str(37) '-Dist'];
    title(titlea);
    subplot(3,1,2);
    histogram(btle.rssiCh38, 'Normalization', 'pdf');
    titlea = [ftitle '- Ch ' num2str(38) '-Dist'];
    title(titlea);
    subplot(3,1,3);
    histogram(btle.rssiCh39, 'Normalization', 'pdf');
    titlea = [ftitle '- Ch ' num2str(39) '-Dist'];
    title(titlea);
    saveas(gcf,[fname '-Dist.jpg']);
    close(fig);
    
    %start = fix(length(btle.rssiCh37)/2);
    %signalAnalyzer(rssi37{i}(start:start+100), 'TimeValue', Tv37{i}(start:start+100));
    %signalAnalyzer(rssi38{i}(start:start+100), 'TimeValue', Tv38{i}(start:start+100));
    %signalAnalyzer(rssi39{i}(start:start+100), 'TimeValue', Tv39{i}(start:start+100));
    %signalAnalyzer(rssi{i}, 'TimeValue', Tv{i});
    %signalAnalyzer(rssi37{i}, 'TimeValue', Tv37{i});
    %signalAnalyzer(rssi38{i}, 'TimeValue', Tv38{i});
    %signalAnalyzer(rssi39{i}, 'TimeValue', Tv39{i});
    %break
end