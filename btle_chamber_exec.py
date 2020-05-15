#!/usr/bin/env python3
import sys
import os
import time
import gc
import threading
import btle_sniffer
from EMCenter_Controller import emcenter_ctrl

class BtleChamberExec():
    def __init__(self):
        super().__init__()
        self.stopExpireTime = 0    
        self.stopTimerRunning = False
        self.scanExpireTime = 0    
        self.scanTimerRunning = False
        self.scanAxis = ''
        self.t1 = None
        self.t2 = None

        self.btleSniffer = btle_sniffer.BtleSniffer(autoMode=True)
        self.emcenterCtrl = emcenter_ctrl.EMCenterController(remoteAddr='192.168.152.36', remotePort='61000')

    def run(self):
        self.btleSniffer.run()
    
    def stop(self):
        print("Stopping...")
        self.btleSniffer.kill()
        self.emcenterCtrl.kill()
    
    def updateMetadata(self, angle=0):
        self.btleSniffer.metaData.angle = str(angle)
        self.btleSniffer.metaData.setDefaults()
    
    def setStopTimer(self, stopExpireTime=0):
        if stopExpireTime > 0 and self.stopTimerRunning == False:
            self.stopExpireTime = stopExpireTime
            self.t1 = threading.Thread(target=self.stopTimerFunc)
            self.t1.start()
        else:
            print('Error, timer already running or invalid time given')
    
    def stopTimerFunc(self):
        if self.stopTimerRunning == False:
            self.stopTimerRunning = True
            time.sleep(self.stopExpireTime)
            self.stop()
            self.stopTimerRunning = False

    def setScanTimer(self, scanExpireTime=0, scanAxis='A'):
        if scanExpireTime > 0 and self.stopTimerRunning == False:
            self.scanExpireTime = scanExpireTime
            self.scanAxis = scanAxis
            self.t2 = threading.Thread(target=self.scanTimerFunc)
            self.t2.start()
        else:
            print('Error, timer already running or invalid time given')
    
    def scanTimerFunc(self):
        if self.scanTimerRunning == False:
            self.scanTimerRunning = True
            time.sleep(self.scanExpireTime)
            self.emcenterCtrl.startScan(self.scanAxis)
            
            counter = 0
            scanning = self.emcenterCtrl.isScanning(self.scanAxis)
            while scanning[1] == '1':
                time.sleep(10)
                print('Still scanning...')

                # set a time limit to avoid inf loop (2000s is plenty) 
                counter = counter + 1
                if counter > 200:
                    break
                
                # get latest scanning status
                scanning = self.emcenterCtrl.isScanning(self.scanAxis)
            
            # now stop the capture
            self.stop()

            self.scanTimerRunning = False

def main(argv):

    # Scripted loop to automate anechoic chamber collection 
    # Run 8 iterations on Mast from 0-360 in 45 deg increments
    pos = 0
    for i in range(10):
        print("Running test (" + str(i) + ") for angle = " + str(pos))

        btle = BtleChamberExec()

        if i<8:
            status = btle.emcenterCtrl.getStatus(update=True)
            if status[0] == btle.emcenterCtrl.OK and status[1] == 'OK':
                # Set axis movement limits
                btle.emcenterCtrl.setUpperLimit(btle.emcenterCtrl.mastAxis, limit=359.9)
                btle.emcenterCtrl.setUpperLimit(btle.emcenterCtrl.tableAxis, limit=150)
                btle.emcenterCtrl.setLowerLimit(btle.emcenterCtrl.mastAxis, limit=0)
                btle.emcenterCtrl.setLowerLimit(btle.emcenterCtrl.tableAxis, limit=-200)

                # Set nmumber of cycles (for scanning, 0=inf)
                btle.emcenterCtrl.setCycles(btle.emcenterCtrl.mastAxis, cycles=1)
                btle.emcenterCtrl.setCycles(btle.emcenterCtrl.tableAxis, cycles=1)

                # set positioner speed to 20%
                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.mastAxis, speed=20)
                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.tableAxis, speed=20)

                # set positioner acceleration to 1s 
                btle.emcenterCtrl.setAcceleration(btle.emcenterCtrl.mastAxis, accel=1)
                btle.emcenterCtrl.setAcceleration(btle.emcenterCtrl.mastAxis, accel=1)

                # move to the correct position
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.mastAxis, pos=pos)
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.tableAxis, pos=40)
                
                time.sleep(20)
                btle.setStopTimer(500)
                btle.btleSniffer.run()
            else:
                print('Positioner Error!')
                exit(-1)

            # update mast angle for next iteration
            pos = pos + 45

            # update metadata for next iteration
            btle.updateMetadata(angle=pos)
        elif i == 8:
            status = btle.emcenterCtrl.getStatus(update=True)
            if status[0] == btle.emcenterCtrl.OK and status[1] == 'OK':
                # Now run scan 1 - Mast Axis
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.mastAxis, pos=0)
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.tableAxis, pos=40)

                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.mastAxis,speed=2)
                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.tableAxis,speed=10)
                
                btle.updateMetadata(angle='H-Axis. 0 to 360. 360 to 0')
                
                # delay the start of the scan by setting a timer to trigger it
                btle.setScanTimer(20, scanAxis=btle.emcenterCtrl.mastAxis)
                btle.btleSniffer.run()
        elif i == 9:
            status = btle.emcenterCtrl.getStatus(update=True)
            if status[0] == btle.emcenterCtrl.OK and status[1] == 'OK':
                # Now run scan 2 - Table Axis
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.mastAxis, pos=0)
                btle.emcenterCtrl.seekPosition(btle.emcenterCtrl.tableAxis, pos=40)

                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.mastAxis,speed=2)
                btle.emcenterCtrl.setSpeed(btle.emcenterCtrl.tableAxis,speed=10)
                
                btle.updateMetadata(angle='V-Axis. 0 to 110. 110 to -240. -240 to 110')

                # delay the start of the scan by setting a timer to trigger it
                btle.setScanTimer(20, btle.emcenterCtrl.tableAxis)
                btle.btleSniffer.run()

    print('DONE WITH AUTOMATED BTLE TEST!')

    return 0

# callable from command line
if __name__ == "__main__":
    main(sys.argv[1:])