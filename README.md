![components](/images/DCF77github.jpg)

[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?style=flat&logo=youtube&logoColor=red&labelColor=white&color=ffed53)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ) [![Instagram](https://img.shields.io/github/stars/veebch?style=flat&logo=github&logoColor=black&labelColor=white&color=ffed53)](https://www.instagram.com/v_e_e_b/)


# Clock

Reinvigorating/ recycling a handsome old clock and making it super-accurate, internet optional. Uses a Raspberry Pi Pico and a radio antenna (**or a Pico W and no radio antenna**) to emulate a signal from a Mother clock. You can define the pulse interval as a parameter, so it works with a broad range of clocks (most take 60 seconds intervals, but some take 30 second or 1 second pulses).

## European or US Radio Signals

The [DCF77 signal](https://en.wikipedia.org/wiki/DCF77) is a radio signal that carries information from some Atomic Clocks. The signal covers most of Europe and is accurate to within a second over about 300,000 years (the DCF77 signal has been broadcasting the time since 1973 and in 2021 it was agreed to be continued for at least 10 more years). 

The script also has (untested) code for [WWVB](https://en.wikipedia.org/wiki/WWVB), the signal used in the United States. To apply WWVB, change the `region` parameter in main.py from `DCF77` to `WWVB`. If you test it and it works, let me know.

(Japan uses [JJY](https://en.wikipedia.org/wiki/JJY). Adding code for this is on the todo list)

## Internet Version

A variation that involves WiFi, fewer components, less code and uses a Pico W. 

There is no need for a Real Time Clock (RTC) or Ferrite receiver as everything is done with a quick connect to WiFi and uses the Pico's RTC.

To use this variation, save the code in `webtime.py` as `main.py` on the Pico W. You will also need to save your WiFi login credentials as `secrets.py` on the Pico W in the format shown in `secrets_example.py`.

# Hardware
- Old ['nebenuhr' clock](https://www.ebay.de/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw=nebenuhr&_sacat=0&LH_TitleDesc=0&_odkw=buerk+uhr&_osacat=0) with secondary mechanism (a mechanism that is controlled by pulses from the mother-clock)
- Or, a clock with a similar mechanism, such as a Timatic slave clock. 
- A ferrite receiver [for the DCF77 signal](https://de.elv.com/dcf-empfangsmodul-dcf-2-091610) if you're in Europe (or [one for the WWVB signal](https://tinkersphere.com/sensors/1517-wwvb-nist-radio-time-receiver-kit.html) if you're in the US)... Not needed if you're using Pico W
- A microcontroller (Raspberry Pi Pico or Pico W)
- [Real time clock](https://eckstein-shop.de/WaveSharePrecisionRTCModuleforRaspberryPiPico2COnboardDS3231ChipEN) (backup for any radio signal issues)... Not needed if you're using Pico W
- H bridge ([LN298](https://www.reichelt.com/ch/de/entwicklerboards-motodriver2-l298n-debo-motodriver2-p202829.html?PROVID=2808)) **or** a [2 channel SPDT Relay Switch](https://wiki.seeedstudio.com/Grove-2-Channel_SPDT_Relay/), for the polarity switch that triggers the clock mechanism. For higher voltage clocks, the relay is the better option
- [Step-up module](https://www.amazon.de/gp/product/B079H3YD8V) to send correct voltage pulse to the clock (or a dc power supply, as used in the video)

# Videos

An overview of how the clock works:

[![Explainer vid](http://img.youtube.com/vi/ZhPZBuXZctg/0.jpg)](http://www.youtube.com/watch?v=ZhPZBuXZctg "Video Title")

How the pieces are assembled:

[![Explainer vid II](http://img.youtube.com/vi/vrSi5gCIbSA/0.jpg)](http://www.youtube.com/watch?v=vrSi5gCIbSA "Video Title")

# Building your own clock

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using. 


## Schematic

The antenna also needs 3.3V power and GND. They were omitted in order to keep the diagram tidy. If you're using the H bridge (rather than a SPDT relay) and  are sending more than 12V (we used 24V) to the clock then make sure you remove the 5v jumper from the H-bridge. 
![schematic](/images/circuit.png)

### Preparing files

Copy the files from this repository

      git clone https://github.com/veebch/clock
      cd clock

**Only if you're running the code on a Pico W and want to sync to time online**
      
      mv webtime.py main.py
      mv secrets_example.py secrets.py

and edit secrets.py so that it contains your WiFi credentials.

## Running a web server on the Pico W using Microdot

This simple web server allows adjustment of the clock if the time on the face gets out of sync with the actual time. This was developed to solve the problem where the time got out of sync due to a dicky old USB phone charger not supplying adequate current to advance the clock, and the clock controller being located in a location that was not easily accessible.

You need to download the microdot library from [the micodot repository](https://github.com/miguelgrinberg/microdot/blob/main/src/microdot/microdot.py) and then copy the file over to the root directory of your Pico W. 

The web server:
- Displays the current RTC time (according to the Pico).
- Provides an input field to update `firstruntime.txt`.
- Includes a "Synchronise Clock" button that:
  - Updates `firstruntime.txt`.
  - Deletes `lastpulseat.txt` (this is then re-created once sync is complete)
- Advances the clock by the required number of minutes based on the difference between firstruntime.txt and the script RTC time.
- Includes buttons to advance the clock by 1 and 5 minutes manually. Helpful in case the user inputs the wrong time in firstruntime input field, or if the clock falls behind while it is advancing/syncing, as this can take some time.
- Restricts web server access to devices on the same network as the Pico W (eg. 192.168.50.*.)

You will need to give the clock a fixed IP address to access the web server. Then, on line 181 of webtime.py, update the IP prefix to match this. For example, if the Pico W IP address is 192.168.1.69, the value here should be set to "192.168.1.". This ensures that the web server can only be accessed from devices on the same LAN/WLAN subnet. 

### Accessing and using the web server

Once your Pico W is connected to your Wi-Fi network and running the modified webtime.py script (renamed to main.py), you can control the clock via a simple web interface. Follow these steps:

1. Open the Web Interface:

  - On any device connected to the same network (with IP address in the 192.168.50.x range, or whatever your subnet is), open a web browser.
  - Navigate to the IP address for the Pico W: eg. http://192.168.50.19/
  - The control panel should display the current time (from the Pico’s RTC) and the baseline time stored in firstruntime.txt.

2. Synchronise the Clock:

  - In the interface, you’ll see an input field labeled Set initial time (HH:MM:SS).
  - Enter the time that is physically shown on the clock face.
  - Click the Synchronise clock button. This action will:
    - Update firstruntime.txt with the entered time.
    - Delete lastpulseat.txt (which holds the time of the last pulse).
    - Calculate the number of pulses (minutes) needed to synchronise the physical clock with the script time.
    - Trigger the clock to advance accordingly.
  - If the clock is ahead of the current time, the clock will stop advancing until the actual time 'catches up'.

3. Manual Adjustments:

  - If you need further fine-tuning, two additional buttons are available:
    - +1 minute: Advances the clock by one minute.
    - +5 minutes: Advances the clock by five minutes.
  - Use these buttons if you notice that the clock is still slightly out of sync.

5. Access Restrictions:

  - The web server is only accessible from devices on the local network. If you attempt to access it from an external network, you will receive a “Forbidden” message.

6. Troubleshooting:

  - If the web page does not load, verify that the Pico W is connected to the Wi-Fi network.
  - Ensure your device’s IP address is within the 192.168.1.x range (or whatever your subnet range is).
  - Check the serial console or Thonny output for any error messages that may indicate connection or configuration issues.
  - With the web server using these instructions, you can easily monitor and adjust the clock directly through your browser.


### Transfer files

Send the files to your Pico using ampy
   
      ampy -p /dev/ttyACM0 put ./*

Edit the file `firstruntime.txt` to show the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code will keep track of time after power-off.

This can also be done through the web server.

# Running

The code in main.py executes as soon as the Pico is powered on.


If you run while connected to Thonny then you will see the terminal output. On the radio version this shows the signal as it is decoded. If the bars look irregular or have gaps in, then there is an issue with the radio signal. A clear signal will look something like this:

![Action Shot](/images/clockscan.png)

# Code used

The DCF77 part of the code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1).

# Licence 

GPL 3.0
