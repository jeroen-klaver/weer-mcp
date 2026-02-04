# Uitbreidingen Plan

## 1. Meer Weerdata
### Huidige tool uitbreiden
- get_current_weather (verbeterde versie van get_temperature)
  - Temperatuur (actueel + gevoelstemperatuur)
  - Luchtvochtigheid (%)
  - Windsnelheid + richting
  - Neerslag (mm)
  - Weersomschrijving

## 2. 5-Daagse Forecast
### Nieuwe tool toevoegen
- get_forecast
  - 5 dagen vooruit
  - Per dag: min/max temperatuur, neerslag kans, weersomschrijving
  - Compact overzicht

## Aanpak
1. Bestaande get_temperature behouden voor backward compatibility
2. Nieuwe tool get_current_weather met uitgebreide info
3. Nieuwe tool get_forecast voor voorspelling
4. OpenMeteo API calls aanpassen voor meer parameters

## OpenMeteo Parameters
Current weather:
- temperature_2m, apparent_temperature
- relative_humidity_2m
- wind_speed_10m, wind_direction_10m
- precipitation
- weather_code (voor beschrijving)

Forecast:
- temperature_2m_max, temperature_2m_min
- precipitation_sum
- weather_code
