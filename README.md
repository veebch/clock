[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Clock

Getting a Raspberry Pi Pico and a DCF77 receiver to power a handsome old clock and make it super-accurate, without any internet.

The [DCF77 signal](https://en.wikipedia.org/wiki/DCF77) is a radio signal that carries information from some Atomic Clocks. The signal pretty much covers Europe and is accurate to within a second over about 300,000 years. 

(The United States uses [WWVB](https://en.wikipedia.org/wiki/WWVB) and you could easily adapt the code to that signal)

# Hardware
- Old 'nebenuhr' clock with secondary mechanism (a mechanism that is controlled by pulses from the mother-clock)
- A ferrite receiver (for DCF77 signal)
- A microcontroller (Raspberry Pi Pico)
- Real time clock (RTC) (backup for any radio signal issues)
- 3.3V to 24V step up board
- H bridge (for the polarity switch that triggers the clock mechanism)

# Video


# Building your own clock

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using. 

Copy the files from this repository

      git clone https://github.com/veebch/clock

then send them your Pico using ampy
   
      sudo ampy -p /dev/ttyACM0 put ./

Edit the file `firstruntime.txt` to show the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code will keep track of time after power-off.

# Code used

The DCF77 part of the code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1).

# Licence 

GPL 3.0
