"""
solar_position.py
------------------
Calcolo della posizione del Sole (azimut, altezza) per una data,
un'ora e una posizione geografica date.

Implementazione dell'algoritmo solare NOAA (basato su Meeus / Jean Meeus,
"Astronomical Algorithms" - le stesse formule usate dal NOAA Solar
Calculator). Precisione tipica: qualche centesimo di grado, ampiamente
sufficiente per lo studio di ombre e proiezioni di luce architettoniche.

Convenzioni:
- Azimut solare: gradi da Nord, in senso orario (Nord=0, Est=90,
  Sud=180, Ovest=270). E' la convenzione "da bussola", la stessa
  usata nel resto del progetto (orientamento pareti, ecc.).
- Altezza solare (elevation): gradi sopra l'orizzonte (0 = orizzonte,
  90 = zenit). Se negativa, il Sole e' sotto l'orizzonte.
- Tutti gli angoli interni sono in radianti; le funzioni pubbliche
  accettano/restituiscono gradi per comodita'.

Nessuna dipendenza esterna a parte la libreria standard.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SolarPosition:
    azimuth_deg: float      # da Nord, orario (bussola)
    altitude_deg: float     # sopra l'orizzonte
    declination_deg: float  # declinazione solare (info accessoria)
    hour_angle_deg: float   # angolo orario (info accessoria)

    @property
    def is_up(self) -> bool:
        return self.altitude_deg > 0.0


def _julian_day(dt_utc: datetime) -> float:
    """Giorno Giuliano da un datetime timezone-aware in UTC."""
    y = dt_utc.year
    m = dt_utc.month
    d = (
        dt_utc.day
        + dt_utc.hour / 24.0
        + dt_utc.minute / 1440.0
        + dt_utc.second / 86400.0
    )
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5
    return jd


def solar_position(dt: datetime, lat_deg: float, lon_deg: float) -> SolarPosition:
    """
    Calcola la posizione solare per l'istante `dt` (deve essere
    timezone-aware; viene convertito internamente in UTC) nel punto
    di coordinate `lat_deg`, `lon_deg` (gradi decimali, longitudine
    positiva a Est).

    Basato sulle formule di Meeus riprese dal NOAA Solar Calculator.
    """
    if dt.tzinfo is None:
        raise ValueError("dt deve essere timezone-aware (usa un tzinfo, es. ZoneInfo)")

    dt_utc = dt.astimezone(timezone.utc)
    jd = _julian_day(dt_utc)
    jc = (jd - 2451545.0) / 36525.0  # secolo giuliano

    # Longitudine media del Sole (gradi)
    geom_mean_long_sun = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0

    # Anomalia media del Sole (gradi)
    geom_mean_anom_sun = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)

    # Eccentricita' orbita terrestre
    eccent_earth_orbit = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)

    m_rad = math.radians(geom_mean_anom_sun)
    sun_eq_of_ctr = (
        math.sin(m_rad) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + math.sin(2 * m_rad) * (0.019993 - 0.000101 * jc)
        + math.sin(3 * m_rad) * 0.000289
    )

    sun_true_long = geom_mean_long_sun + sun_eq_of_ctr
    sun_app_long = sun_true_long - 0.00569 - 0.00478 * math.sin(
        math.radians(125.04 - 1934.136 * jc)
    )

    mean_obliq_ecliptic = (
        23.0
        + (26.0 + ((21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813)))) / 60.0) / 60.0
    )
    obliq_corr = mean_obliq_ecliptic + 0.00256 * math.cos(
        math.radians(125.04 - 1934.136 * jc)
    )

    sun_declin = math.degrees(
        math.asin(math.sin(math.radians(obliq_corr)) * math.sin(math.radians(sun_app_long)))
    )

    var_y = math.tan(math.radians(obliq_corr / 2.0)) ** 2
    eq_of_time = 4.0 * math.degrees(
        var_y * math.sin(2.0 * math.radians(geom_mean_long_sun))
        - 2.0 * eccent_earth_orbit * math.sin(m_rad)
        + 4.0 * eccent_earth_orbit * var_y * math.sin(m_rad) * math.cos(2.0 * math.radians(geom_mean_long_sun))
        - 0.5 * var_y * var_y * math.sin(4.0 * math.radians(geom_mean_long_sun))
        - 1.25 * eccent_earth_orbit * eccent_earth_orbit * math.sin(2.0 * m_rad)
    )

    time_utc_min = dt_utc.hour * 60.0 + dt_utc.minute + dt_utc.second / 60.0
    true_solar_time = (time_utc_min + eq_of_time + 4.0 * lon_deg) % 1440.0

    hour_angle = true_solar_time / 4.0 - 180.0
    if hour_angle < -180.0:
        hour_angle += 360.0

    lat_rad = math.radians(lat_deg)
    decl_rad = math.radians(sun_declin)
    ha_rad = math.radians(hour_angle)

    cos_zenith = (
        math.sin(lat_rad) * math.sin(decl_rad)
        + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad)
    )
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith = math.degrees(math.acos(cos_zenith))
    altitude = 90.0 - zenith

    # Correzione per rifrazione atmosferica (approssimazione standard,
    # trascurabile per altezze > ~5 gradi, utile vicino all'orizzonte)
    if altitude > 85.0:
        refraction = 0.0
    elif altitude > 5.0:
        tan_alt = math.tan(math.radians(altitude))
        refraction = 58.1 / tan_alt - 0.07 / tan_alt**3 + 0.000086 / tan_alt**5
    elif altitude > -0.575:
        refraction = (
            1735.0
            + altitude * (-518.2 + altitude * (103.4 + altitude * (-12.79 + altitude * 0.711)))
        )
    else:
        refraction = -20.772 / math.tan(math.radians(altitude))
    altitude += refraction / 3600.0

    # Azimut (da Nord, orario). Uso l'altezza GEOMETRICA (pre-rifrazione,
    # cioe' 90-zenith) per coerenza con l'identita' trigonometrica:
    #   cos(Az) = (sin(decl) - sin(lat)*sin(alt_geom)) / (cos(lat)*cos(alt_geom))
    alt_geom_rad = math.radians(90.0 - zenith)
    az_denom = math.cos(lat_rad) * math.cos(alt_geom_rad)
    if abs(az_denom) < 1e-9:
        azimuth = 180.0
    else:
        cos_az = (
            math.sin(decl_rad) - math.sin(lat_rad) * math.sin(alt_geom_rad)
        ) / az_denom
        cos_az = max(-1.0, min(1.0, cos_az))
        azimuth = math.degrees(math.acos(cos_az))
        if hour_angle > 0.0:
            azimuth = 360.0 - azimuth

    return SolarPosition(
        azimuth_deg=azimuth % 360.0,
        altitude_deg=altitude,
        declination_deg=sun_declin,
        hour_angle_deg=hour_angle,
    )


def sun_vector_enu(pos: SolarPosition) -> tuple[float, float, float]:
    """
    Vettore unitario che punta DAL SUOLO VERSO IL SOLE, in coordinate
    ENU locali (East, North, Up), a partire da una SolarPosition.
    """
    az_rad = math.radians(pos.azimuth_deg)
    alt_rad = math.radians(pos.altitude_deg)
    east = math.sin(az_rad) * math.cos(alt_rad)
    north = math.cos(az_rad) * math.cos(alt_rad)
    up = math.sin(alt_rad)
    return (east, north, up)
