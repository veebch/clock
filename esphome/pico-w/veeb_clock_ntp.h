// Runtime-settable SNTP server (the "Time server" text entity).
//
// ESPHome's sntp component takes its servers at compile time. On RP2 it drives lwIP's
// SNTP client directly (sntp_stop / sntp_setservername / sntp_init in its setup()), so
// re-running that sequence from the main loop swaps the server at runtime.
//
// The chosen server goes into BOTH lwIP slots (arduino-pico builds lwIP with
// SNTP_MAX_SERVERS 2). lwIP never moves back to slot 0 once a timeout has moved it to
// slot 1, and sntp_stop()/sntp_init() keep that index, so a different server in slot 1
// would silently become the only one used, and changing slot 0 would then do nothing.
// To use the public pool, set it as the server.
//
// The name is kept in LittleFS next to the clock state, not in a `restore_value` text
// entity: template text saves whatever it is sent before any check can run, and its
// `pattern` is only a hint to the frontend.
#pragma once

#include <cstring>
#include <string>

#include "lwip/apps/sntp.h"
#include "pico/cyw43_arch.h"
#include "esphome/core/log.h"
#include "veeb_clock_store.h"

namespace veeb_clock {

static const char *const NTP_TAG = "veeb_clock.ntp";
static const char *const kNtpFile = "/veeb/ntp.txt";

// lwIP keeps the pointer, not a copy, so the name must outlive the call.
inline char g_ntp_server[64];

// Hostname, IPv4 or IPv6 literal: [A-Za-z0-9.:-], 1..63 chars, no leading/trailing '.'/'-'.
inline bool valid_ntp_server(const std::string &s) {
  if (s.empty() || s.size() >= sizeof(g_ntp_server))
    return false;
  for (char c : s) {
    bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
              c == '.' || c == '-' || c == ':';
    if (!ok)
      return false;
  }
  return s.front() != '.' && s.front() != '-' && s.back() != '.' && s.back() != '-';
}

inline void apply_ntp_server(const char *name) {
  // lwIP's timers and sntp_recv run from the CYW43 background IRQ; arduino-pico wraps
  // udp_*/dns_* in the lwIP lock but not sntp_*. Stop first, then change the buffer
  // lwIP points at.
  cyw43_arch_lwip_begin();
  sntp_stop();
  if (name != g_ntp_server) {
    strncpy(g_ntp_server, name, sizeof(g_ntp_server) - 1);
    g_ntp_server[sizeof(g_ntp_server) - 1] = '\0';
  }
  for (u8_t i = 0; i < SNTP_MAX_SERVERS; i++)
    sntp_setservername(i, g_ntp_server);
  sntp_init();
  cyw43_arch_lwip_end();
  ESP_LOGI(NTP_TAG, "Time server: %s", g_ntp_server);
}

// Last 8 polls answered, as a bit mask (lwIP reachability; both slots hold the same server).
inline uint8_t ntp_reachability() {
  cyw43_arch_lwip_begin();
  uint8_t r = sntp_getreachability(0) | sntp_getreachability(1);
  cyw43_arch_lwip_end();
  return r;
}

// Boot: the saved server if there is a valid one, otherwise the compiled default.
inline void ntp_boot(const char *fallback) {
  std::string saved;
  File f = LittleFS.open(kNtpFile, "r");
  if (f) {
    saved = f.readString().c_str();
    f.close();
    while (!saved.empty() && (saved.back() == '\n' || saved.back() == '\r' || saved.back() == ' '))
      saved.pop_back();
  }
  apply_ntp_server(valid_ntp_server(saved) ? saved.c_str() : fallback);
}

// From the entity: validate, save, apply. Returns false (and changes nothing) if invalid.
inline bool ntp_set(const std::string &name) {
  if (!valid_ntp_server(name)) {
    ESP_LOGW(NTP_TAG, "Rejected time server '%s' (hostname or IP address only)", name.c_str());
    return false;
  }
  File f = LittleFS.open(kNtpFile, "w");
  if (!f || f.print(name.c_str()) != name.size())
    ESP_LOGE(NTP_TAG, "Cannot save %s", kNtpFile);
  if (f)
    f.close();
  apply_ntp_server(name.c_str());
  return true;
}

}  // namespace veeb_clock
