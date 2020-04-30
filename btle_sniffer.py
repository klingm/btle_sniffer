#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as pyplot
import matplotlib.animation as animation
from matplotlib import style

import sys
import os
import time
import math
import statistics
import getopt
import logging
import subprocess
import threading
import readline

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import (NavigationToolbar2Tk as NavigationToolbar)

from datetime import datetime
import time

matplotlib.use('TkAgg')

# Class that implements all BTLE sniffer functionality.  Create and update GUI,
# send commands to RaspPi, receive data stream and process it.
class BtleSniffer:
    # Constructor, init all class vars and call init routine for the PiSniffer
    def __init__(self, _filter = ""):
        print("init")
        self.mainProcess = None
        self.wiresharkProcess = None
        self.tsharkProcess = [None, None]
        self.t = [None,None,None]

        self.fig = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ani = None
        self.window = None
        self.figCanvasAgg = None
        self.pausePlot = False

        self.filter = _filter
        self.runFlag = False

        self.advAddrs = set()
        self.rssiCounts = dict({'*': '*'})
        self.plotMarker = ""
        self.hideInfrequent = True
        self.infrequentThresh = 10

        # stats
        self._min = [0,0,0]
        self._max = [0,0,0]
        self._mean = [0,0,0]
        self._median = [0,0,0]
        self._mode = [0,0,0]
        self._std = [0,0,0]
        self._range = [0,0,0]

        # call init function for RaspPi
        self.initPiSniffer()
    
    # Generic routine to send a command to the RaspPi.  Only for use with 
    # commands that return and don'thang until killed.  This is used to send 
    # init commands.  Command is specified in _cmdStr arg.
    def sendPiSnifferCmd(self, _cmdStr):
        # ssh command to stream a pacapng file over ssh from the rasp pi to the 
        # local machine and then use tshark to dissect the packets
        cmd =  ["ssh", "ubuntu@pi_sniffer", _cmdStr]

        # open the process and save the process object as a class member variable
        process = subprocess.Popen(cmd, 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)

        # monitor the process and wait for exit
        while True:
            output = process.stdout.readline()

            # wait for process to exit
            return_code = process.poll()
            if return_code is not None:
                print(output)
                print('RETURN CODE', return_code)
                break
    
    # Initialization routine for setting up the RaspPi.  This turns off 
    # bluetooth and shuts off WiFi to allow for clean data collections.
    def initPiSniffer(self):
        self.sendPiSnifferCmd("sudo systemctl stop bluetooth")
        self.sendPiSnifferCmd("sudo ifconfig wlan0 down")

    # wait for main process to exit, if it is running
    def wait(self):
        if self.mainProcess is not None:
            self.mainProcess.join()
        else:
            print("main process not running!")

    # Creates the master window used for holding the plot and the UI controls.
    def masterPlotWindow(self, canvas, figure, update=False):
        if not update:
            figureCanvasAgg = FigureCanvasTkAgg(figure, canvas)
            #toolbar = NavigationToolbar(figureCanvasAgg, canvas)
            #toolbar.update()
            #figureCanvasAgg.get_tk_widget().pack(side='top', fill='both', expand=1)
        else:
            figureCanvasAgg = self.figCanvasAgg
        
        figureCanvasAgg.draw()
        figureCanvasAgg.get_tk_widget().pack(side='top', fill='both', expand=1)

        return figureCanvasAgg

    # create the plot for RSSI using matplotlib.  The generated figure will be
    # embedded into another window using the TkAgg backend.
    def plotRSSI(self):
        if self.runFlag == True:
            # set up plot
            style.use('ggplot')

            # determine max size to make the figure
            window = pyplot.get_current_fig_manager().window
            yMax = window.winfo_screenheight()/100
            xMax = window.winfo_screenwidth()/100

            if(xMax > 18.0):
                xMax = 18.0
            if(yMax > 7.5):
                yMax = 7.5

            # generate the figure
            self.fig = pyplot.figure(figsize=(xMax, yMax))
            self.ax1 = self.fig.add_subplot(3,1,1)
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel("RSSI (dB)")
            self.ax1.set_title("Ch 37 All BTLE Devices")

            self.ax2 = self.fig.add_subplot(3,1,2)
            self.ax2.set_xlabel("Time (s)")
            self.ax2.set_ylabel("RSSI (dB)")
            self.ax2.set_title("Ch 38 All BTLE Devices")
            
            self.ax3 = self.fig.add_subplot(3,1,3)
            self.ax3.set_xlabel("Time (s)")
            self.ax3.set_ylabel("RSSI (dB)")
            self.ax3.set_title("Ch 39 All BTLE Devices")
            self.fig.tight_layout()

    # This function must be called periodically to read new data and plot it.
    def animatePlot(self, i, window):
        # open the file containing data to plot and read.  Data is stored as 
        # CSV so split before using.
        lines = open('tshark.out','r').readlines()
        xs1 = []
        ys1 = []
        xs2 = []
        ys2 = []
        xs3 = []
        ys3 = []

        # field indexes for BLTE data
        BTLE_TIME = 0
        BTLE_CH = 1
        BTLE_SCAN_ADDR = 2
        BTLE_ADV_ADDR = 3
        BTLE_RSSI = 4

        # Plot title
        title = ""
        if self.filter == "":
            title = "All BTLE Devices"
        else:
            title = self.filter

        # loop over all data read
        num = 0
        rssiCounts = dict({"*":"*"})
        t0 = 0
        for line in lines:
            line = line.rstrip()
            # FIXME - skip the first line, it is garbage
            num = num + 1
            if num == 1:
                continue
            if num == len(lines):
                continue

            if len(line) > 1:
                data = line.split(',')
                if len(data) == 5:
                    # convert timestamp to seconds since start of capture
                    s = data[BTLE_TIME]
                    d = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
                    t = time.mktime(d.timetuple())
                    
                    # get the first timestamp to use in calculating the display
                    # time (seconds since start of capture)
                    if num == 2:
                        t0 = t

                    # count the number of RSSI samples for this address
                    if data[BTLE_ADV_ADDR] in rssiCounts:
                        rssiCounts[data[BTLE_ADV_ADDR]] = rssiCounts[data[BTLE_ADV_ADDR]] + 1 
                    else:
                        rssiCounts[data[BTLE_ADV_ADDR]] = 1

                    # check if this address is the selected one (or none means show all)
                    if (data[BTLE_ADV_ADDR].lower() == self.filter.lower()) or self.filter == "":
                        # separate the data by channel (37, 38 or 39)
                        if data[BTLE_CH] == "37":
                            xs1.append(float(t-t0))
                            ys1.append(float(data[BTLE_RSSI]))
                        if data[BTLE_CH] == "38":
                            xs2.append(float(t-t0))
                            ys2.append(float(data[BTLE_RSSI]))
                        if data[BTLE_CH] == "39":
                            xs3.append(float(t-t0))
                            ys3.append(float(data[BTLE_RSSI]))

                else:
                    print("ERROR: unexpected data length ", len(data), " ", num)

        # update the plot (3 subplots)
        if pyplot.fignum_exists(self.fig.number) and not self.pausePlot:
            self.ax1.clear()
            self.ax1.set_title("Ch 37 " + title)
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel("RSSI (dB)")
            self.ax1.plot(xs1, ys1, linewidth=1, marker=self.plotMarker)
            self.ax2.clear()
            self.ax2.set_title("Ch 38 " + title)
            self.ax2.set_xlabel("Time (s)")
            self.ax2.set_ylabel("RSSI (dB)")
            self.ax2.plot(xs2, ys2, linewidth=1, marker=self.plotMarker)
            self.ax3.clear()
            self.ax3.set_title("Ch 39 " + title)
            self.ax3.set_xlabel("Time (s)")
            self.ax3.set_ylabel("RSSI (dB)")
            self.ax3.plot(xs3, ys3, linewidth=1, marker=self.plotMarker)

            # update the stats panel on the window using new data
            self.updateStats(window, ys1,ys2,ys3)
        
        # update the class var that holds all RSSI counters
        self.rssiCounts = rssiCounts

    # calculate new stats and then post them to the screen widgets for display
    def updateStats(self, window, rssi1, rssi2, rssi3):
        if not rssi1 or not rssi2 or not rssi3:
            print("RSSI not received yet!")
            return

        self._min1 = min(rssi1) 
        self._min2 = min(rssi2) 
        self._min3 = min(rssi3) 

        self._max1 = max(rssi1) 
        self._max2 = max(rssi2) 
        self._max3 = max(rssi3) 

        self._mean1 = statistics.mean(rssi1) 
        self._mean2 = statistics.mean(rssi2) 
        self._mean3 = statistics.mean(rssi3) 

        self._median1 = statistics.median(rssi1) 
        self._median2 = statistics.median(rssi2) 
        self._median3 = statistics.median(rssi3) 

        self._mode1 = (max(set(rssi1), key=rssi1.count)) 
        self._mode2 = (max(set(rssi2), key=rssi2.count)) 
        self._mode3 = (max(set(rssi3), key=rssi3.count)) 

        self._std1 = statistics.stdev(rssi1) 
        self._std2 = statistics.stdev(rssi2) 
        self._std3 = statistics.stdev(rssi3) 

        self._range1 = self._max1 - self._min1 
        self._range2 = self._max2 - self._min2 
        self._range3 = self._max3 - self._min3 

        window["-Min1-"].update(str(self._min1))
        window["-Min2-"].update(str(self._min2))
        window["-Min3-"].update(str(self._min3))

        window["-Max1-"].update(str(self._max1))
        window["-Max2-"].update(str(self._max2))
        window["-Max3-"].update(str(self._max3))

        window["-Mean1-"].update('{:3.6f}'.format(self._mean1))
        window["-Mean2-"].update('{:3.6f}'.format(self._mean2))
        window["-Mean3-"].update('{:3.6f}'.format(self._mean3))

        window["-Median1-"].update(str(self._median1))
        window["-Median2-"].update(str(self._median2))
        window["-Median3-"].update(str(self._median3))

        window["-Mode1-"].update(str(self._mode1))
        window["-Mode2-"].update(str(self._mode2))
        window["-Mode3-"].update(str(self._mode3))

        window["-Std1-"].update('{:3.6f}'.format(self._std1))
        window["-Std2-"].update('{:3.6f}'.format(self._std2))
        window["-Std3-"].update('{:3.6f}'.format(self._std3))

        window["-Rng1-"].update(str(self._range1))
        window["-Rng2-"].update(str(self._range2))
        window["-Rng3-"].update(str(self._range3))

    # Create a list of addresses plus the associated RSSI count on each for 
    # display in the UI ComboBox.  If the hideInfrequent flag is set then don't
    # add those to the list.
    def getAddrList(self):
        addrs = list()
        for k, v in self.rssiCounts.items():
            if k != "":
                if k == "*":
                    addrs.append(str(k) + ' ' + str(v))
                elif (self.hideInfrequent and int(v) > self.infrequentThresh) or (not self.hideInfrequent):
                    addrs.append(str(k) + ' ' + str(v))

        return sorted(addrs)

    # This routine runs the loop that reads data from the UI window and then 
    # performs the requested actions.
    def mainUiLoop(self):
        print("Starting command prompt...\n")

        while self.runFlag == True:
            # set the window theme
            sg.theme('Reddit')	# Add a touch of color
            
            # Get the figure dimensions for use in creating the GUI layout
            figX, figY, figW, figH = self.fig.bbox.bounds

            # The UI widgets below the plot are arranged into two columns, col1 
            # contains the UI controls and col2 contains the stats that are updated live.
            col1 = [ [sg.Text('RSSI Filter', font=("Courier", 10)), sg.Text('')],
                        [sg.Text('Select advertising addr: ', font=("Courier", 10)), 
                         sg.Combo(self.getAddrList(), auto_size_text=True, key="-ComboList-", font=("Courier",10))],
                        [sg.Checkbox("Don't show infrequent addrs", default=True, font=("Courier", 10), key="-Infrequent-")],
                        [sg.Checkbox("Show data points", default=False, font=("Courier", 10), key="-ShowDataPoints-")],
                        [sg.Checkbox("Pause plot updates", default=False, font=("Courier", 10), key="-PausePlot-")],
                        [sg.Button('OK'), sg.Button('Refresh Addr List')] ]
            
            col2 = [ [sg.Text('   Stats ', size=(10,1), font=("Courier",10)), sg.Text('Ch 37', size=(10,1), font=("Courier",10)), sg.Text('Ch 38', size=(10,1), font=("Courier",10)), sg.Text('Ch 39', size=(10,1), font=("Courier",10))],
                    [sg.Text('    Min   ', size=(10,1), font=("Courier",10)), sg.Text(str(self._min[0]), key="-Min1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._min[1]), key="-Min2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._min[2]), key="-Min3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Max   ', size=(10,1), font=("Courier",10)), sg.Text(str(self._max[0]), key="-Max1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._max[1]), key="-Max2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._max[2]), key="-Max3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Mean  ', size=(10,1), font=("Courier",10)), sg.Text(str(self._mean[0]), key="-Mean1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._mean[1]), key="-Mean2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._mean[2]), key="-Mean3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Median', size=(10,1), font=("Courier",10)), sg.Text(str(self._median[0]), key="-Median1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._median[1]), key="-Median2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._median[2]), key="-Median3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Mode  ', size=(10,1), font=("Courier",10)), sg.Text(str(self._mode[0]), key="-Mode1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._mode[1]), key="-Mode2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._mode[2]), key="-Mode3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Std   ', size=(10,1), font=("Courier",10)), sg.Text(str(self._std[0]), key="-Std1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._std[1]), key="-Std2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._std[2]), key="-Std3-", size=(10,1), font=("Courier",10))],
                    [sg.Text('    Rng   ', size=(10,1), font=("Courier",10)), sg.Text(str(self._range[0]), key="-Rng1-", size=(10,1), font=("Courier",10)), sg.Text(str(self._range[1]), key="-Rng2-", size=(10,1), font=("Courier",10)), sg.Text(str(self._range[2]), key="-Rng3-", size=(10,1), font=("Courier",10))]
                  ]

            layout = [  [sg.Canvas(size=(figW, figH), key="canvas")], 
                        [sg.Column(col1), sg.Column(col2)]]
            
            # Create the Window
            window = sg.Window('RSSI Filter', layout, resizable=True, finalize=True)
            self.window = window

            # add the plot to the window
            self.figCanvasAgg = self.masterPlotWindow(window['canvas'].TKCanvas, self.fig)

            # Event Loop to process "events" and get the "values" of the inputs
            done = False
            while not done:
                # wait for user action, or timeout.  On timeout update the window.
                event, values = window.read(timeout=500, timeout_key="-Timeout-")

                # Exit - user clicked "x" in upper right corner
                # Refresh Addr List - user clicked refresh button, so update the combobox
                # OK - update display based on user input
                # Timeout - allows for periodic screen updates/plot animation, or 
                #           exiting when wireshark is killed
                if event in (None, "Exit"):
                    print("Exiting window")
                    done = True
                elif event in (None, 'Refresh Addr List'):
                    print("Refreshing combo box list")
                    addrs = self.getAddrList()
                    window["-ComboList-"].Update(values=addrs, font=("Courier", 10))
                    window["-ComboList-"].set_size((len(max(addrs, key=len)), None))
                    window.Finalize()
                elif event in (None, 'OK'):
                    # get the value chosen to filter on
                    print('Filtering ', values["-ComboList-"])
                    v = values["-ComboList-"].split(" ")
                    if len(v) == 2:
                        if v[0] == "*":
                            v[0] = ""
                        self.filter = v[0]
                    else:
                        print("Unexpected value length: ", len(v))
                    
                    # check whether infrequent adv addrs should be shown in the 
                    # combo box list
                    self.hideInfrequent = values["-Infrequent-"]

                    # get the other plot options
                    if values["-ShowDataPoints-"] == True:
                        self.plotMarker = "."
                    else:
                        self.plotMarker = ""

                    self.pausePlot = values["-PausePlot-"]

                elif event in (None, "-Timeout-"):
                    # check if the exit flag was set, if so exit this loop and quit.  
                    # Otherwise, update the screen.
                    if self.runFlag == False:
                        print("runFlag set to False, exiting...")
                        done = True
                    else:
                        self.animatePlot(0, window)
                        self.figCanvasAgg = self.masterPlotWindow(window['canvas'].TKCanvas, self.fig, update=True)
                else:
                    print("Unknown event: ", event)

            window.close()

        print("Exiting mainUiLoop")

    # Spawn threads for capturing btle RSSI and other info
    def run(self):
        print("run")
        self.runFlag = True
        self.mainProcess = threading.Thread(target=self.spawnThreads)
        self.mainProcess.start()

        time.sleep(12)
        self.plotRSSI()
        self.mainUiLoop() 

    # spawn all threads, then wait for wireshark thread to exit and set the 
    # runFlag to false to cause other threads to quit.
    def spawnThreads(self):
        print("spawnThreads")

        # spawn wireshark
        self.t[0] = threading.Thread(target=self.runWireshark)
        self.t[0].start()

        # Give wireshark time to open, there is no other direct way to do this, 
        # so use sleep. Then spawn tshark that runs on the local machine.
        time.sleep(10)      
        self.t[1] = threading.Thread(target=self.runTshark)
        self.t[1].start()

        # wait for wireshark to exit, then send SIGTERM to tshark
        self.t[0].join()

        # terminate other subprocesses and wait for them to finish
        self.tsharkProcess[0].terminate()
        self.tsharkProcess[1].terminate()
        self.t[1].join()

        self.runFlag = False

    # Remotely run wireshark on the sniffer host, start capturing immediately on
    # the sniffer interface, and redirect its output to a file for reading.  This
    # is all a workaround for the fact that the Nordic Semi Btle Sniffer does not
    # work with tshark and requires wireshark with the Nodic Semi toolbar plugin.
    # Nordic Semi plans to support tshark in a future release but there is no date
    # for that yet.
    def runWireshark(self):
        # ssh command to stream a pacapng file over ssh from the rasp pi to the 
        # local machine and then use tshark to dissect the packets
        cmd =  ["ssh", "-X", "ubuntu@pi_sniffer", 
                "rm -f /home/ubuntu/nRF52/rb/rb.pcapng; touch /home/ubuntu/nRF52/rb/rb.pcapng; wireshark", 
                "-i /dev/ttyACM0", "-k", "-w /home/ubuntu/nRF52/rb/rb.pcapng"]

        # open the process and save the process object as a class member variable
        process = subprocess.Popen(cmd, 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        self.wiresharkProcess = process

        # monitor the process and wait for exit
        while True:
            # wait for process to exit
            return_code = process.poll()
            if return_code is not None:
                print('RETURN CODE', return_code)
                break
    
    # Spawn system processes to grab wireshark data from the remote sniffer host.
    # SSH is used to run the tail command to stream bytes from the capture file.
    # The output of this process is redirected to a pipe and then written to the 
    # input of a local instance of tshark running with stdin as its input vector.
    # The tshark process stdout is redirected to the file tshark.out.
    def runTshark(self):

        cmd1 =  ["ssh", "ubuntu@pi_sniffer", "tail", "-c +1", 
                 "-f /home/ubuntu/nRF52/rb/rb.pcapng"]

        cmd2 = ["tshark", "-r", "-", "-T", "fields", "-E", "separator=,", 
                "-e", "_ws.col.Time", "-e", "nordic_ble.channel", 
                "-e", "btle.scanning_address", "-e", "btle.advertising_address", 
                "-e", "nordic_ble.rssi", "-t", "ad"]
                

        # open the process and save the process object as a class member variable
        proc1 = subprocess.Popen(cmd1, 
                           stdout=subprocess.PIPE,
                           universal_newlines=False)
        self.tsharkProcess[0] = proc1


        f = open("tshark.out", "w")
        proc2 = subprocess.Popen(cmd2, 
                           stdin=subprocess.PIPE,
                           stdout=f,
                           universal_newlines=False)
        self.tsharkProcess[1] = proc2

        # monitor the process and wait for exit
        ret1 = None
        ret2 = None
        while True:
            if ret1 is None:
                binPcap = proc1.stdout.read(256)
                ret1 = proc1.poll()
            else:
                binPcap = None

            if ret2 is None:
                if binPcap is not None:
                    proc2.stdin.write(binPcap)
                ret2 = proc2.poll()
            
            # wait for proc1  and proc2 to exit
            if (ret1 is not None) and (ret2 is not None):
                print('RETURN CODE ', ret1, ', ', ret2)
                break

# print usage info
def usage():
    print("\nDescription: this program uses the nRF52-DK with installed Bluetooth LE Sniffer firmware to capture and visualize live RSSI data.\n")
    print("\nUsage:\n")
    print(" ",__file__, " [-vh] [-f filter_addr]\n")
    print("     -v: verbose\n")
    print("     -h: help\n")
    print("     -f filter_addr: display only bluetooth data with specified advertising address.")
    print("     The filter address can be adjusted live by enter 'filter' into the command prompt")
    print("\n")

# main function for command line entry point
def main(argv):
    _filter = ""

    # grab command line args
    try:
        opts, args = getopt.getopt(argv,"vhf:",["filter="])
    except getopt.GetoptError:
        usage()
        return

    verbose = False
    for opt, arg in opts:
        if opt == '-h':
            usage()
            return
        elif opt in ("-f", "--filter"):
            _filter = arg
        elif opt == "-v":
            verbose = True

    sniffer = BtleSniffer(_filter)
    sniffer.run()
    sniffer.wait()

# callable from command line
if __name__ == "__main__":
    main(sys.argv[1:])