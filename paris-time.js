// paris-time.js
// Conversione ora locale di Parigi (Europe/Paris, CET/CEST) verso UTC,
// senza dipendenze esterne. Regola DST europea: da CET (UTC+1) a CEST
// (UTC+2) l'ultima domenica di marzo, viceversa l'ultima domenica di
// ottobre. Verificato contro Python zoneinfo su 60 date del 2026
// (vedi test/verify_paris_time.mjs): corrispondenza esatta.
//
// Semplificazione nota: la transizione reale avviene alle 2:00/3:00
// locali del giorno del cambio; questa funzione usa una granularita'
// giornaliera (l'intero giorno del cambio assume gia' il nuovo
// offset). Per un simulatore di luce solare l'impatto e' trascurabile
// (poche ore, un giorno l'anno, nelle prime ore del mattino).

function lastSundayUTC(year, month1based) {
  // ultimo giorno del mese, a mezzanotte UTC
  const d = new Date(Date.UTC(year, month1based, 0));
  const dow = d.getUTCDay(); // 0 = domenica
  d.setUTCDate(d.getUTCDate() - dow);
  return d;
}

function parisOffsetHours(year, month1based, day) {
  const marchLastSun = lastSundayUTC(year, 3);
  const octLastSun = lastSundayUTC(year, 10);
  const current = new Date(Date.UTC(year, month1based - 1, day));
  const isDst = current >= marchLastSun && current < octLastSun;
  return isDst ? 2 : 1;
}

// hourFloat: ore locali di Parigi come numero decimale (es. 13.5 = 13:30)
function parisLocalToUTC(year, month1based, day, hourFloat) {
  const offset = parisOffsetHours(year, month1based, day);
  const hh = Math.floor(hourFloat);
  const mm = Math.round((hourFloat - hh) * 60);
  return new Date(Date.UTC(year, month1based - 1, day, hh - offset, mm));
}

// Converte (giorno-dell'anno 1-365/366, ora decimale) in {year,month,day}
function dayOfYearToDate(year, dayOfYear) {
  const d = new Date(Date.UTC(year, 0, 1));
  d.setUTCDate(d.getUTCDate() + (dayOfYear - 1));
  return { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate() };
}
