[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Clock

Getting a Pico and a DCF77 receiver to power a handsome old clock

The [DCF77 signal](https://en.wikipedia.org/wiki/DCF77) is a radio signal that carries information from an Atomic Clock. The signal pretty much covers Europe.

(The US uses [WWVB](https://en.wikipedia.org/wiki/WWVB) and you could easily adapt the code to that signal)

# Hardware

- DCF77
- Pi Pico
- Clock
- 24V power supply to run the clock and supply the pulse

# Code used

The DCF77 code was based on [demogorgi/set-rtc-using-dcf77-via-dcf1](https://github.com/demogorgi/set-rtc-using-dcf77-via-dcf1). It relies on a clean DCF77 signal, but is beautifully readable.

The code works in two basic steps:
- Listen until the quiet 59th second
- Listen and decode

An alternative would be to listen for a minute, use the 59th second to rearrange the signal and then clean and decode. 

# Getting things up and running

Assemble the Pico, step up transformer and H bridge. Note that the voltage of the step up tranformer may vary depending on the clock you're using.

Copy the files from this repository to your pico using Thonny

Edit the file firstruntime.txt to the time that the clock is showing before the first run. This *should* be the only time you need to do this, the code should be able to keep track of time after power-off after this.

# Licence 

GPL 3.0
