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
  AND valid_datetime > :forecast_init::timestamptz + INTERVAL '336 hours'
  AND project_name = 'ercot_generic'
  AND location = :location
  AND variable = :variable
  AND ensemble_path = :ensemble_path

ORDER BY valid_datetime;
"""

GSI_PEAK_PROBABILITY_14_DAYS_SQL = """
SELECT valid_datetime, COUNT(*)::float / 1000.0 as probability
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND valid_datetime < :initialization::timestamptz + interval ':days_ahead days'
  AND ensemble_value > :gsi_threshold
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

GSI_P99_PEAK_SEASONAL_SQL = """
/* Combined CTE pushes predicates down to the index scan level */
WITH combined_data AS (
    SELECT valid_datetime, ensemble_value
    FROM energy_forecast_ensemble
    WHERE initialization = :forecast_init
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'gsi'
    UNION ALL
    SELECT valid_datetime, ensemble_value
    FROM energy_base_ensemble
    WHERE initialization = :seasonal_init
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'gsi'
      AND valid_datetime > :forecast_init::timestamptz + interval '336 hours'
)
SELECT valid_datetime, percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) as p99_gsi
FROM combined_data
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK_SQL = """
SELECT EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') as hb, COUNT(*)::float / 7000.0 as probability
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND valid_datetime < :initialization::timestamptz + interval ':days_ahead days'
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN :hours_start AND :hours_end
  AND ensemble_value > :gsi_threshold
GROUP BY 1 ORDER BY 1;
"""

GSI_PATHS_ABOVE_THRESHOLD_SQL = """
SELECT DISTINCT ensemble_path
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND ensemble_value > :gsi_threshold;
"""

GSI_P50_P90_FEBRUARY_SQL = """
/* Optimization: Direct filters on both parts of the UNION */
WITH combined_data AS (
    SELECT ensemble_value FROM energy_forecast_ensemble
    WHERE initialization = :forecast_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi'
      AND EXTRACT(MONTH FROM valid_datetime) = :month
    UNION ALL
    SELECT ensemble_value FROM energy_base_ensemble
    WHERE initialization = :seasonal_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi'
      AND valid_datetime > :forecast_init::timestamptz + interval '336 hours'
      AND EXTRACT(MONTH FROM valid_datetime) = :month
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY ensemble_value) as p50_gsi,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY ensemble_value) as p90_gsi
FROM combined_data;
"""

GSI_DURATION_WORST_5_PERCENT_SQL = """
WITH high_stress AS (
    SELECT ensemble_path, valid_datetime,
           CASE WHEN ensemble_value > :gsi_threshold THEN 1 ELSE 0 END as is_stress
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'gsi'
),
runs AS (
    SELECT ensemble_path, sum(is_stress) as total_hours
    FROM high_stress
    GROUP BY ensemble_path
)
SELECT percentile_disc(:percentile) WITHIN GROUP (ORDER BY total_hours) as duration_p95
FROM runs;
"""

AVG_NET_DEMAND_PLUS_OUTAGES_HIGH_GSI_SQL = """
SELECT AVG(nd.ensemble_value)
FROM energy_forecast_ensemble gsi
JOIN energy_forecast_ensemble nd
  ON gsi.initialization = nd.initialization
  AND gsi.valid_datetime = nd.valid_datetime
  AND gsi.ensemble_path = nd.ensemble_path
WHERE gsi.initialization = :initialization
  AND gsi.project_name = 'ercot_generic' AND gsi.location = 'rto' AND gsi.variable = 'gsi'
  AND gsi.ensemble_value > :gsi_threshold
  AND nd.project_name = 'ercot_generic' AND nd.location = 'rto' AND nd.variable = 'net_demand_plus_outages';
"""

LIKELIHOOD_NONRENEWABLE_OUTAGE_COLD_SNAP_SQL = """
WITH cold_snaps AS (
    SELECT valid_datetime, ensemble_path
    FROM weather_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'temp_2m'
      AND ensemble_value < :temp_threshold
)
SELECT COUNT(*)::float / NULLIF((SELECT COUNT(*) FROM cold_snaps), 0)
FROM energy_forecast_ensemble e
JOIN cold_snaps c ON e.valid_datetime = c.valid_datetime AND e.ensemble_path = c.ensemble_path
WHERE e.initialization = :initialization
  AND e.project_name = 'ercot_generic'
  AND e.location = 'rto'
  AND e.variable = 'nonrenewable_outage_mw'
  AND e.ensemble_value > :outage_threshold;
"""

TIGHTEST_HOUR_GSI_SQL = """
SELECT valid_datetime, AVG(ensemble_value) as avg_gsi
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

GSI_PROBABILITY_LASTING_HOURS_SQL = """
WITH flagged AS (
    SELECT ensemble_path, valid_datetime,
           ensemble_value,
           LEAD(ensemble_value, 1) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h1,
           LEAD(ensemble_value, 2) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h2,
           LEAD(ensemble_value, 3) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h3
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'gsi'
)
SELECT COUNT(DISTINCT ensemble_path)::float / 1000.0
FROM flagged
WHERE ensemble_value > :gsi_threshold AND h1 > :gsi_threshold AND h2 > :gsi_threshold AND h3 > :gsi_threshold;
"""

