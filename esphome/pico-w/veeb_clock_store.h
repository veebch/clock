// Persists veeb_clock::State in LittleFS instead of ESPHome preferences.
//
// Why not `globals: restore_value: true`: on RP2040, ESPHome keeps every preference in one
// 4 KB flash sector and erases it on every save that changed something. The hand position
// changes every minute, so that sector would see ~1440 erases a day and pass its ~100k
// rated cycles in about 70 days. LittleFS (already present: OTA stages images in it)
// wear-levels across its free blocks and is power-loss safe.
//
// The file sits in a subdirectory, not the root: littlefs keeps the root directory in the
// superblock pair, and a subdirectory's metadata pair is free to be relocated as it wears.
#pragma once

#include <LittleFS.h>

#include "esphome/core/log.h"
#include "veeb_clock_logic.h"

namespace veeb_clock {

static const char *const STORE_TAG = "veeb_clock.store";
static const char *const kDir = "/veeb";
static const char *const kFile = "/veeb/state.bin";
static const char *const kTmp = "/veeb/state.tmp";

// The live state. Lives here rather than in a YAML `globals:` entry because ESPHome emits
// globals before `includes:`, so a global cannot have this header's type.
inline State g_state;
// A pulse has been energised but not yet recorded (see the pulse script).
inline bool g_in_flight = false;
// Set when a Face time was refused mid-pulse: queued pulses behind it must not energise.
inline bool g_cancel_queued = false;
// An OTA is running: no new pulses (its data phase blocks the loop, so a pulse started
// now would hold the coil energised until the upload ends).
inline bool g_ota_active = false;

inline bool store_begin() {
  if (!LittleFS.begin()) {  // arduino-pico formats an unformatted region here
    ESP_LOGE(STORE_TAG, "LittleFS mount failed");
    return false;
  }
  if (!LittleFS.exists(kDir))
    LittleFS.mkdir(kDir);
  return true;
}

inline bool read_file(const char *path, State &s) {
  File f = LittleFS.open(path, "r");
  if (!f)
    return false;
  uint8_t buf[kRecordSize];
  size_t n = f.read(buf, sizeof(buf));
  f.close();
  return n == sizeof(buf) && decode(buf, s);
}

// Both files can be valid: a power cut between closing state.tmp and the rename leaves the
// newer record in state.tmp. Take whichever was saved last.
inline bool store_load(State &s) {
  State a, b;
  bool ok_a = read_file(kFile, a);
  bool ok_b = read_file(kTmp, b);
  if (ok_b && (!ok_a || newer(b, a))) {
    ESP_LOGW(STORE_TAG, "Using %s (seq %u), newer than %s", kTmp, (unsigned) b.seq, kFile);
    s = b;
    return true;
  }
  if (ok_a)
    s = a;
  return ok_a;
}

// Write the temp file, read it back, then rename it over the real one. littlefs renames
// are atomic, so a power cut leaves either the old record or the new one. The read-back
// matters because File::close() reports no errors, and arduino-pico's open("w") has
// already committed the truncation: a failed write must never be renamed over good data.
inline bool store_save(State &s) {
  State next = s;
  next.seq++;
  uint8_t buf[kRecordSize];
  encode(next, buf);
  File f = LittleFS.open(kTmp, "w");
  if (!f) {
    ESP_LOGE(STORE_TAG, "Cannot open %s", kTmp);
    return false;
  }
  size_t n = f.write(buf, sizeof(buf));
  f.close();
  State check;
  if (n != sizeof(buf) || !read_file(kTmp, check) || check.seq != next.seq) {
    ESP_LOGE(STORE_TAG, "Write of %s did not verify (wrote %u bytes)", kTmp, (unsigned) n);
    return false;
  }
  if (!LittleFS.rename(kTmp, kFile)) {
    // state.tmp is valid and newer, so store_load() still finds it.
    ESP_LOGE(STORE_TAG, "Rename to %s failed", kFile);
    return false;
  }
  s.seq = next.seq;
  return true;
}

}  // namespace veeb_clock
