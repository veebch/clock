
# DCF1 receiver module https://www.pollin.de/p/dcf-77-empfangsmodul-dcf1-810054?gclid=EAIaIQobChMIpdOkt7bK5wIViM13Ch0Tsw1dEAQYASABEgKgafD_BwE
# DCF1 module receives DCF77 signal, see https://en.wikipedia.org/wiki/DCF77

from machine import Pin, Signal
from time import sleep, sleep_ms, ticks_ms, ticks_diff
from math import ceil, floor


# Loops until a new minute is detected
def detectNewMinute(dcfpin):
    print("Waiting for 59th second until listening to signal")
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

# decodes the received signal into a time 
def computeTime(dcf):
    minute, stunde, tag, wochentag, monat, jahr = -1, -1, -1, -1, -1, -1
    samplespeed = 5                                 # time between samples (ms)
    samples = floor(1000/samplespeed * .35)         # sample points taken over .35 of a second 
    a = [0] * samples
    secs, bitNum, cnt = 0, 0, 0
    timeInfo = []
    start = ticks_ms()
    noisethreshms = 40
    zerothreshms = 180
    print("Computing time:",samples,"samples @",1000/samplespeed,"samples a second. 100ms would be", str(floor(.1*1000/samplespeed)),"samples. 200ms would be",str(floor(.2*1000/samplespeed)))
    print("Bars show 0 as space and 1 as solid. If signal is classified as ONE then █, if ZERO ▒") 
    while True:
        delta = cnt * samplespeed - ticks_diff(ticks_ms(), start)
        #print ("delta ms:"+str(delta))
        a.pop(0)
        a.append(dcf.value())
        if  a[0]==0 and a[1]==1 and sum(a[0:10]) > 7:               # first element 0 second 1 and first 10 has more than 7 ones (remove hardcoding)
            
            if sum(a) > 1000/samplespeed * noisethreshms/1000:      # Anything less than 50 ms is considered noise
                if sum(a) <= 1000/samplespeed * zerothreshms/1000:   # Anything less than 140 ms is a zero
                    timeInfo.append(0)
                else:
                    timeInfo.append(1)
                bar= atobar(a,timeInfo[bitNum])   
                print(str(bitNum) + '\t'+ bar)
                bitNum += 1
        if bitNum == 59:
            if timeInfo[0] != 0 or timeInfo[20] != 1:
                print("Error: check bits")
                #break
                return True
            if (arraysumpart(timeInfo,21,29) % 2 == 1) or (arraysumpart(timeInfo,29,36)% 2 == 1) or (arraysumpart(timeInfo,36,59)% 2 == 1) :
                print("Error: parity")
                # break
                return True
            minute    =  timeInfo[21] + 2 * timeInfo[22] + 4 * timeInfo[23] + 8 * timeInfo[24] + 10 * timeInfo[25] + 20 * timeInfo[26] + 40 * timeInfo[27]
            stunde    =  timeInfo[29] + 2 * timeInfo[30] + 4 * timeInfo[31] + 8 * timeInfo[32] + 10 * timeInfo[33] + 20 * timeInfo[34]
            tag       =  timeInfo[36] + 2 * timeInfo[37] + 4 * timeInfo[38] + 8 * timeInfo[39] + 10 * timeInfo[40] + 20 * timeInfo[41]
            wochentag =  timeInfo[42] + 2 * timeInfo[43] + 4 * timeInfo[44]
            monat     =  timeInfo[45] + 2 * timeInfo[46] + 4 * timeInfo[47] + 8 * timeInfo[48] + 10 * timeInfo[49]
            jahr      =  timeInfo[50] + 2 * timeInfo[51] + 4 * timeInfo[52] + 8 * timeInfo[53] + 10 * timeInfo[54] + 20 * timeInfo[55] + 40 * timeInfo[56] + 80 * timeInfo[57]
            #Now wait for change in minute
            print("{:d}/{:02d}/{:02d} ({:s}) {:02d}:{:02d}:{:02d}".format(2000+jahr, monat, tag, weekday(wochentag), stunde, minute, 0, 0))
            # Now wait for minute trigger to set time
            loop=True
            while loop:
                loop = not detectNewMinute(dcf)
            radiotime=(2000+jahr, monat, tag, wochentag, stunde, minute, 0  , 0)
            print(radiotime)
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


cnd = True
while cnd:
    if detectNewMinute(dcf):
        cnd = computeTime(dcf)
