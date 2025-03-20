#!/usr/bin/python
# -*- coding: utf-8 -*-

from machine import Pin, RTC, reset
import time
from math import ceil, floor
import network
import secrets
import urequests

# URL for time based on timezone
worldtimeurl = "https://timeapi.io/api/TimeZone/zone?timeZone=Australia/Canberra"
pulsefrequency = 60   # Pulse frequency in seconds
wifi_retry_interval = 600  # 10 minutes between WiFi reconnection attempts

time.sleep(5)

# Helper function to format time as human-readable string
def format_time(t):
    year, month, day, hour, minute, second, *_ = t
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

# Function to print GMT and local time
def print_gmt_and_local_time(worldtimeurl):
    gmt_time = time.gmtime()
    print(f"GMT time: {format_time(gmt_time)} (UTC)")
    try:
        print(f"Fetching local time from: {worldtimeurl}")
        response = urequests.get(worldtimeurl)
        if response.status_code != 200:
            print(f"Failed to fetch time. HTTP Status Code: {response.status_code}")
            return
        parsed = response.json()
        datetime_str = str(parsed["currentLocalTime"])
        timezone_name = parsed["timeZone"]
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
        return False
    ip = wlan.ifconfig()[0]
    netw = secrets.SSID
    print(f'Connected to {netw} on {ip}')
    try:
        print_gmt_and_local_time(worldtimeurl)
        response = urequests.get(worldtimeurl)
        parsed = response.json()
        datetime_str = str(parsed["currentLocalTime"])
        print(f"Received time: {datetime_str}")
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])
        RTC().datetime((year, month, day, 0, hour, minute, second, 0))
        print("RTC updated\n")
    except Exception as e:
        print(f"Error fetching or updating time: {e}")
        return False
    # Keep WiFi connected for the web server (do not disconnect)
    return True

# Utility: ensure numbers are two digits
def twodigits(digit):
    digitstring = str(digit)
    if len(digitstring) == 1:
        digitstring = "0" + digitstring
    return digitstring

# Advance the physical clock by toggling GPIO pins.
# Modified to return the new time and updated polarities.
def pulsetoclock(lasttime, a, b):
    print('PULSE')
    a = not a
    b = not b
    print(f"Polarity: {a}, {b}")
    clock1(int(a))
    clock2(int(b))
    led = Pin("LED", Pin.OUT)
    led.on()
    time.sleep(1)
    clock1(0)
    clock2(0)
    led.off()
    lasttimehour, lasttimemin, lasttimesecs = map(int, lasttime.split(':'))
    delta = lasttimesecs + pulsefrequency
    inctimesecs = delta % 60
    inctimemin = (lasttimemin + (delta // 60)) % 60
    inctimehour = (lasttimehour + (lasttimemin + (delta // 60)) // 60) % 12
    newtime = f"{twodigits(inctimehour)}:{twodigits(inctimemin)}:{twodigits(inctimesecs)}"
    print(newtime)
    try:
        with open("lastpulseat.txt", "w+") as file:
            strngtofile = f"{newtime}\t{a}\t{b}"
            file.write(strngtofile)
    except Exception as e:
        print(f"Error writing to file: {e}")
    time.sleep(0.5)
    return newtime, a, b

def pulsessince12(timestring):
    breakuptime = timestring.split(":")
    secondssince12 = (int(breakuptime[0]) % 12) * 3600 + int(breakuptime[1]) * 60 + int(breakuptime[2])
    pulses = int(secondssince12 / pulsefrequency)
    return pulses

# Revised calcoffset: if lastpulseat.txt doesn't exist, create it immediately from firstruntime.txt.
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
    except OSError:
        print('File does not exist. Assuming this is the first run')
        try:
            with open('firstruntime.txt', "r") as f:
                initialstring = f.read().strip()
        except OSError:
            print("Error: 'firstruntime.txt' is also missing.")
            return None, None, None, None
        lastpulseat = initialstring
        lastpulse = pulsessince12(initialstring)
        a = False
        b = True
        # Write the baseline to lastpulseat.txt so that future calls find it.
        try:
            with open("lastpulseat.txt", "w") as file:
                file.write(f"{initialstring}\t{a}\t{b}")
        except Exception as e:
            print(f"Error writing to file in calcoffset fallback: {e}")
    except Exception as e:
        print(f"Error reading pulse file: {e}")
        return None, None, None, None
    rtcpulsessince12 = pulsessince12(timenow)
    offset = rtcpulsessince12 - lastpulse
    return offset, lastpulseat, a, b

# GPIO pins for clock control
clock2 = Pin(14, Pin.OUT, value=0)
clock1 = Pin(13, Pin.OUT, value=0)

################# Web Server with Microdot ######################
from microdot import Microdot, Response
import uasyncio as asyncio
import os

Response.default_content_type = 'text/html'
app = Microdot()

@app.before_request
def restrict_access(request):
    client_ip = request.client_addr[0]
    if not client_ip.startswith("192.168.50."):
        return Response("Forbidden", status_code=403)

@app.route('/')
def index(request):
    current_time = format_time(time.localtime())
    try:
        with open('firstruntime.txt', 'r') as f:
            base_time = f.read().strip()
    except OSError:
        base_time = "(not set)"
    html = f"""
    <html>
      <head><title>Pico Clock Control Panel</title></head>
      <body>
        <h1>Pico Clock Control Panel</h1>
        <p><strong>Current Time:</strong> {current_time}</p>
        <p><strong>Initial clock time (firstruntime):</strong> {base_time}</p>
        <form action="/sync" method="post">
          <label>Set initial time (HH:MM:SS): 
            <input type="text" name="initial_time" placeholder="HH:MM:SS"/>
          </label>
          <button type="submit">Synchronise clock</button>
        </form>
        <form action="/advance1" method="post" style="display:inline;">
          <button type="submit">+1 minute</button>
        </form>
        <form action="/advance5" method="post" style="display:inline;">
          <button type="submit">+5 minutes</button>
        </form>
      </body>
    </html>
    """
    return html

@app.post('/sync')
def sync_clock(request):
    new_time = request.form.get('initial_time')
    if not new_time:
        return Response("No time provided.", status_code=400)
    try:
        with open('firstruntime.txt', 'w') as f:
            f.write(new_time.strip())
    except Exception as e:
        return Response(f"Error updating firstruntime.txt: {e}", status_code=500)
    try:
        os.remove('lastpulseat.txt')
    except OSError:
        pass
    lt = time.localtime()
    now_str = f"{twodigits(lt[3])}:{twodigits(lt[4])}:{twodigits(lt[5])}"
    offset, lasttime, a, b = calcoffset(now_str)
    if offset is None:
        return Response("Synchronization failed (missing baseline data).", status_code=500)
    if offset > 0:
        for i in range(offset):
            lasttime, a, b = pulsetoclock(lasttime, a, b)
    return index(request)

@app.post('/advance1')
def advance_one(request):
    try:
        with open('lastpulseat.txt', 'r') as f:
            t, a_str, b_str = f.read().strip().split('\t')
            lasttime = t
            a = (a_str.lower() == 'true')
            b = (b_str.lower() == 'true')
    except OSError:
        try:
            with open('firstruntime.txt', 'r') as f:
                lasttime = f.read().strip()
                a = False
                b = True
        except OSError:
            return Response("No baseline time available to advance.", status_code=500)
    lasttime, a, b = pulsetoclock(lasttime, a, b)
    return index(request)

@app.post('/advance5')
def advance_five(request):
    for i in range(5):
        try:
            with open('lastpulseat.txt', 'r') as f:
                t, a_str, b_str = f.read().strip().split('\t')
                lasttime = t
                a = (a_str.lower() == 'true')
                b = (b_str.lower() == 'true')
        except OSError:
            try:
                with open('firstruntime.txt', 'r') as f:
                    lasttime = f.read().strip()
                    a = False
                    b = True
            except OSError:
                return Response("No baseline time available to advance.", status_code=500)
        lasttime, a, b = pulsetoclock(lasttime, a, b)
    return index(request)

################# Asynchronous Clock Loop ######################
async def clock_loop():
    global wifi_failed, last_wifi_attempt
    while True:
        rtctimestring = f"{twodigits(time.localtime()[3])}:{twodigits(time.localtime()[4])}:{twodigits(time.localtime()[5])}"
        if rtctimestring == "03:00:00":
            reset()
        offset, lasttime, a, b = calcoffset(rtctimestring)
        if offset is None:
            print("Error in calculating offset, skipping this cycle.")
        else:
            if offset < - (60 * 60 / pulsefrequency) or offset > 0:
                pulsetoclock(lasttime, a, b)
        if wifi_failed and (time.time() - last_wifi_attempt) > wifi_retry_interval:
            print("Attempting to reconnect to WiFi...")
            last_wifi_attempt = time.time()
            if set_time(worldtimeurl, wlan):
                wifi_failed = False
                print("WiFi reconnected and time synced.")
            else:
                print("WiFi reconnection failed, continuing with RTC.")
        await asyncio.sleep(0.1)

################# MAIN LOGIC ######################
def main():
    led = Pin("LED", Pin.OUT)
    led.on()
    time.sleep(1)
    led.off()
    print("Startup. RTC reads:")
    print(time.gmtime())
    print('Connecting to internet and getting time')
    global wlan, wifi_failed, last_wifi_attempt
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wifi_failed = False
    if not set_time(worldtimeurl, wlan):
        print("Failed to sync time. Running based on RTC.")
        wifi_failed = True
    last_wifi_attempt = time.time()
    async def main_async():
        server_task = asyncio.create_task(app.start_server(host="0.0.0.0", port=80))
        clock_task = asyncio.create_task(clock_loop())
        await asyncio.gather(server_task, clock_task)
    asyncio.run(main_async())

if __name__ == '__main__':
    main()
