# ESP32 / ESPHome Port

An alternative to the Pico W `webtime.py` version, using an [ESP32](https://www.espressif.com/en/products/socs/esp32) and [ESPHome](https://esphome.io/). This gives you native [Home Assistant](https://www.home-assistant.io/) integration, OTA updates, and a built-in web interface — with no DS3231 RTC module required.

The H-bridge or relay wiring is identical to the Pico version. Only the microcontroller changes.

## Hardware

- Any ESP32 DevKit board with an ESP32-WROOM-32 or equivalent module (the standard 38-pin DevKit C works well)
- H-bridge ([L298N](https://www.reichelt.com/ch/de/entwicklerboards-motodriver2-l298n-debo-motodriver2-p202829.html?PROVID=2808)) or [2-channel SPDT relay](https://wiki.seeedstudio.com/Grove-2-Channel_SPDT_Relay/), wired as described in the main README
- Step-up module or DC supply to drive the clock mechanism at the correct voltage

## Pin assignments

| GPIO | Function |
|------|----------|
| 2    | Onboard LED (status indicator) |
| 13   | Clock output A (H-bridge / relay in1) |
| 14   | Clock output B (H-bridge / relay in2) |

GPIO 13 and 14 connect to the H-bridge or relay in exactly the same way as the Pico version.

## Requirements

- [ESPHome](https://esphome.io/guides/installing_esphome) 2024.1 or later
- Home Assistant with the ESPHome integration (for time sync and entity control)

## Setup

Clone the repository and navigate to the `esphome` folder:

```bash
git clone https://github.com/veebch/clock
cd clock/esphome
```

Copy the secrets example and fill in your values:

```bash
cp secrets_example.yaml secrets.yaml
```

Edit `secrets.yaml`:

```yaml
wifi_ssid: "YourNetworkName"
wifi_password: "YourWiFiPassword"
api_encryption_key: "base64_32_byte_key_here"
ota_password: "yourpassword"
```

To generate a valid `api_encryption_key`:

```bash
python3 -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

Open `esp32-esphome.yaml` and set the two substitutions at the top to match your setup:

```yaml
substitutions:
  pulse_frequency: "60"   # seconds — most clocks use 60, some use 30 or 1
  timezone: "Europe/Berlin"
```

Flash via USB the first time:

```bash
esphome run esp32-esphome.yaml
```

All subsequent updates can be done OTA from the ESPHome dashboard.

## Home Assistant

Once adopted by Home Assistant, the device exposes:

| Entity | Type | Purpose |
|--------|------|---------|
| Clock face position | Sensor | Current tracked face time (HH:MM) |
| Clock face hour | Number | Set the hour currently showing on the physical face |
| Clock face minute | Number | Set the minute currently showing on the physical face |
| Synchronise | Button | Confirm face time and resume auto-advance |
| Advance 1 minute | Button | Step the clock forward one minute manually |
| Advance 5 minutes | Button | Step the clock forward five minutes manually |
| Pause auto-advance | Switch | Pause the clock loop without synchronising |

The built-in web interface is also available at `http://secondary-clock.local/`.

## Synchronising the clock face

When first setting up, or after a long power outage, the physical clock face may not show the correct time. To synchronise:

1. In Home Assistant, set **Clock face hour** and **Clock face minute** to match what the physical face currently shows. Moving either slider automatically pauses auto-advance.
2. Press **Synchronise**. The pause clears and the clock begins advancing automatically to catch up to real time.

Clock face position and polarity state are stored in ESP32 NVS flash and survive reboots.

## Differences from the Pico W version

- No `firstruntime.txt` or `lastpulseat.txt` — state is held in NVS flash
- No Microdot dependency — the web server is provided by ESPHome natively
- No DS3231 RTC module — time comes from Home Assistant, with SNTP as fallback
- OTA firmware updates via the ESPHome dashboard