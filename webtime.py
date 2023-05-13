#!/usr/bin/python
# -*- coding: utf-8 -*-

# The code just sets the RTC to localtime. Micropython does not have an obvious elegant way of dealing with timezones.

from machine import Pin, RTC, reset
import time
from math import ceil, floor
#import binascii
import network
import secrets
import urequests

worldtimeurl = "https://timeapi.io/api/TimeZone/zone?timeZone=Europe/Zurich"   #this will return the time based on your IP address
pulsefrequency = 60   # Pulse frequency in seconds

def set_time(worldtimeurl,wlan):
        wlan.connect(secrets.SSID, secrets.PASSWORD)
        while wlan.isconnected() is not True:
            time.sleep(1)
            print("Not connecting to WiFi\nWaiting\n")
        time.sleep(1)
        response = urequests.get(worldtimeurl)    
        # parse JSON
        parsed = response.json()
        datetime_str = str(parsed["currentLocalTime"])
        print(datetime_str)
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])
        # update internal RTC
        RTC().datetime((year,
                      month,
                      day,
                      0,
                      hour,
                      minute,
                      second,
                      0))
        print("RTC updated\n")
        wlan.disconnect()

# Takes a single digit integer and turns it into a two digit string
# (or a two digit number and does nothing to it).
def twodigits(digit):     
    digitstring=str(digit)        
    if len(digitstring)==1:
        digitstring= "0"+digitstring
    return digitstring

def pulsetoclock(lasttime,a,b):
    print('PULSE')
    # get a b and lastime
    a = not bool(a) # Reverse polarity from the lastpulse 
    b = not bool(b)
    print("Polarity: " + str(a) + str(b))
    clock1(int(a))
    clock2(int(b))
    time.sleep(1) # 1 second pulse
    clock1(0)
    clock2(0)
    splittime=lasttime.split(':')
    lasttimehour=int(splittime[0])
    lasttimemin=int(splittime[1])
    lasttimesecs=int(splittime[2])

    # Now increment by 1 pulse    
    delta= lasttimesecs + pulsefrequency
    inctimesecs=(delta) % 60
    if (delta // 60) > 0:
        inctimemin=(lasttimemin + (delta // 60)) % 60
    else:
        inctimemin = lasttimemin
    if (lasttimemin + (delta // 60))>=60:
        inctimehour=(lasttimehour + 1 ) % 12 # Assumes pluses are never more than an hour apart
    else:
        inctimehour=lasttimehour

    newtime= twodigits(inctimehour) + ":" + twodigits(inctimemin) + ":" + twodigits(inctimesecs)
    print(newtime)
    strngtofile = newtime + '\t' + str(a)+ '\t' + str(b)
    file = open ("lastpulseat.txt", "w+")  #writes to file, even if it doesnt exist
    file.write(strngtofile)
    file.close()
    # Dignified little sleep so we don't upset the clock mechanism
    time.sleep(.5)
    return

def pulsessince12(timestring):
    breakuptime =timestring.split(":")
    secondssince12=(int(breakuptime[0]) % 12)*3600+int(breakuptime[1])*60+int(breakuptime[2])   # We'll avoid midnight issues by never using it then *taps temple
    pulses=int(secondssince12/pulsefrequency)
    return pulses

def calcoffset(timenow):
    # Compare real time clock to the time in file (or if the file doesn't exist, use the initial time file)
    try:
        f = open('lastpulseat.txt', "r")
        string = f.read().split('\t')
        a=(string[1]=='True')           # String to Bool trick
        b=(string[2]=='True')           # String to Bool trick
        lastpulseat = string[0]
        lastpulse = pulsessince12(lastpulseat)
    except:  # open failed
        print('file does not exist. Assuming this is the first run')
        # This initial time file has the time that the clock reads on first connection
        f = open('firstruntime.txt', "r")
        initialstring = f.read()
        lastpulseat = initialstring
        lastpulse = pulsessince12(initialstring)
        a= True    # for an even number of minutes, for an odd number of minutes reverse this, not coded in because it depends on the wiring
        b= False
    rtcpulsessince12 = pulsessince12(timenow)
    offset=rtcpulsessince12 - lastpulse            
    #print('Offset:' + str(offset) + "-" + str(timenow) + " " + str(lastpulseat) + " " + str(rtcpulsessince12) + " " + str(lastpulse))
    return offset, lastpulseat, a, b



clock2 = Pin(14, Pin.OUT, value=0)          # These are the pins where you toggle polarity to advance the clock
clock1 = Pin(13, Pin.OUT, value=0)          

#---------------- MAIN LOGIC

def main():
    led = machine.Pin("LED", machine.Pin.OUT)
    led.off()
    led.on()
    time.sleep(1)
    led.off()
    print("Startup. RTC reads:")
    print(time.gmtime())
    print('connecting to internet and getting time')
    gottime=False
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    set_time(worldtimeurl,wlan)
    print(time.gmtime())

    #--------------Main loop
    # Super simple:
    # 1. Is the clock showing the right time (within a pulse) according to the RTC (or is it more than an hour fast)? 
    # 2. If no advance a pulse, otherwise, do nothing (clocks that can go backwards (eg Seiko) are not considered in this simple first version)
    # 3. Goto 1

    while True:
        rtctimestring=twodigits(time.localtime()[3])+':'+twodigits(time.localtime()[4])+':'+twodigits(time.localtime()[5]) # Get the current time string from the rtc
        # run this once a day (at a time that won't cause issues (3:33))- update rtc
        if rtctimestring=="03:00:00":     # reset daily. This will force a quick reconnect to wifi, and update the RTC 
            machine.reset()
        # Calculate offset by comparing value in file from last pulse to rtc value
        offset, lasttime, a, b = calcoffset(rtctimestring)
        if offset>=-60*60/pulsefrequency and offset<=0:
            pass 
        else:
            # Advance the clock, make a note of where it is currently
            pulsetoclock(lasttime,a,b)
        time.sleep(.1)

if __name__ == '__main__':
    main()



