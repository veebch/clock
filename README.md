[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Clock

Getting a Raspberry Pi Pico and a radio receiver to power a handsome old clock and make it super-accurate, without any internet 

The [DCF77 signal](https://en.wikipedia.org/wiki/DCF77) is a radio signal that carries information from some Atomic Clocks. The signal covers most of Europe and is accurate to within a second over about 300,000 years (the DCF77 signal has been broadcasting since the time since the 1973 and in 2021 it was agreed to be continued for at least 10 more years). 

(The United States uses [WWVB](https://en.wikipedia.org/wiki/WWVB) and you could easily adapt the code to that signal)

# Hardware
- Old ['nebenuhr' clock](https://www.ebay.de/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw=nebenuhr&_sacat=0&LH_TitleDesc=0&_odkw=buerk+uhr&_osacat=0) with secondary mechanism (a mechanism that is controlled by pulses from the mother-clock)
- A ferrite receiver (for DCF77 signal)
- A microcontroller (Raspberry Pi Pico)
- Real time clock (RTC) (backup for any radio signal issues)
- 24V DC to 5V DC step down board (you can skip this if you intend to power the pico via USB)
- H bridge (for the polarity switch that triggers the clock mechanism)

# Video


# Building your own clock

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using. 

Copy the files from this repository

      git clone https://github.com/veebch/clock
      cd clock

then send them your Pico using ampy
   
      sudo ampy -p /dev/ttyACM0 put ./

Edit the file `firstruntime.txt` to show the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code will keep track of time after power-off.
# Running

If you run while connected to Thonny then you will see the terminal output showing the signal as it is decoded. If the bars look irregular or have gaps in, then there is an issue with the dcf77 signal. A clear signal will look something like this:

![Action Shot](/images/clockscan.png)

# Code used

The DCF77 part of the code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1).

# Licence 

GPL 3.0
