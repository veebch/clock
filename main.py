# Micropython script to set rtc-time to time from
# DCF1 receiver module https://www.pollin.de/p/dcf-77-empfangsmodul-dcf1-810054?gclid=EAIaIQobChMIpdOkt7bK5wIViM13Ch0Tsw1dEAQYASABEgKgafD_BwE
# DCF1 module receives DCF77 signal, see https://en.wikipedia.org/wiki/DCF77

from machine import Pin, Signal, RTC
from time import sleep, sleep_ms, ticks_ms, ticks_diff
from math import ceil, floor

# Loops until a new minute is detected
def detectNewMinute(dcfpin):
    print("in detectNewMinute.. waiting")
    countZeros = 0
    mx = 0
    t = 0
    sleeptime = 50
    start = ticks_ms()
    breakat = ceil(1000/sleeptime) + 1
    while True:
        v = dcfpin.value()
        # print("Zeroes %d: signal %d, max zeros %d" % (countZeros,v,mx))
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
            print("No Amplitude Modulation for "+str(breakat)+" or more consecutive readings. Must be 59 seconds")
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
 
# decodes the received signal into a time and sets rtc to it
def computeTime(rtc,dcf):
    minute, stunde, tag, wochentag, monat, jahr = -1, -1, -1, -1, -1, -1
    samplespeed = 10                               # time between samples (ms)
    samples = floor(1000/samplespeed * .25)        # sample points
    a = [0] * samples
    secs, bitNum, cnt = 0, 0, 0
    timeInfo = []
    start = ticks_ms()
    noisethreshms = 50
    zerothreshms = 140
    print("In computeTime: ",samples," samples.",1000/samplespeed," samples a second. 100ms would be ", str(floor(.1*1000/samplespeed))," 200ms would be ",str(floor(.2*1000/samplespeed)))
    while True:
        delta = cnt * samplespeed - ticks_diff(ticks_ms(), start)
        #print ("delta ms:"+str(delta))
        a.pop(0)
        a.append(dcf.value())
        if  a[0]==0 and a[1] == 1:
            print(bitNum,a, sum(a))
            if sum(a) > 1000/samplespeed * noisetheshms/1000:      # Anything less than 50 ms is considered noise
                if sum(a) < 1000/samplespeed * zerotheshms/1000:   # Anything less than 140 ms is a zero
                    timeInfo.append(0)
                    print ("ZERO")
                else:
                    timeInfo.append(1)
                    print ("ONE")
                bitNum += 1
        if bitNum == 59:
            if timeInfo[0] != 0 or timeInfo[20] != 1:
                print("Error: check bits")
                #break
                return True
            if (arraysumpart(timeInfo,21,29) % 2 != 0) or (arraysumpart(timeInfo,29,36)% 2 != 0) or (arraysumpart(timeInfo,36,59)% 2 != 0) :
                print("Error: parity")
                print (timeInfo[21:29])
                print (timeInfo[29:36])
                print (timeInfo[36:59])
                # break
                return True
            minute    =  timeInfo[21] + 2 * timeInfo[22] + 4 * timeInfo[23] + 8 * timeInfo[24] + 10 * timeInfo[25] + 20 * timeInfo[26] + 40 * timeInfo[27]
            stunde    =  timeInfo[29] + 2 * timeInfo[30] + 4 * timeInfo[31] + 8 * timeInfo[32] + 10 * timeInfo[33] + 20 * timeInfo[34]
            tag       =  timeInfo[36] + 2 * timeInfo[37] + 4 * timeInfo[38] + 8 * timeInfo[39] + 10 * timeInfo[40] + 20 * timeInfo[41]
            wochentag =  timeInfo[42] + 2 * timeInfo[43] + 4 * timeInfo[44]
            monat     =  timeInfo[45] + 2 * timeInfo[46] + 4 * timeInfo[47] + 8 * timeInfo[48] + 10 * timeInfo[49]
            jahr      =  timeInfo[50] + 2 * timeInfo[51] + 4 * timeInfo[52] + 8 * timeInfo[53] + 10 * timeInfo[54] + 20 * timeInfo[55] + 40 * timeInfo[56] + 80 * timeInfo[57]
            #Now wait for change in minute and set rtc
            print("{:d}/{:02d}/{:02d} ({:s}) {:02d}:{:02d}:{:02d}".format(2000+jahr, monat, tag, weekday(wochentag), stunde, minute, 0, 0))
            # Now wait for minute trigger to set rtc
            loop=True
            while loop:
                loop = not detectNewMinute(dcf)
            rtc.datetime((2000+jahr, monat, tag, wochentag, stunde, minute, 0  , 0))
            print(rtc.datetime())
            #break
            return False
        sleep_ms(samplespeed + delta)
        cnt += 1
        
def arraysumpart(arr, fromindex, toindex):
    sum=0
    for i in range(fromindex, toindex):
        sum += arr[i]
    return int(sum)

# to wake up dcf1 (maybe connecting to PON pin is sufficient)
pon_pin = Pin(16, Pin.OUT) #D5
#pon_pin.on()
#sleep_ms(200)
#pon_pin.off()

# dcf1
dcf = Pin(15, Pin.IN,Pin.PULL_DOWN) 

# real time clock
rtc = RTC()

cnd = True
while cnd:
    if detectNewMinute(dcf):
        cnd = computeTime(rtc,dcf)
