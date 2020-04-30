# btle_sniffer
This program requires a RaspPi 4 and a nRF52-DK with installed Bluetooth LE Sniffer (see Nordic Semi documentation) firmware to capture and visualize live Bluetooth LE RSSI data.  The image for use on the RaspPi 4 is available from the author.  

The btle_sniffer.py program generates three plots showing the measured RSSI on each of the available Bluetooth LE advertising channels (37, 38, 39).  Additionally, the stats for each channel are shown.  All data is saved in an output file in the same folder as the script as "tshark.out".  In order to run the program, a Linux installation with ssh client, wireshark/tshark, python3, pysimplegui, and matplotlib is required.  For convenience, the following OVA (Open Virtualization Framework) Ubuntu 18.04 VM can be downloaded and used.  It is fully configured with this software and the packages required to run it.

[Ubuntu 18.04 OVA File](https://drive.google.com/file/d/1dWmI-uXqkVM4jhfaz4iX1YwmndrMgIVz/view?usp=sharing)

[Ubuntu 18.04 OVA Readme](https://drive.google.com/open?id=1KTFkCMhauD021Ow03gZeThJPVKwmc4OWUg1Dok6Tf40)

The program is executed on the computer running Linux, which connects to the RaspPi 4 and the BTLE sniffer using commands piped over ssh.  The BTLE sniffer from Nordic Semi does not work with tshark (only wireshark), so a capture is initiated to a local file on the RaspPi 4 that is the streamed to the local Linux computer and consumed by the btle_sniffer program.  The GUI is rendered using a TkAgg backend for the Matplotlib and PySimpleGUI libbraries.

The user interface is shown below.
![btle_sniffer GUI](readme/gui.png)

## Usage

The Combo Box for the advertising address allows the user to filter the display on a specific Bluetooth MAC address.  The list of addresses can be updated using the "Refresh Addr List" button.  Selecting '\* \*' results in all data being displayed.  To make any changes take effect clock the OK button.

The output file format is:

Timestamp, Channel, Src Addr, Adv Addr, RSSI

![btle_sniffer GUI](readme/tshark.out.png)

## Matlab Script
An additional Matlab script has been provided for reading in and processing the data in the output file.  The script creates a plot for each channel's RSSI and then calculates and prints the statistics for each dataset.  The script usage is shown below:

![btle_sniffer GUI](readme/matlab_usage.png)

![Matlab plot](readme/matlab_plot.png)

![Matlab plot](readme/matlab_stats.png)
