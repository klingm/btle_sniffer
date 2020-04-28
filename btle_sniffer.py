#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as pyplot
import matplotlib.animation as animation
from matplotlib import style

import sys
import os
import time
import math
import getopt
import logging
import subprocess
import threading
import readline

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import (NavigationToolbar2Tk as NavigationToolbar)

matplotlib.use('TkAgg')

class BtleSniffer:
    # Constructor
    def __init__(self, _filter = ""):
        print("init")
        self.mainProcess = None
        self.wiresharkProcess = None
        self.tsharkProcess = [None, None]
        self.t = [None,None,None]

        self.fig = None
        self.ax1 = None
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
    
    # wait for main process to exit, if it is running
    def wait(self):
        if self.mainProcess is not None:
            self.mainProcess.join()
        else:
            print("main process not running!")

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

            if(xMax > 19):
                xMax = 19
            if(yMax > 8):
                yMax = 8

            # generate the figure
            self.fig = pyplot.figure(figsize=(xMax, yMax))
            self.ax1 = self.fig.add_subplot(1,1,1)
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel("RSSI (dB)")
            self.ax1.set_title("All BTLE Devices")
            self.fig.tight_layout()

            #self.ani = animation.FuncAnimation(self.fig, self.animatePlot, interval=1000)
            #pyplot.show(block=False)

    def animatePlot(self, i):
        # open the file containing data to plot and read.  Data is stored as 
        # CSV so split before using.
        lines = open('tshark.out','r').readlines()
        xs = []
        ys = []

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
                    # count the number of RSSI samples for this address
                    if data[BTLE_ADV_ADDR] in rssiCounts:
                        rssiCounts[data[BTLE_ADV_ADDR]] = rssiCounts[data[BTLE_ADV_ADDR]] + 1 
                    else:
                        rssiCounts[data[BTLE_ADV_ADDR]] = 1

                    if (data[BTLE_ADV_ADDR].lower() == self.filter.lower()) or self.filter == "":
                        xs.append(float(data[BTLE_TIME]))
                        ys.append(float(data[BTLE_RSSI]))
                else:
                    print("ERROR: unexpected data length ", len(data), " ", num)

        # update the plot
        if pyplot.fignum_exists(self.fig.number) and not self.pausePlot:
            self.ax1.clear()
            self.ax1.set_title(title)
            self.ax1.set_xlabel("Time (s)")
            self.ax1.set_ylabel("RSSI (dB)")
            self.ax1.plot(xs, ys, linewidth=1, marker=self.plotMarker)
        
        # update the class var that holds all RSSI counters
        self.rssiCounts = rssiCounts

    def getAddrList(self):
        addrs = list()
        for k, v in self.rssiCounts.items():
            if k != "":
                if k == "*":
                    addrs.append(str(k) + ' ' + str(v))
                elif (self.hideInfrequent and int(v) > self.infrequentThresh) or (not self.hideInfrequent):
                    addrs.append(str(k) + ' ' + str(v))

        return sorted(addrs)

    def commandPrompt(self):
        print("Starting command prompt...\n")

        while self.runFlag == True:
            sg.theme('Reddit')	# Add a touch of color
            # All the stuff inside your window.
            figX, figY, figW, figH = self.fig.bbox.bounds
            layout = [  [sg.Canvas(size=(figW, figH), key="canvas")], 
                        [sg.Text('RSSI Filter', font=("Courier", 10))],
                        [sg.Text('Select advertising addr: ', font=("Courier", 10)), 
                         sg.Combo(self.getAddrList(), auto_size_text=True, key="-ComboList-", font=("Courier",10))],
                        [sg.Checkbox("Don't show infrequent addrs", default=True, font=("Courier", 10), key="-Infrequent-")],
                        [sg.Checkbox("Show data points", default=False, font=("Courier", 10), key="-ShowDataPoints-")],
                        [sg.Checkbox("Pause plot updates", default=False, font=("Courier", 10), key="-PausePlot-")],
                        [sg.Button('OK'), sg.Button('Refresh Addr List'), sg.Button('Clear Data')] ]

            # Create the Window
            window = sg.Window('RSSI Filter', layout, resizable=True, finalize=True)
            self.window = window

            # add the plot to the window
            self.figCanvasAgg = self.masterPlotWindow(window['canvas'].TKCanvas, self.fig)

            # Event Loop to process "events" and get the "values" of the inputs
            done = False
            while not done:
                event, values = window.read(timeout=1000, timeout_key="-Timeout-")
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
                    if self.runFlag == False:
                        print("runFlag set to False, exiting...")
                        done = True
                    else:
                        self.animatePlot(0)
                        self.figCanvasAgg = self.masterPlotWindow(window['canvas'].TKCanvas, self.fig, update=True)
                else:
                    print("Unknown event: ", event)

            window.close()

        print("Exiting commandPrompt")

    # Spawn threads for capturing btle RSSI and other info
    def run(self):
        print("run")
        self.runFlag = True
        self.mainProcess = threading.Thread(target=self.spawnThreads)
        self.mainProcess.start()

        time.sleep(12)
        self.plotRSSI()
        self.commandPrompt() 

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
        if self.ani != None:
            if self.ani.event_source != None:
                self.ani.event_source.stop()

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
                "-e", "nordic_ble.rssi"]
                

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


def usage():
    print("\nDescription: this program uses the nRF52-DK with installed Bluetooth LE Sniffer firmware to capture and visualize live RSSI data.\n")
    print("\nUsage:\n")
    print(" ",__file__, " [-vh] [-f filter_addr]\n")
    print("     -v: verbose\n")
    print("     -h: help\n")
    print("     -f filter_addr: display only bluetooth data with specified advertising address.")
    print("     The filter address can be adjusted live by enter 'filter' into the command prompt")
    print("\n")

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

if __name__ == "__main__":
    main(sys.argv[1:])