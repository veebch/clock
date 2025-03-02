#!/usr/bin/python
# -*- coding: utf-8 -*-

from machine import Pin, RTC, reset
import time
from math import ceil, floor
import network
import secrets
import urequests

worldtimeurl = "https://timeapi.io/api/TimeZone/zone?timeZone=Australia/Canberra"  # Time based on timezone
pulsefrequency = 60   # Pulse frequency in seconds
wifi_retry_interval = 600  # 10 minutes between WiFi reconnection attempts
time.sleep(5)

# Helper function to format time as human-readable string
def format_time(t):
    year, month, day, hour, minute, second, *_ = t
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

# Function to print GMT and local time
def print_gmt_and_local_time(worldtimeurl):
    # Print GMT time
    gmt_time = time.gmtime()  # Get the GMT time
    print(f"GMT time: {format_time(gmt_time)} (UTC)")

    # Fetch local time from timezone API
    try:
        print(f"Fetching local time from: {worldtimeurl}")
        response = urequests.get(worldtimeurl)
        
        if response.status_code != 200:
            print(f"Failed to fetch time. HTTP Status Code: {response.status_code}")
            return

        parsed = response.json()
        datetime_str = str(parsed["currentLocalTime"])
        timezone_name = parsed["timeZone"]
        
        # Parse local time string
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])
        
        local_time = (year, month, day, hour, minute, second, 0, 0)
        print(f"Local time: {format_time(local_time)} ({timezone_name})")
    
    except OSError as e:
        print(f"Network error occurred: {e}")
    except ValueError as e:
        print(f"JSON parsing error: {e}")
    except Exception as e:
        print(f"Unexpected error fetching local time: {e}")

# WiFi connection function with retry logic
def set_time(worldtimeurl, wlan):
    wlan.connect(secrets.SSID, secrets.PASSWORD)
    retry_count = 0
    max_retries = 10
    while not wlan.isconnected() and retry_count < max_retries:
        time.sleep(2)
        retry_count += 1
        print(f"Not connecting to WiFi, retry {retry_count}/{max_retries}\n")

    if not wlan.isconnected():
        print("Failed to connect to WiFi after maximum retries.")
        return False  # WiFi connection failed

    ip = wlan.ifconfig()[0]
    netw = secrets.SSID
    print(f'Connected to {netw} on {ip}')

    try:
        # Fetch and print GMT and local time after connecting to WiFi
        print_gmt_and_local_time(worldtimeurl)

        # Fetch time data from API
        response = urequests.get(worldtimeurl)
        parsed = response.json()
        datetime_str = str(parsed["currentLocalTime"])
        print(f"Received time: {datetime_str}")

        # Parse the time string
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])

        # Update internal RTC
        RTC().datetime((year, month, day, 0, hour, minute, second, 0))
        print("RTC updated\n")
    except Exception as e:
        print(f"Error fetching or updating time: {e}")
        return False
    
    # Disconnect from WiFi
    wlan.disconnect()
    return True

# Takes a single digit integer and turns it into a two digit string
def twodigits(digit):     
    digitstring = str(digit)
    if len(digitstring) == 1:
        digitstring = "0" + digitstring
    return digitstring

def pulsetoclock(lasttime, a, b):
    print('PULSE')
    # Reverse polarity from the last pulse
    a = not a
    b = not b
    print(f"Polarity: {a}, {b}")

    # Trigger clock pulses
    clock1(int(a))
    clock2(int(b))

    # Pulse the onboard LED during the clock pulse
    led = Pin("LED", Pin.OUT)
    led.on()  # Turn the LED on
    time.sleep(1)  # 1 second pulse (adjust if necessary)
    clock1(0)
    clock2(0)
    led.off()  # Turn the LED off after the pulse

    # Split time into components
    lasttimehour, lasttimemin, lasttimesecs = map(int, lasttime.split(':'))

    # Increment time by pulse frequency
    delta = lasttimesecs + pulsefrequency
    inctimesecs = delta % 60
    inctimemin = (lasttimemin + (delta // 60)) % 60
    inctimehour = (lasttimehour + (lasttimemin + (delta // 60)) // 60) % 12

    newtime = f"{twodigits(inctimehour)}:{twodigits(inctimemin)}:{twodigits(inctimesecs)}"
    print(newtime)

    # Save new time and polarity to the file
    try:
        with open("lastpulseat.txt", "w+") as file:
            strngtofile = f"{newtime}\t{a}\t{b}"
            file.write(strngtofile)
    except Exception as e:
        print(f"Error writing to file: {e}")

    # Dignified little sleep so we don't upset the clock mechanism
    time.sleep(0.5)
    return

def pulsessince12(timestring):
    breakuptime = timestring.split(":")
    secondssince12 = (int(breakuptime[0]) % 12) * 3600 + int(breakuptime[1]) * 60 + int(breakuptime[2])
    pulses = int(secondssince12 / pulsefrequency)
    return pulses

def calcoffset(timenow):
    try:
        with open('lastpulseat.txt', "r") as f:
            string = f.read().strip().split('\t')

        if len(string) < 3:
            raise ValueError("Insufficient data in lastpulseat.txt")

        lastpulseat = string[0]
        a = string[1].strip().lower() == 'true'
        b = string[2].strip().lower() == 'true'
        lastpulse = pulsessince12(lastpulseat)

    except FileNotFoundError:
        print('File does not exist. Assuming this is the first run')

        try:
            with open('firstruntime.txt', "r") as f:
                initialstring = f.read().strip()
        except FileNotFoundError:
            print("Error: 'firstruntime.txt' is also missing.")
            return None, None, None, None

        lastpulseat = initialstring
        lastpulse = pulsessince12(initialstring)
        a = True  # Adjust based on clock wiring
        b = False

    except Exception as e:
        print(f"Error reading pulse file: {e}")
        return None, None, None, None

    rtcpulsessince12 = pulsessince12(timenow)
    offset = rtcpulsessince12 - lastpulse

    return offset, lastpulseat, a, b


# These are the pins where you toggle polarity to advance the clock
clock2 = Pin(14, Pin.OUT, value=0)
clock1 = Pin(13, Pin.OUT, value=0)

#---------------- MAIN LOGIC
def main():
    led = Pin("LED", Pin.OUT)
    led.on()
    time.sleep(1)
    led.off()

    print("Startup. RTC reads:")
    print(time.gmtime())
    
    print('Connecting to internet and getting time')

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    wifi_failed = False

    if not set_time(worldtimeurl, wlan):
        print("Failed to sync time. Running based on RTC.")
        wifi_failed = True

    # Main loop
    last_wifi_attempt = time.time()
    while True:
        # Get RTC time
        rtctimestring = f"{twodigits(time.localtime()[3])}:{twodigits(time.localtime()[4])}:{twodigits(time.localtime()[5])}"

        # Reset daily at 03:00:00
        if rtctimestring == "03:00:00":
            print("Daily reset triggered.")
            machine.reset()

        # Calculate offset by comparing last pulse time with current RTC
        offset, lasttime, a, b = calcoffset(rtctimestring)
        if offset is None:
            print("Error in calculating offset, skipping this cycle.")
            continue

        # If clock needs adjustment
        if offset < -60 * 60 / pulsefrequency or offset > 0:
            pulsetoclock(lasttime, a, b)

        # Periodically retry WiFi connection if it previously failed
        if wifi_failed and (time.time() - last_wifi_attempt) > wifi_retry_interval:
            print("Attempting to reconnect to WiFi...")
            last_wifi_attempt = time.time()
            if set_time(worldtimeurl, wlan):
                wifi_failed = False
                print("WiFi reconnected and time synced.")
            else:
                print("WiFi reconnection failed, continuing with RTC.")

        time.sleep(0.1)

if __name__ == '__main__':
    main()

