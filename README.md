![components](/images/DCF77github.jpg)

[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)


[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/v_e_e_b/)


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
- A ferrite receiver [for the DCF77 signal](https://de.elv.com/dcf-empfangsmodul-dcf-2-091610) if you're in Europe (or [one for the WWVB signal](https://tinkersphere.com/sensors/1517-wwvb-nist-radio-time-receiver-kit.html) if you're in the US)... Not needed if you're using Pico W
- A microcontroller (Raspberry Pi Pico or Pico W)
- [Real time clock](https://eckstein-shop.de/WaveSharePrecisionRTCModuleforRaspberryPiPico2COnboardDS3231ChipEN) (backup for any radio signal issues)... Not needed if you're using Pico W
- H bridge ([LN298](https://www.reichelt.com/ch/de/entwicklerboards-motodriver2-l298n-debo-motodriver2-p202829.html?PROVID=2808)) **or** a 2 channel SPDT Relay Switch, for the polarity switch that triggers the clock mechanism
- [Step-up module](https://www.amazon.de/gp/product/B079H3YD8V) to send correct voltage pulse to the clock (or a dc power supply, as used in the video)

# Videos

An overview of how the clock works:

[![Explainer vid](http://img.youtube.com/vi/ZhPZBuXZctg/0.jpg)](http://www.youtube.com/watch?v=ZhPZBuXZctg "Video Title")

How the pieces are assembled:

[![Explainer vid II](http://img.youtube.com/vi/vrSi5gCIbSA/0.jpg)](http://www.youtube.com/watch?v=vrSi5gCIbSA "Video Title")

# Building your own clock

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using. 


## Schematic

The antenna also needs 3.3V power and GND. They were omitted in order to keep the diagram tidy. If you're sending more than 12V (we used 24V) to the clock then make sure you remove the 5v jumper from the h-bridge. 
![schematic](/images/circuit.png)

### Preparing files

Copy the files from this repository

      git clone https://github.com/veebch/clock
      cd clock

**Only if you're running the code on a Pico W and want to sync to time online**
      
      mv webtime.py main.py
      mv secrets_example.py secrets.py

and edit secrets.py so that it contains your WiFi credentials.

### Transfer files

Send the files to your Pico using ampy
   
      ampy -p /dev/ttyACM0 put ./*

Edit the file `firstruntime.txt` to show the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code will keep track of time after power-off.

# Running

The code in main.py executes as soon as the Pico is powered on.


If you run while connected to Thonny then you will see the terminal output. On the radio version this shows the signal as it is decoded. If the bars look irregular or have gaps in, then there is an issue with the radio signal. A clear signal will look something like this:

![Action Shot](/images/clockscan.png)

# Code used

The DCF77 part of the code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1).

# To Do

WiFi version that runs a web server for easy tweaks to the time via smartphone.

# Licence 

GPL 3.0
