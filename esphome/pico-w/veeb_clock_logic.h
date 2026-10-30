// Pure logic for driving a polarity-reversing secondary ("slave") clock.
// No Arduino/ESPHome dependencies, so tests/logic_test.cpp builds it on the host.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace veeb_clock {

// One pulse moves the minute hand one minute; the dial repeats every 12 hours.
static const int kDialMinutes = 720;
// The movement cannot run backwards. If the hands are up to this far ahead (the autumn
// clock change, or a slightly fast face), wait for real time to catch up instead of
// pulsing all the way round. Same rule as the veeb firmware.
static const int kMaxAheadMinutes = 60;

inline int dial_minutes(int hour, int minute) { return (hour % 12) * 60 + minute; }

// Pulses needed to bring the face to real time, or 0 when it is right or within
// kMaxAheadMinutes ahead.
inline int pulses_needed(int real_dial, int face_dial) {
  int behind = ((real_dial - face_dial) % kDialMinutes + kDialMinutes) % kDialMinutes;
  return behind >= kDialMinutes - kMaxAheadMinutes ? 0 : behind;
}

// What survives a power cut. Written after every pulse, so `face` is where the hands
// were left and `last_a` is the polarity of the last pulse actually sent.
struct State {
  uint16_t face = 0;      // dial minutes the hands show, 0..719
  bool last_a = false;    // output A level during the last pulse (B is always !A)
  bool running = false;   // auto-advance on
  bool confirmed = false; // Face time has been entered at least once
  uint32_t seq = 0;       // bumped on every save; the newer of two records wins
};

// True if `a` was saved after `b` (seq comparison that survives wrap-around).
inline bool newer(const State &a, const State &b) { return int32_t(a.seq - b.seq) > 0; }

static const uint32_t kMagic = 0x56454542;  // "VEEB"
static const size_t kRecordSize = 16;

inline uint32_t crc32(const uint8_t *p, size_t n) {
  uint32_t c = 0xFFFFFFFFu;
  for (size_t i = 0; i < n; i++) {
    c ^= p[i];
    for (int k = 0; k < 8; k++)
      c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
  }
  return ~c;
}

inline void put32(uint8_t *p, uint32_t v) {
  for (int i = 0; i < 4; i++)
    p[i] = uint8_t(v >> (8 * i));
}
inline uint32_t get32(const uint8_t *p) {
  return uint32_t(p[0]) | uint32_t(p[1]) << 8 | uint32_t(p[2]) << 16 | uint32_t(p[3]) << 24;
}

// Layout: magic(4) seq(4) face(2) last_a(1) flags(1: bit0 running, bit1 confirmed)
// crc32-of-first-12(4).
inline void encode(const State &s, uint8_t out[kRecordSize]) {
  put32(out, kMagic);
  put32(out + 4, s.seq);
  out[8] = uint8_t(s.face);
  out[9] = uint8_t(s.face >> 8);
  out[10] = s.last_a ? 1 : 0;
  out[11] = uint8_t((s.running ? 1 : 0) | (s.confirmed ? 2 : 0));
  put32(out + 12, crc32(out, 12));
}

inline bool decode(const uint8_t in[kRecordSize], State &s) {
  if (get32(in) != kMagic || get32(in + 12) != crc32(in, 12))
    return false;
  uint16_t face = uint16_t(in[8] | in[9] << 8);
  if (face >= kDialMinutes || in[10] > 1 || in[11] > 3)
    return false;
  s.seq = get32(in + 4);
  s.face = face;
  s.last_a = in[10] == 1;
  s.running = (in[11] & 1) != 0;
  s.confirmed = (in[11] & 2) != 0;
  return true;
}

}  // namespace veeb_clock
