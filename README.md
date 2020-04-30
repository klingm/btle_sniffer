# btle_sniffer
This program requires a RaspPi 4 and a nRF52-DK with installed Bluetooth LE Sniffer (see Nordic Semi documentation) firmware to capture and visualize live RSSI data.  The image for use on the RaspPi 4 is available from the author.  Three plots are generated showing the measured RSSI on each of the available Bluetooth LE advertising channels (37, 38, 39).  Additionally, the stats for each channel are shown.  All data is saved in an output file in the same folder as the script as "tshark.out".  In order to run the program, a Linux installation with ssh client, wireshark/tshark, python3, pysimplegui, and matplotlib is required.

The user interface is shown below.
![btle_sniffer GUI](readme/gui.png)
