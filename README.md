![components](/images/DCF77github.jpg)

[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Clock

Reinvigorating a handsome old clock and making it super-accurate, without any internet. Uses a Raspberry Pi Pico, a radio antenna and a couple of components to emulate a signal from a Mother clock. You can define the pulse interval as a parameter, so it works with a broad range of clocks (most take 60 seconds intervals, but some take 30 second or 1 second pulses).

The [DCF77 signal](https://en.wikipedia.org/wiki/DCF77) is a radio signal that carries information from some Atomic Clocks. The signal covers most of Europe and is accurate to within a second over about 300,000 years (the DCF77 signal has been broadcasting the time since 1973 and in 2021 it was agreed to be continued for at least 10 more years). 

(The United States uses [WWVB](https://en.wikipedia.org/wiki/WWVB), United Kingdom uses [MSF](https://en.wikipedia.org/wiki/Time_from_NPL_(MSF)) and Japan uses [JJY](https://en.wikipedia.org/wiki/JJY). You could easily adapt the code to any of those signals)

# Hardware
- Old ['nebenuhr' clock](https://www.ebay.de/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw=nebenuhr&_sacat=0&LH_TitleDesc=0&_odkw=buerk+uhr&_osacat=0) with secondary mechanism (a mechanism that is controlled by pulses from the mother-clock)
- A [ferrite receiver](https://de.elv.com/dcf-empfangsmodul-dcf-2-091610) (for the DCF77 signal)
- A microcontroller (Raspberry Pi Pico)
- [Real time clock](https://eckstein-shop.de/WaveSharePrecisionRTCModuleforRaspberryPiPico2COnboardDS3231ChipEN) (RTC) (backup for any radio signal issues)
- H bridge ([LN298](https://www.reichelt.com/ch/de/entwicklerboards-motodriver2-l298n-debo-motodriver2-p202829.html?PROVID=2808)), for the polarity switch that triggers the clock mechanism
- [Step-up module](https://www.amazon.de/gp/product/B079H3YD8V) to send correct voltage pulse to the clock (or a dc power supply, as used in the video)

# Video

[![Explainer vid](http://img.youtube.com/vi/ZhPZBuXZctg/0.jpg)](http://www.youtube.com/watch?v=ZhPZBuXZctg "Video Title")

# Building your own clock

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using. 


## Schematic

The antenna also needs 3.3V power and GND. They were omitted in order to keep the diagram tidy. If you're sending more than 12V (we used 24V) to the clock then make sure you remove the 5v jumper from the h-bridge. 
![schematic](/images/circuit.png)

Copy the files from this repository

      git clone https://github.com/veebch/clock
      cd clock

then send them your Pico using ampy
   
      sudo ampy -p /dev/ttyACM0 put ./*

Edit the file `firstruntime.txt` to show the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code will keep track of time after power-off.
# Running

The code in main.py executes as soon as the pico is powered on, but if you run while connected to Thonny then you will see the terminal output showing the signal as it is decoded. If the bars look irregular or have gaps in, then there is an issue with the dcf77 signal. A clear signal will look something like this:

![Action Shot](/images/clockscan.png)

# Code used

The DCF77 part of the code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1).

# Licence 

GPL 3.0
