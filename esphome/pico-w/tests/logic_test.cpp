// Host test for veeb_clock_logic.h:  make -C tests
#include <cassert>
#include <cstdio>

#include "../veeb_clock_logic.h"

using namespace veeb_clock;

static int failures = 0;
#define CHECK(cond)                                              \
  do {                                                           \
    if (!(cond)) {                                               \
      std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
      failures++;                                                \
    }                                                            \
  } while (0)

int main() {
  CHECK(dial_minutes(0, 0) == 0);
  CHECK(dial_minutes(12, 0) == 0);
  CHECK(dial_minutes(23, 59) == 719);
  CHECK(dial_minutes(13, 5) == 65);

  // In step, one behind, many behind.
  CHECK(pulses_needed(100, 100) == 0);
  CHECK(pulses_needed(101, 100) == 1);
  CHECK(pulses_needed(400, 100) == 300);
  // Across 12:00: real 00:01, face 11:59 -> 2 pulses.
  CHECK(pulses_needed(1, 719) == 2);
  // Ahead by 1..60 minutes: wait.
  CHECK(pulses_needed(100, 101) == 0);
  CHECK(pulses_needed(100, 160) == 0);
  // Ahead by 61: cheaper to go round (659 pulses) than to wait 61 min? The veeb rule
  // (and ours) goes round, because "more than an hour ahead" means the face is wrong.
  CHECK(pulses_needed(100, 161) == 659);
  // Largest catch-up: 659 behind.
  CHECK(pulses_needed(659, 0) == 659);
  CHECK(pulses_needed(660, 0) == 0);

  // Spring forward (local 01:59 -> 03:00, an hour skipped): face 01:59, real 03:00 -> 61.
  CHECK(pulses_needed(dial_minutes(3, 0), dial_minutes(1, 59)) == 61);
  // Autumn (local 03:00 -> 02:00, an hour repeated): face 03:00, real 02:xx -> wait...
  for (int m = 0; m < 60; m++)
    CHECK(pulses_needed(dial_minutes(2, m), dial_minutes(3, 0)) == 0);
  // ...and resume at 03:01.
  CHECK(pulses_needed(dial_minutes(3, 1), dial_minutes(3, 0)) == 1);

  // Record round trip and corruption detection.
  State s;
  s.face = 719;
  s.last_a = true;
  s.running = true;
  s.confirmed = true;
  s.seq = 123456;
  uint8_t buf[kRecordSize];
  encode(s, buf);
  State r;
  CHECK(decode(buf, r));
  CHECK(r.face == 719 && r.last_a && r.running && r.confirmed && r.seq == 123456);
  s.running = false;
  encode(s, buf);
  CHECK(decode(buf, r) && !r.running && r.confirmed);
  s.confirmed = false;
  s.running = true;
  encode(s, buf);
  CHECK(decode(buf, r) && r.running && !r.confirmed);
  s.running = false;
  for (size_t i = 0; i < kRecordSize; i++) {
    uint8_t b[kRecordSize];
    std::memcpy(b, buf, kRecordSize);
    b[i] ^= 0x01;
    State x;
    CHECK(!decode(b, x));
  }
  uint8_t erased[kRecordSize];
  std::memset(erased, 0xFF, sizeof(erased));
  CHECK(!decode(erased, r));
  s.face = 720;  // out of range even with a valid CRC
  encode(s, buf);
  CHECK(!decode(buf, r));

  // Newest record wins, including across seq wrap-around.
  State a, b;
  a.seq = 5;
  b.seq = 4;
  CHECK(newer(a, b) && !newer(b, a) && !newer(a, a));
  a.seq = 1;
  b.seq = 0xFFFFFFFFu;
  CHECK(newer(a, b));

  std::printf(failures ? "%d FAILED\n" : "all passed\n", failures);
  return failures ? 1 : 0;
}
