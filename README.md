# btle_sniffer
This program requires a RaspPi 4 and a nRF52-DK with installed Bluetooth LE Sniffer (see Nordic Semi documentation) firmware to capture and visualize live Bluetooth LE RSSI data.  The image for use on the RaspPi 4 is available from the author.  

The btle_sniffer.py program generates three plots showing the measured RSSI on each of the available Bluetooth LE advertising channels (37, 38, 39).  Additionally, the stats for each channel are shown.  All data is saved in an output file in the same folder as the script as "tshark.out".  In order to run the program, a Linux installation with ssh client, wireshark/tshark, python3, pysimplegui, and matplotlib is required.

The program is executed on the computer running Linux, which connects to the RaspPi 4 and the BTLE sniffer using commands piped over ssh.  The BTLE sniffer from Nordic Semi does not work with tshark (only wireshark), so a capture is initiated to a local file on the RaspPi 4 that is the streamed to the local Linux computer and consumed by the btle_sniffer program.  The GUI is rendered using a TkAgg backend for the Matplotlib and PySimpleGUI libbraries.

The user interface is shown below.
![btle_sniffer GUI](readme/gui.png)

The output file format is:

Timestamp, Channel, Src Addr, Adv Addr, RSSI

![btle_sniffer GUI](readme/tshark.out.png)
