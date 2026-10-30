# Raspberry Pi Pico W / ESPHome Port

An ESPHome firmware for the Raspberry Pi Pico W. It replaces `webtime.py` on a DIY Pico W
build, and the stock firmware on the **VEEB Clock Driver** (which is a Pico W). Like the
[ESP32 port](../README.md) it gives you native Home Assistant integration, OTA updates and a
built-in web page. It also lets you set the time server at runtime, and it is built to
survive power cuts at any moment without losing track of the hands.

Same wiring as the Pico version: **GP13 = output A, GP14 = output B** into the H-bridge or
relay pair. Each pulse drives one high and the other low, alternating polarity every pulse.

## Hardware

- A VEEB Clock Driver, or any Raspberry Pi Pico W wired as in the [main README](../../README.md)
- Tested on a VEEB Clock Driver running a secondary clock, with ESPHome 2026.10

## Requirements

- [ESPHome](https://esphome.io/guides/installing_esphome) 2026.10 or later (`rp2:` platform)
- Home Assistant with the ESPHome integration is optional: the web page has every control

## Setup

```bash
git clone https://github.com/veebch/clock
cd clock/esphome/pico-w
cp secrets_example.yaml secrets.yaml   # then fill it in
```

At the top of `pico-w-esphome.yaml`, set `timezone` to your
[IANA time zone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), and if you
like, `ntp_default`, the time server used until you change it on the device.

Build:

```bash
esphome compile pico-w-esphome.yaml
```

**The first install is over USB.** Hold the Pico W's BOOTSEL button while plugging it in,
and copy `.esphome/build/veeb-clock/.pioenvs/veeb-clock/firmware.uf2` onto the `RPI-RP2`
drive that appears. Every later update can go over Wi-Fi:

```bash
esphome run pico-w-esphome.yaml --device veeb-clock.local
```

Note that `esphome upload` sends the *last build* without compiling. Use `run` (or compile
first) so you don't flash a stale image.

> **Back up a VEEB Clock Driver first.** Its shipped firmware isn't published anywhere, so
> once it is overwritten you can't get it back. With the board in BOOTSEL mode,
> [picotool](https://github.com/raspberrypi/picotool) can save the whole 2 MB flash to a
> file and load it again later. The image includes the board's saved Wi-Fi password, so
> keep it private.

## Using it

The first time, and whenever the face is wrong:

1. Set **Face time** to the time the hands show now.
2. Press **Synchronise**. The clock steps forward to the current time (about 0.7 s per
   minute) and then runs on its own.
3. If the hands end up exactly one minute behind after the first pulse, the movement's last
   polarity didn't match. Set Face time back one minute and press Synchronise again.

| Entity | Type | Purpose |
|---|---|---|
| Face time | Time | Where the hands are now. Setting it pauses auto-advance |
| Synchronise | Button | Start auto-advance (only once Face time has been set) |
| Auto-advance | Switch | Pause / resume; survives reboots |
| Advance 1 / 5 minutes | Button | Manual steps, only while paused |
| Time server | Text | Hostname or IP of the NTP server; checked on the device, kept across reboots |
| Pulse width | Number | 100–2000 ms, default 400 ms (the stock firmware's value) |
| Face position | Sensor | The tracked hand position |
| State | Sensor | running / catching up / waiting (face ahead) / paused / waiting for time / … |
| Device time, Time server replies | Diagnostic | Current time; answers to the last 8 hourly NTP polls |
| Board button (GP0) | Diagnostic | The VEEB board's small button, reported only (see below) |

The web page is at `http://veeb-clock.local/`. Daylight saving is automatic: in spring the
clock steps forward 60 minutes, and in autumn it waits an hour (the movement can't run
backwards; like `webtime.py`, it waits whenever the face is up to an hour ahead).

If the hands miss steps, raise **Pulse width**, and check the USB supply: a weak charger
can leave the movement short of current. Once you know the value that works, put it in
`pulse_width_default`, so it isn't lost if the stored settings are ever reset.

## Differences from the ESP32 port

- **Hand position is kept in LittleFS, not ESPHome preferences.** On the RP2040, ESPHome
  stores every preference in a single 4 KB flash sector and erases it on each save that
  changed something. One save per minute would wear that sector out in about 70 days.
  LittleFS spreads the writes and is safe against power loss (`veeb_clock_store.h`).
- **Saved after each pulse, never before.** A power cut mid-pulse leaves the previous
  record, so the next pulse repeats the same polarity, which the movement ignores if it had
  already stepped. The record and the hands therefore agree again, whenever the power went.
- **Time comes from SNTP alone**, from a server you can change at runtime, so no Home
  Assistant is needed. The chosen server fills both of lwIP's server slots: lwIP never moves
  back to the first slot once a timeout has sent it to the second, so a fallback there would
  quietly take over (`veeb_clock_ntp.h`).
- **Nothing moves until Face time has been entered once.** If Face time is set while a
  pulse is energised, it is refused and you are asked to re-read the hands, because there's
  no way to know whether you read them before or after that step.
- **Robustness:**
  - `api: reboot_timeout: 0s`, so the board doesn't reboot when Home Assistant is away. It
    has no battery clock, so a reboot would lose the time.
  - OTA updates stop pulses first, so the coil isn't left energised during an upload.
  - The web page can't take firmware uploads; OTA is encrypted with the API key.
- **The board button (GP0) has no action.** On the VEEB Clock Driver, GP0 is the small
  button, which the stock firmware treats as a reset of the saved Wi-Fi details. Here it is
  only reported. GP0 has only the RP2040's weak internal pull-up, so tying an action to a
  single edge on it isn't safe; give it a long-press trigger if you want one.

## Tests

The dial maths (catch-up, waiting when ahead, the 12:00 wrap, both daylight-saving
changes) and the state record format have a host test:

```bash
make -C tests
```
