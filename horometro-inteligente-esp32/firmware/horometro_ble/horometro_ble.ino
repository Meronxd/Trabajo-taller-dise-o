/*
 * HOROMETRO CON INTERRUPTOR - ESP32-S3 / USB COM, 115200 baudios.
 * GPIO4 -- contacto seco del switch -- GND. INPUT_PULLUP.
 * ON = contacto cerrado. Sin alimentacion externa en el switch.
 * Arduino: ESP32S3 Dev Module; USB CDC On Boot = Disabled.
 * DEMO: 1 segundo real en ON = 1 hora simulada.
 */
#include <Arduino.h>
#include <Preferences.h>
#include <esp_timer.h>
#include <esp_random.h>
#include <cstring>
#include <cstdlib>
#include <cerrno>
#include "visor_ble.h"

constexpr uint8_t SWITCH_PIN = 4;
constexpr uint64_t US_PER_HOUR = 1000000ULL; // Tiempo real: 3600000000ULL
constexpr uint32_t DEFAULT_INTERVAL = 10;
constexpr uint64_t DEBOUNCE_US = 40000ULL;
constexpr uint64_t REPORT_US = 250000ULL;
constexpr uint64_t SAVE_US = 5000000ULL;
constexpr uint64_t RETRY_US = 1000000ULL;
constexpr uint32_t MAGIC_V1 = 0x484F5231, MAGIC_V2 = 0x484F5232;

struct LegacyState {
  uint32_t magic, generation;
  uint64_t totalUs, scale;
  uint32_t interval, reserved;
};
struct PersistentState {
  uint32_t magic, generation;
  uint64_t totalUs, scale;
  uint32_t interval, schedule;
  uint64_t baselineIndex, ackIndex;
};
static_assert(sizeof(LegacyState) == 32, "Formato anterior incompatible");
static_assert(sizeof(PersistentState) == 48, "Formato actual incompatible");
static_assert(US_PER_HOUR > 0 && US_PER_HOUR <= 3600000000ULL,
              "Escala fuera de rango");

Preferences prefs;
PersistentState state{};
bool storageOpen = false, storageOk = false, dirty = false;
bool running = false, rawOn = false, initialized = false;
uint64_t previousUs = 0, rawChangedUs = 0, lastReportUs = 0, lastSaveAttemptUs = 0;
char deviceId[20], input[96];
size_t inputLength = 0;
bool inputOverflow = false;

uint64_t intervalUs() { return state.scale * state.interval; }
uint64_t alertIndex() { return state.totalUs / intervalUs(); }

// Guarda todo el registro en una sola clave NVS, sin escribir en cada vuelta.
bool persist(uint64_t now) {
  lastSaveAttemptUs = now;
  storageOk = storageOpen &&
      prefs.putBytes("state2", &state, sizeof(state)) == sizeof(state);
  dirty = !storageOk;
  return storageOk;
}

void report() {
  const uint64_t index = alertIndex();
  publishViewer((double)state.totalUs / state.scale, (double)(index + 1) * state.interval, running, index > state.ackIndex);
  Serial.printf(
    "{\"type\":\"status\",\"protocol\":2,\"device\":\"%s\","
    "\"generation\":%lu,\"schedule\":%lu,\"on\":%s,\"ready\":%s,"
    "\"total_us\":%llu,\"us_per_hour\":%llu,\"interval_hours\":%lu,"
    "\"alert_index\":%llu,\"baseline_index\":%llu,\"ack_index\":%llu,"
    "\"maintenance_due\":%s,\"next_due_us\":%llu,\"storage_ok\":%s}\n",
    deviceId, (unsigned long)state.generation, (unsigned long)state.schedule,
    running ? "true" : "false", initialized ? "true" : "false",
    (unsigned long long)state.totalUs, (unsigned long long)state.scale,
    (unsigned long)state.interval, (unsigned long long)index,
    (unsigned long long)state.baselineIndex, (unsigned long long)state.ackIndex,
    index > state.ackIndex ? "true" : "false",
    (unsigned long long)((index + 1) * intervalUs()),
    storageOk ? "true" : "false");
}

void reply(uint32_t id, bool ok, const char* message) {
  // Todos los mensajes son literales controlados, sin caracteres JSON especiales.
  report();
  Serial.printf("{\"type\":\"reply\",\"id\":%lu,\"ok\":%s,\"message\":\"%s\"}\n",
                (unsigned long)id, ok ? "true" : "false", message);
}

bool parseNumber(const char* text, uint64_t& value) {
  if (!*text) return false;
  for (const char* p = text; *p; ++p) if (*p < '0' || *p > '9') return false;
  errno = 0;
  char* end = nullptr;
  value = strtoull(text, &end, 10);
  return errno != ERANGE && end && !*end;
}

void handleCommand(uint64_t now) {
  char* space = strchr(input, ' ');
  if (!space) return;
  *space = 0;
  uint64_t idValue = 0;
  if (!parseNumber(input, idValue) || idValue > UINT32_MAX) return;
  const uint32_t id = (uint32_t)idValue;
  const char* cmd = space + 1;
  if (!strcmp(cmd, "STATUS")) { reply(id, true, "Estado actualizado"); return; }

  if (!strcmp(cmd, "RESET") || !strncmp(cmd, "INTERVAL ", 9)) {
    if (!initialized || running || rawOn || digitalRead(SWITCH_PIN) == LOW) {
      reply(id, false, "Ponga el interruptor en OFF antes de cambiar o reiniciar");
      return;
    }
  }
  const PersistentState old = state;
  if (!strcmp(cmd, "RESET")) {
    state.totalUs = 0;
    ++state.generation;
    state.baselineIndex = state.ackIndex = 0;
  } else if (!strncmp(cmd, "INTERVAL ", 9)) {
    uint64_t hours = 0;
    if (!parseNumber(cmd + 9, hours) || hours < 1 || hours > 1000000) {
      reply(id, false, "Use un intervalo entero entre 1 y 1000000 horas");
      return;
    }
    if (hours == state.interval) { reply(id, true, "El intervalo ya estaba configurado"); return; }
    if (alertIndex() > state.ackIndex) {
      reply(id, false, "Reconozca primero el aviso de mantenimiento pendiente");
      return;
    }
    state.interval = (uint32_t)hours;
    ++state.schedule;
    state.baselineIndex = state.ackIndex = alertIndex();
  } else if (!strncmp(cmd, "ACK ", 4)) {
    uint64_t index = 0;
    if (!parseNumber(cmd + 4, index) || index > alertIndex()) {
      reply(id, false, "Indice de aviso invalido");
      return;
    }
    if (index <= state.ackIndex) { reply(id, true, "El aviso ya estaba reconocido"); return; }
    state.ackIndex = index;
  } else {
    reply(id, false, "Comando desconocido");
    return;
  }
  if (!persist(now)) {
    state = old; dirty = true;
    reply(id, false, "No se pudo guardar el cambio; no fue aplicado");
    return;
  }
  reply(id, true, "Cambio confirmado y guardado por la ESP32");
}

void setup() {
  Serial.begin(115200);
  pinMode(SWITCH_PIN, INPUT_PULLUP);
  snprintf(deviceId, sizeof(deviceId), "%012llX",
           (unsigned long long)ESP.getEfuseMac());
  storageOpen = prefs.begin("horometro", false);
  bool loaded = storageOpen && prefs.getBytesLength("state2") == sizeof(state)
      && prefs.getBytes("state2", &state, sizeof(state)) == sizeof(state)
      && state.magic == MAGIC_V2 && state.scale == US_PER_HOUR
      && state.interval >= 1 && state.interval <= 1000000;
  if (loaded) {
    loaded = state.baselineIndex <= alertIndex()
          && state.ackIndex >= state.baselineIndex && state.ackIndex <= alertIndex();
  }
  if (!loaded) {
    state = {MAGIC_V2, esp_random(), 0, US_PER_HOUR, DEFAULT_INTERVAL, 0, 0, 0};
    // Migra el contador anterior solamente si no existe una version nueva.
    // Si cambia la escala recompilando, crea una demostracion nueva.
    LegacyState old{};
    if (storageOpen && prefs.getBytesLength("state2") == 0
        && prefs.getBytesLength("state") == sizeof(old)
        && prefs.getBytes("state", &old, sizeof(old)) == sizeof(old)
        && old.magic == MAGIC_V1 && old.scale == US_PER_HOUR
        && old.interval >= 1 && old.interval <= 1000000) {
      state.generation = old.generation; state.totalUs = old.totalUs;
      state.interval = old.interval;
      state.baselineIndex = state.ackIndex = alertIndex();
    }
  }
  startViewer();
  storageOk = loaded;
  previousUs = rawChangedUs = lastReportUs = lastSaveAttemptUs =
      (uint64_t)esp_timer_get_time();
  rawOn = digitalRead(SWITCH_PIN) == LOW;
  if (!loaded) { dirty = true; persist(previousUs); }
  report();
}

void loop() {
  const uint64_t now = (uint64_t)esp_timer_get_time();
  const uint64_t elapsed = now - previousUs;
  previousUs = now;
  const uint64_t oldIndex = alertIndex();
  if (running) { state.totalUs += elapsed; dirty = true; }

  const bool reading = digitalRead(SWITCH_PIN) == LOW;
  if (reading != rawOn) { rawOn = reading; rawChangedUs = now; }
  bool changed = false;
  if ((!initialized || rawOn != running) && now - rawChangedUs >= DEBOUNCE_US) {
    initialized = true;
    changed = running != rawOn;
    running = rawOn;
  }
  const bool threshold = alertIndex() != oldIndex;
  const bool periodic = now - lastSaveAttemptUs >= SAVE_US;
  const bool retry = !storageOk && now - lastSaveAttemptUs >= RETRY_US;
  if (dirty && storageOpen &&
      ((storageOk && (threshold || periodic || (changed && !running))) || retry)) {
    persist(now);
  }

  // Parser sin readStringUntil ni esperas largas, maximo 96 bytes por vuelta.
  for (int i = 0; i < 96 && Serial.available(); ++i) {
    const char c = (char)Serial.read();
    if (c == '\n') {
      input[inputLength] = 0;
      if (!inputOverflow) handleCommand(now);
      inputLength = 0; inputOverflow = false;
    } else if (c != '\r') {
      if (inputLength < sizeof(input) - 1) input[inputLength++] = c;
      else inputOverflow = true;
    }
  }
  if (changed || threshold || now - lastReportUs >= REPORT_US) {
    report(); lastReportUs = now;
  }
  delay(1);
}
