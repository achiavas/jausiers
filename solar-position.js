// solar-position.js
// Porting 1:1 di solar_position.py — algoritmo NOAA/Meeus per la
// posizione del sole, validato contro l'output Python (vedi
// test/verify_solar.mjs): corrispondenza esatta su azimut e altezza,
// inclusa la correzione per la rifrazione atmosferica vicino
// all'orizzonte.

const SP_RAD = Math.PI / 180;
const SP_DEG = 180 / Math.PI;

// dt: oggetto Date JS (in un istante preciso, qualunque timezone -
// internamente si usa sempre UTC, come fa Python con datetime aware)
function solarPosition(dt, latDeg, lonDeg) {
    const jd = dt.getTime() / 86400000 + 2440587.5;
    const jc = (jd - 2451545.0) / 36525.0;

    const geomMeanLongSun = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360;
    const geomMeanAnomSun = 357.52911 + jc * (35999.05029 - 0.0001537 * jc);
    const eccentEarthOrbit = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc);
    const sunEqOfCtr = Math.sin(SP_RAD * geomMeanAnomSun) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + Math.sin(SP_RAD * 2 * geomMeanAnomSun) * (0.019993 - 0.000101 * jc)
        + Math.sin(SP_RAD * 3 * geomMeanAnomSun) * 0.000289;
    const sunTrueLong = geomMeanLongSun + sunEqOfCtr;
    const sunAppLong = sunTrueLong - 0.00569 - 0.00478 * Math.sin(SP_RAD * (125.04 - 1934.136 * jc));
    const meanObliqEcliptic = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60;
    const obliqCorr = meanObliqEcliptic + 0.00256 * Math.cos(SP_RAD * (125.04 - 1934.136 * jc));
    const sunDeclin = SP_DEG * Math.asin(Math.sin(SP_RAD * obliqCorr) * Math.sin(SP_RAD * sunAppLong));

    const varY = Math.tan(SP_RAD * obliqCorr / 2) * Math.tan(SP_RAD * obliqCorr / 2);
    const eqOfTime = 4 * SP_DEG * (varY * Math.sin(2 * SP_RAD * geomMeanLongSun)
        - 2 * eccentEarthOrbit * Math.sin(SP_RAD * geomMeanAnomSun)
        + 4 * eccentEarthOrbit * varY * Math.sin(SP_RAD * geomMeanAnomSun) * Math.cos(2 * SP_RAD * geomMeanLongSun)
        - 0.5 * varY * varY * Math.sin(4 * SP_RAD * geomMeanLongSun)
        - 1.25 * eccentEarthOrbit * eccentEarthOrbit * Math.sin(2 * SP_RAD * geomMeanAnomSun));

    const utcMinutes = dt.getUTCHours() * 60 + dt.getUTCMinutes() + dt.getUTCSeconds() / 60;
    let trueSolarTime = (utcMinutes + eqOfTime + 4 * lonDeg) % 1440;
    if (trueSolarTime < 0) trueSolarTime += 1440;

    let hourAngle = trueSolarTime / 4 - 180;
    if (hourAngle < -180) hourAngle += 360;

    const latRad = SP_RAD * latDeg;
    const declRad = SP_RAD * sunDeclin;
    const haRad = SP_RAD * hourAngle;

    const cosZenith = Math.sin(latRad) * Math.sin(declRad) + Math.cos(latRad) * Math.cos(declRad) * Math.cos(haRad);
    const zenith = SP_DEG * Math.acos(Math.max(-1, Math.min(1, cosZenith)));
    const altitudeGeom = 90 - zenith;
    let altitude = altitudeGeom;

    let refraction;
    if (altitude > 85.0) {
        refraction = 0.0;
    } else if (altitude > 5.0) {
        const tanAlt = Math.tan(SP_RAD * altitude);
        refraction = 58.1 / tanAlt - 0.07 / Math.pow(tanAlt, 3) + 0.000086 / Math.pow(tanAlt, 5);
    } else if (altitude > -0.575) {
        refraction = 1735.0 + altitude * (-518.2 + altitude * (103.4 + altitude * (-12.79 + altitude * 0.711)));
    } else {
        refraction = -20.772 / Math.tan(SP_RAD * altitude);
    }
    altitude += refraction / 3600.0;

    const azDenom = Math.cos(latRad) * Math.cos(SP_RAD * altitudeGeom);
    let azimuth;
    if (Math.abs(azDenom) < 1e-9) {
        azimuth = 180.0;
    } else {
        let cosAz = (Math.sin(declRad) - Math.sin(latRad) * Math.sin(SP_RAD * altitudeGeom)) / azDenom;
        cosAz = Math.max(-1, Math.min(1, cosAz));
        azimuth = SP_DEG * Math.acos(cosAz);
        if (hourAngle > 0) azimuth = 360 - azimuth;
    }
    azimuth = ((azimuth % 360) + 360) % 360;

    return { azimuthDeg: azimuth, altitudeDeg: altitude, declinationDeg: sunDeclin, isUp: altitude > 0 };
}

// Vettore unitario dal suolo VERSO il sole, in ENU (Est,Nord,Alto)
function sunVectorEnu(sun) {
    const azRad = SP_RAD * sun.azimuthDeg;
    const altRad = SP_RAD * sun.altitudeDeg;
    return [
        Math.sin(azRad) * Math.cos(altRad),
        Math.cos(azRad) * Math.cos(altRad),
        Math.sin(altRad),
    ];
}
