#!/usr/bin/python
# -*- coding: utf-8 -*-

# DCF receiver module https://de.elv.com/dcf-empfangsmodul-dcf-2-091610
# DCF1 module receives DCF77 signal, see https://en.wikipedia.org/wiki/DCF77

from machine import Pin, I2C
from time import sleep, sleep_ms, ticks_ms, ticks_diff
from math import ceil, floor
import binascii
#import uasyncio


# Loops until a new minute is detected 
def detectNewMinute(dcfpin):
    print("Waiting for all-zero 59th second until listening to signal:")
    countZeros = 0
    mx = 0
    t = 0
    sleeptime = 50
    start = ticks_ms()
    breakat = ceil(1000/sleeptime) + 1
    while True:
        v = 1-dcfpin.value()
        print("%d" % (v), end="")
        delta = t - ticks_diff(ticks_ms(), start)
        if v == 0:
            countZeros += 1
            if countZeros > mx:
                mx = countZeros
        else:
            countZeros = 0
        sleep_ms(sleeptime + delta)
        t += sleeptime
        if countZeros >= breakat:
            print("No Amplitude Modulation for "+str(breakat)+" consecutive readings. Must be 59 seconds")
            return True

# returns weekday that corresponds to i or "Invalid day of week"
def weekday(i):
        switcher={
                1:'Monday',
                2:'Tuesday',
                3:'Wednesday',
                4:'Thursday',
                5:'Friday',
                6:'Saturday',
                7:'Sunday'
             }
        return switcher.get(i,"Invalid day of week")

def atobar(a, val):
    stringa=''
    if val==0:
        block = '▒'
    else:
        block = '█'
    for i in range (1,len(a)):
        if a[i]==1:
            stringa += block
        else:
            stringa += ' '
    return stringa


def twodigits(digit):    # Takes a single digit integer and turns it into a two digit string (or a two digit number and does nothing to it). 
    digitstring=str(digit)        
    if len(digitstring)==1:
        digitstring= "0"+digitstring
    return digitstring

# decodes the received signal into a time 
# This still relies on a relatively clean signal. It would be better to just take 1 second samples and count what's in there. No need to change for now.
def computeTime(dcf):
    radiotime='failed'
    minutesince12='failed'
    minute, stunde, tag, wochentag, monat, jahr = -1, -1, -1, -1, -1, -1
    samplespeed = 5                                 # time between samples (ms)
    samples = floor(1000/samplespeed * .35)         # sample points taken over .35 of a second 
    a = [0] * samples
    secs, bitNum, cnt = 0, 0, 0
    timeInfo = []
    start = ticks_ms()
    noisethreshms = 40
    zerothreshms = 130
    print("Computing time:",samples,"samples @",1000/samplespeed,"samples a second. 100ms would be", str(floor(.1*1000/samplespeed)),"samples. 200ms would be",str(floor(.2*1000/samplespeed)))
    print("Bars show 0 as space and 1 as solid. If signal is classified as ONE then █, if ZERO ▒") 
    while True:
        delta = cnt * samplespeed - ticks_diff(ticks_ms(), start)
        #print ("delta ms:"+str(delta))
        a.pop(0)
        a.append(1-dcf.value())
        if  a[0]==0 and a[1]==1 and sum(a[0:10]) > 7:               # first element 0 second 1 and first 10 has more than 7 ones (remove hardcoding)
            
            if sum(a) > 1000/samplespeed * noisethreshms/1000:      # Anything less than 50 ms is considered noise
                if sum(a) <= 1000/samplespeed * zerothreshms/1000:   # Anything less than 140 ms is a zero
                    timeInfo.append(0)
                else:
                    timeInfo.append(1)
                bar= atobar(a,timeInfo[bitNum])   
                print(str(bitNum) + '\t'+ bar)
                bitNum += 1
                # Flash LED while getting radio signal
                ledPin.toggle()
        if bitNum == 59:
            if timeInfo[0] != 0 or timeInfo[20] != 1:
                print("Error: Check bits not set to correct value")
                #break
                return radiotime, False
            if (sum(timeInfo[21:29]) % 2 == 1) or (sum(timeInfo[29:36])% 2 == 1) or (sum(timeInfo[36:59])% 2 == 1) :
                print("Error: Parity")
                # break
                return radiotime, False
            minute    =  timeInfo[21] + 2 * timeInfo[22] + 4 * timeInfo[23] + 8 * timeInfo[24] + 10 * timeInfo[25] + 20 * timeInfo[26] + 40 * timeInfo[27]
            
            stunde    =  timeInfo[29] + 2 * timeInfo[30] + 4 * timeInfo[31] + 8 * timeInfo[32] + 10 * timeInfo[33] + 20 * timeInfo[34]
            tag       =  timeInfo[36] + 2 * timeInfo[37] + 4 * timeInfo[38] + 8 * timeInfo[39] + 10 * timeInfo[40] + 20 * timeInfo[41]
            wochentag =  timeInfo[42] + 2 * timeInfo[43] + 4 * timeInfo[44]
            monat     =  timeInfo[45] + 2 * timeInfo[46] + 4 * timeInfo[47] + 8 * timeInfo[48] + 10 * timeInfo[49]
            jahr      =  timeInfo[50] + 2 * timeInfo[51] + 4 * timeInfo[52] + 8 * timeInfo[53] + 10 * timeInfo[54] + 20 * timeInfo[55] + 40 * timeInfo[56] + 80 * timeInfo[57]
            print("{:d}/{:02d}/{:02d} ({:s}) {:02d}:{:02d}:{:02d}".format(2000+jahr, monat, tag, weekday(wochentag), stunde, minute, 0, 0))            
            radiotime= twodigits(stunde)+ ":" + twodigits(minute) + ":00," + weekday(wochentag) + "," + str(2000+jahr) + '-' + twodigits(monat)+ '-' + twodigits(tag)
            # sleep for 1 second and break
            sleep(1)
            return radiotime, True
        sleep_ms(samplespeed + delta)
        cnt += 1

class ds3231(object):
#            13:45:00 Mon 24 May 2021
#  the register value is the binary-coded decimal (BCD) format
#               sec min hour week day month year
    NowTime = b'\x00\x45\x13\x02\x24\x05\x21'
    w  = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
    address = 0x68
    start_reg = 0x00
    alarm1_reg = 0x07
    control_reg = 0x0e
    status_reg = 0x0f
    def __init__(self,i2c_port,i2c_scl,i2c_sda):
        self.bus = I2C(i2c_port,scl=Pin(i2c_scl),sda=Pin(i2c_sda), freq=200000)

    def set_time(self,new_time):
        hour = new_time[0] + new_time[1]
        minute = new_time[3] + new_time[4]
        second = new_time[6] + new_time[7]
        week = "0" + str(self.w.index(new_time.split(",",2)[1])+1)
        year = new_time.split(",",2)[2][2] + new_time.split(",",2)[2][3]
        month = new_time.split(",",2)[2][5] + new_time.split(",",2)[2][6]
        day = new_time.split(",",2)[2][8] + new_time.split(",",2)[2][9]
        now_time = binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ',''))
        #print(binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ','')))
        #print(self.NowTime)
        self.bus.writeto_mem(int(self.address),int(self.start_reg),now_time)
    
    def read_time(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        a = t[0]&0x7F  #second
        b = t[1]&0x7F  #minute
        c = t[2]&0x3F  #hour
        d = t[3]&0x07  #week
        e = t[4]&0x3F  #day
        f = t[5]&0x1F  #month
        timestring="20%x/%02x/%02x %02x:%02x:%02x %s" %(t[6],t[5],t[4],t[2],t[1],t[0],self.w[t[3]-1])
        #print(timestring)
        return timestring

    def set_alarm_time(self,alarm_time):
        #    init the alarm pin
        self.alarm_pin = Pin(ALARM_PIN,Pin.IN,Pin.PULL_UP)
        #    set alarm irq
        self.alarm_pin.irq(lambda pin: print("alarm1 time is up"), Pin.IRQ_FALLING)
        #    enable the alarm1 reg
        self.bus.writeto_mem(int(self.address),int(self.control_reg),b'\x05')
        #    convert to the BCD format
        hour = alarm_time[0] + alarm_time[1]
        minute = alarm_time[3] + alarm_time[4]
        second = alarm_time[6] + alarm_time[7]
        date = alarm_time.split(",",2)[2][8] + alarm_time.split(",",2)[2][9]
        now_time = binascii.unhexlify((second + " " + minute + " " + hour +  " " + date).replace(' ',''))
        #    write alarm time to alarm1 reg
        self.bus.writeto_mem(int(self.address),int(self.alarm1_reg),now_time)
    
def pulseminute(lasttime,a,b):
    print('PULSE 1 min')
    # get a b and lastime
    a = not bool(a) # Reverse polarity from the lastpulse 
    b = not bool(b)
    print("Polarity: " + str(a) + str(b))
    clock1(int(a))
    clock2(int(b))
    sleep_ms(300)
    clock1(0)
    clock2(0)
    splittime=lasttime.split(':')
    lasttimehour=int(splittime[0])
    lasttimemin=int(splittime[1])
    # Now increment by 1 minute ( bearing in mind that 11:59 + 1 is 00:00 )
    lasttimemin=(lasttimemin +1) % 60
    if lasttimemin==0:
        lasttimehour=lasttimehour + 1
    lasttimehour=(lasttimehour) % 12
    # turn the minute motor off and then return the last values
    newtime= twodigits(lasttimehour) + ":" + twodigits(lasttimemin) + ":00"
    strngtofile = newtime + '\t' + str(a)+ '\t' + str(b)
    file = open ("lastpulseat.txt", "w+")  #writes to file, even if it doesnt exist
    file.write(strngtofile)
    file.close()
    # Dignified little sleep so we don't upset the clock mechanism
    sleep(1)
    return

def minutesince12(timestring):
    breakuptime =timestring.split(":") 
    minsintoday=(int(breakuptime[0]) % 12)*60+int(breakuptime[1])   # We'll avoid midnight issues by never using it then *taps temple
    return minsintoday

def calcoffset(timenow):
    # Compare real time clock to the time in file (or if the file doesn't exist, use the initial time file)
    try:
        f = open('lastpulseat.txt', "r")
        string = f.read().split('\t')
        a=(string[1]=='True')
        b=(string[2]=='True')
        lastpulseat = string[0]
        lastpulse = minutesince12(lastpulseat)
    except:  # open failed
        print('file does not exist. Assuming this is the first run')
        # This initial time file has the time that the clock reads on first connection
        f = open('firstruntime.txt', "r")
        initialstring = f.read()
        lastpulseat = initialstring
        lastpulse = minutesince12(initialstring)
        a= True    # for an even number of minutes, for an odd number of minutes reverse this, not coded in because it depends on the wiring
        b= False
    rtcminutesince12 = minutesince12(timenow)
    offset=rtcminutesince12 - lastpulse            
    #print('Offset:' + str(offset) + "-" + str(timenow) + " " + str(lastpulseat) + " " + str(rtcminutesince12) + " " + str(lastpulse))
    return offset, lastpulseat, a, b

def dcf77update(dcf):
    while not detectNewMinute(dcf):
        pass
    radiotime, gottime = computeTime(dcf)
    if gottime==True:
        sleep(1) 
        print(radiotime)
        rtc.set_time(radiotime)
        ledPin.value(1)
    else:
        print('Radio Time Fail, turning off on board LED as visual cue')
        ledPin.value(0)
    return gottime

#---------------- MAIN LOGIC

if __name__ == '__main__':
    FORCE_RADIO_UPDATE = True          # Force radio update on startup
    #------------ Real Time Clock (RTC) PIN ALLOCATION
    #    the first version of the rtc uses i2c1
    I2C_PORT = 1
    I2C_SDA = 6
    I2C_SCL = 7
    #    The newer versions of the RTC use i2c0. If there are issues, try to comment the i2c1 lines and uncomment the i2c0
    #I2C_PORT = 0
    #I2C_SDA = 20
    #I2C_SCL = 21
    #ALARM_PIN = 3
    #----------- END RTC PIN ALLOCATION
    

    # Initialise DCF77 receiver and Real Time Clock and onboard LED (we'll use this to show limited diagnostic info)
    dcf = Pin(16, Pin.IN,Pin.PULL_UP)
    rtc = ds3231(I2C_PORT  ,I2C_SCL,I2C_SDA)
    ledPin = Pin(25, Pin.OUT, value = 0) # Onboard led on GPIO 25
    clock2 = Pin(14, Pin.OUT, value=1)          # Toggle polarity to advance minute ORANGE
    clock1 = Pin(13, Pin.OUT, value=1)          # Driving the seconds hand YELLOW
    ledPin(1)                                   # A quick flash of the pico's onboard LED, to illustrate life
    sleep(.3)
    ledPin(0)
    print("Startup of DCF77 code. RTC reads:")
    print(rtc.read_time())
    gottime=False
    try:
        if FORCE_RADIO_UPDATE:
            raise('Forced Radio')
        f = open('lastpulseat.txt', "r")
        f.close()
        print('There is a lastpulse file. Assuming Real Time clock is ok.... will set against radio signal later')
    except:
        print('Looks like the first (or forced radio) run, setting rtc from radio signal')
        while gottime==False:
            gottime=dcf77update(dcf)

    #--------------Main loop
    # Super simple:
    # 1. Is the clock showing the right time according to the RTC (or is it more than an hour fast)? 
    # 2. If no advance a minute, otherwise, do nothing
    # 3. Goto 1

    while True:
        rtctimestring=rtc.read_time().split(" ")[1] # Get the current time string from the rtc
        # run this once a day (at a time that won't cause issues (3:33))- update rtc
        if rtctimestring=="03:33:30":     # The correction in the wee hours of the morning, only try once
            dcf77update(dcf)
        # Calculate offset by comparing value in file from last pulse to rtc value
        offset, lasttime, a, b = calcoffset(rtctimestring)
        if offset>=-60 and offset<=0:
            pass
        else:
            # Advance the minute hand, make a note of where it is
            pulseminute(lasttime,a,b)
        sleep_ms(100)
