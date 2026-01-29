WEATHER_SINGLE_PATH_TS_SQL = """
SELECT
    valid_datetime,
    ensemble_value
FROM weather_forecast_ensemble
WHERE initialization = :forecast_init
  AND project_name = 'ercot_generic'
  AND location = :location
  AND variable = :variable
  AND ensemble_path = :ensemble_path

UNION ALL

SELECT
    valid_datetime,
    ensemble_value
FROM weather_seasonal_ensemble
WHERE initialization = :seasonal_init
  AND valid_datetime > :forecast_init + INTERVAL '336 hours'
  AND project_name = 'ercot_generic'
  AND location = :location
  AND variable = :variable
  AND ensemble_path = :ensemble_path

ORDER BY valid_datetime;
"""
