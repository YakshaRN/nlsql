# =============================================================================
# Section I: Grid Stress & Scarcity Risk (GSI) - Queries 1-10
# =============================================================================

GSI_PEAK_PROBABILITY_14_DAYS_SQL = """
SELECT valid_datetime, COUNT(*)::float / 1000.0 as probability
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND valid_datetime < CAST(:initialization AS timestamptz) + make_interval(days => :days_ahead)
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
      AND valid_datetime > CAST(:forecast_init AS timestamptz) + interval '336 hours'
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
  AND valid_datetime < CAST(:initialization AS timestamptz) + make_interval(days => :days_ahead)
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

GSI_P50_P90_MONTH_SQL = """
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
      AND valid_datetime > CAST(:forecast_init AS timestamptz) + interval '336 hours'
      AND EXTRACT(MONTH FROM valid_datetime) = :month
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY ensemble_value) as p50_gsi,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY ensemble_value) as p90_gsi
FROM combined_data;
"""

GSI_DURATION_WORST_PERCENT_SQL = """
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

# =============================================================================
# Section II: Load & Temperature Sensitivity - Queries 11-20
# =============================================================================

P01_EXTREME_COLD_TEMP_FORECAST_SQL = """
SELECT valid_datetime, percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as p01_temp
FROM weather_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'temp_2m'
  AND valid_datetime < CAST(:initialization AS timestamptz) + make_interval(days => :days_ahead)
GROUP BY 1 ORDER BY 1;
"""

AVG_LOAD_EXTREME_COLD_SQL = """
SELECT AVG(e.ensemble_value) as avg_load_extreme_cold
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e
  ON w.initialization = e.initialization
  AND w.valid_datetime = e.valid_datetime
  AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = :initialization
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
  AND w.ensemble_value < :temp_threshold
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'load';
"""

ZONE_HIGHEST_FREEZING_PROBABILITY_SQL = """
SELECT location, COUNT(*)::float / (1000.0 * :days_ahead * 24.0) as prob_freezing
FROM weather_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location in ('north_raybn', 'south_lcra_aen_cps', 'houston', 'west')
  AND variable = 'temp_2m'
  AND valid_datetime < CAST(:initialization AS timestamptz) + make_interval(days => :days_ahead)
  AND ensemble_value < :temp_threshold
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

P99_RTO_LOAD_MORNING_PEAK_SQL = """
WITH combined AS (
    SELECT ensemble_value
    FROM energy_forecast_ensemble
    WHERE initialization = :forecast_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND EXTRACT(MONTH FROM valid_datetime AT TIME ZONE 'US/Central') = :month
      AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN :hour_start AND :hour_end
    UNION ALL
    SELECT ensemble_value
    FROM energy_base_ensemble
    WHERE initialization = :seasonal_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND valid_datetime > CAST(:forecast_init AS timestamptz) + interval '336 hours'
      AND EXTRACT(MONTH FROM valid_datetime AT TIME ZONE 'US/Central') = :month
      AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN :hour_start AND :hour_end
)
SELECT percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) FROM combined;
"""

CORRELATION_DEW_LOAD_HOUSTON_SQL = """
SELECT corr(w.ensemble_value, e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = :initialization
  AND w.project_name = 'ercot_generic' AND w.location = :location AND w.variable = 'dew_2m'
  AND e.project_name = 'ercot_generic' AND e.location = :location AND e.variable = 'load';
"""

LOAD_SENSITIVITY_TEMP_DROP_SQL = """
WITH data AS (
    SELECT w.ensemble_value as temp, e.ensemble_value as load
    FROM weather_forecast_ensemble w
    JOIN energy_forecast_ensemble e
      ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
    WHERE w.initialization = :initialization
      AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
      AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'load'
      AND w.ensemble_value < :temp_threshold
)
SELECT regr_slope(load, temp) * -1 as mw_increase_per_degree_drop FROM data;
"""

LOAD_RANGE_P99_P01_DATE_SQL = """
SELECT valid_datetime,
       percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) -
       percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as load_range
FROM energy_base_ensemble
WHERE initialization = :seasonal_init
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'load'
  AND valid_datetime >= CAST(:target_date AS date) AND valid_datetime < CAST(:target_date AS date) + interval '1 day'
GROUP BY 1 ORDER BY 1;
"""

PATHS_NORTH_COLDER_THAN_WEST_SQL = """
SELECT w1.valid_datetime, w1.ensemble_path
FROM weather_forecast_ensemble w1
JOIN weather_forecast_ensemble w2
  ON w1.initialization = w2.initialization AND w1.valid_datetime = w2.valid_datetime AND w1.ensemble_path = w2.ensemble_path
WHERE w1.initialization = :initialization
  AND w1.project_name = 'ercot_generic' AND w1.location = 'north_raybn' AND w1.variable = 'temp_2m'
  AND w2.project_name = 'ercot_generic' AND w2.location = 'west' AND w2.variable = 'temp_2m'
  AND w1.ensemble_value < (w2.ensemble_value - :temp_diff);
"""

PROBABILITY_RTO_LOAD_EXCEEDS_SQL = """
WITH combined AS (
    SELECT ensemble_value FROM energy_forecast_ensemble
    WHERE initialization = :forecast_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
    UNION ALL
    SELECT ensemble_value FROM energy_base_ensemble
    WHERE initialization = :seasonal_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND valid_datetime > CAST(:forecast_init AS timestamptz) + interval '336 hours'
)
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM combined)
FROM combined WHERE ensemble_value > :load_threshold;
"""

MEDIAN_OUTAGE_LOWEST_1_PERCENT_TEMP_SQL = """
WITH p01_temp AS (
    SELECT percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as thresh
    FROM weather_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'temp_2m'
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY e.ensemble_value)
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
JOIN p01_temp t ON 1=1
WHERE w.initialization = :initialization
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
  AND w.ensemble_value < t.thresh
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'nonrenewable_outage_mw';
"""

# =============================================================================
# Section III: Renewables - Queries 21-30
# =============================================================================

PROBABILITY_DUNKELFLAUTE_SQL = """
SELECT valid_datetime, COUNT(*)::float / 1000.0 as prob
FROM (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN variable = 'wind_cap_fac' THEN ensemble_value END) as wind,
           MAX(CASE WHEN variable = 'solar_cap_fac' THEN ensemble_value END) as solar
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable IN ('wind_cap_fac', 'solar_cap_fac')
    GROUP BY 1, 2
) x
WHERE wind < :wind_threshold AND solar < :solar_threshold
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN :daylight_start AND :daylight_end
GROUP BY 1;
"""

P10_LOW_WIND_EVENING_RAMP_SQL = """
SELECT valid_datetime, percentile_disc(0.10) WITHIN GROUP (ORDER BY ensemble_value)
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'wind_gen'
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN :hours_start AND :hours_end
GROUP BY 1;
"""

SOLAR_RAMP_P50_P90_SQL = """
WITH ramps AS (
    SELECT t1.ensemble_path, t1.ensemble_value as val_end, t2.ensemble_value as val_start
    FROM energy_forecast_ensemble t1
    JOIN energy_forecast_ensemble t2
      ON t1.initialization = t2.initialization AND t1.ensemble_path = t2.ensemble_path
      AND t1.valid_datetime = t2.valid_datetime + make_interval(hours => (:hour_end - :hour_start))
    WHERE t1.initialization = :initialization
      AND t1.project_name = 'ercot_generic' AND t1.location = 'rto' AND t1.variable = 'solar_gen'
      AND EXTRACT(HOUR FROM t1.valid_datetime AT TIME ZONE 'US/Central') = :hour_end
      AND t2.project_name = 'ercot_generic' AND t2.location = 'rto' AND t2.variable = 'solar_gen'
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY (val_end - val_start)) as p50_ramp,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY (val_end - val_start)) as p90_ramp
FROM ramps;
"""

PROBABILITY_WEST_WIND_BELOW_CUTIN_SQL = """
SELECT valid_datetime, COUNT(*)::float / 1000.0
FROM weather_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = :location
  AND variable = 'wind_100m_mps'
  AND ensemble_value < :wind_speed_threshold
GROUP BY 1;
"""

SOLAR_GEN_AT_RISK_LOW_GHI_SQL = """
WITH stats AS (
    SELECT valid_datetime, percentile_disc(0.5) WITHIN GROUP (ORDER BY ensemble_value) as p50_ghi
    FROM weather_forecast_ensemble
    WHERE initialization = :initialization AND project_name = 'ercot_generic'
      AND location = 'rto' AND variable = 'ghi'
    GROUP BY 1
)
SELECT w.valid_datetime, AVG(e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN stats s ON w.valid_datetime = s.valid_datetime
JOIN energy_forecast_ensemble e
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = :initialization
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'ghi'
  AND w.ensemble_value < (:ghi_percentage * s.p50_ghi)
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'solar_gen'
GROUP BY 1;
"""

MAX_DOWNWARD_WIND_RAMP_SQL = """
WITH ramps AS (
    SELECT valid_datetime, ensemble_path,
           ensemble_value - LAG(ensemble_value) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as ramp
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'wind_gen'
)
SELECT MIN(ramp) as max_downward_ramp FROM ramps;
"""

PROBABILITY_SOLAR_GEN_DURING_PEAK_GSI_SQL = """
SELECT COUNT(*)::float / 1000.0
FROM (
   SELECT ensemble_path, valid_datetime,
          MAX(CASE WHEN variable = 'gsi' THEN ensemble_value END) as gsi,
          MAX(CASE WHEN variable = 'solar_gen' THEN ensemble_value END) as solar
   FROM energy_forecast_ensemble
   WHERE initialization = :initialization
     AND project_name = 'ercot_generic'
     AND location = 'rto'
     AND variable IN ('gsi', 'solar_gen')
   GROUP BY 1, 2
) x
WHERE gsi > :gsi_threshold AND solar > :solar_threshold;
"""

VARIANCE_WIND_VS_SOLAR_MONTH_SQL = """
SELECT variable, var_pop(ensemble_value)
FROM energy_base_ensemble
WHERE initialization = :seasonal_init
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable IN ('wind_gen', 'solar_gen')
  AND EXTRACT(MONTH FROM valid_datetime) = :month
GROUP BY 1;
"""

PATH_MAX_RENEWABLE_CURTAILMENT_RISK_SQL = """
SELECT ensemble_path, SUM(ensemble_value) as total_potential_gen
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable IN ('wind_gen', 'solar_gen')
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

PROBABILITY_LOW_WIND_CAP_FAC_DURATION_SQL = """
WITH flagged AS (
    SELECT ensemble_path, valid_datetime,
           CASE WHEN ensemble_value < :wind_cap_fac_threshold THEN 1 ELSE 0 END as low_wind
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'wind_cap_fac'
),
grouped AS (
    SELECT ensemble_path, valid_datetime,
           SUM(low_wind) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime ROWS BETWEEN (:duration_hours - 1) PRECEDING AND CURRENT ROW) as rolling_sum
    FROM flagged
)
SELECT COUNT(DISTINCT ensemble_path)::float / 1000.0
FROM grouped WHERE rolling_sum = :duration_hours;
"""

# =============================================================================
# Section IV: Zonal Basis & Constraints - Queries 31-40
# =============================================================================

NORTH_VS_WEST_LOAD_SPREAD_P99_SQL = """
/* Optimization: location IN (...) to scan both zones at once, then conditional agg */
SELECT valid_datetime,
       percentile_disc(0.99) WITHIN GROUP (ORDER BY CASE WHEN location = 'north_raybn' THEN ensemble_value END) -
       percentile_disc(0.99) WITHIN GROUP (ORDER BY CASE WHEN location = 'west' THEN ensemble_value END)
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location IN ('north_raybn', 'west')
  AND variable = 'load'
GROUP BY 1;
"""

WEST_WIND_EXPORT_CONSTRAINT_RISK_SQL = """
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'west' THEN ensemble_value END) as west_wind,
           MAX(CASE WHEN location = 'rto' THEN ensemble_value END) as rto_wind
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location IN ('west', 'rto')
      AND variable = 'wind_gen'
    GROUP BY 1, 2
)
SELECT valid_datetime, COUNT(*)::float / 1000.0 as prob_constraint
FROM pivoted
WHERE west_wind > (:percentage_threshold * rto_wind)
GROUP BY 1;
"""

PROBABILITY_HOUSTON_LOAD_SHARE_SQL = """
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'houston' THEN ensemble_value END) as h_load,
           MAX(CASE WHEN location = 'rto' THEN ensemble_value END) as rto_load
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location IN ('houston', 'rto')
      AND variable = 'load'
    GROUP BY 1, 2
)
SELECT valid_datetime, COUNT(*)::float / 1000.0
FROM pivoted WHERE h_load > (:percentage_threshold * rto_load)
GROUP BY 1;
"""

PATHS_SOUTH_WARMER_THAN_NORTH_SQL = """
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'south_lcra_aen_cps' THEN ensemble_value END) as s_temp,
           MAX(CASE WHEN location = 'north_raybn' THEN ensemble_value END) as n_temp
    FROM weather_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location IN ('south_lcra_aen_cps', 'north_raybn')
      AND variable = 'temp_2m'
    GROUP BY 1, 2
)
SELECT * FROM pivoted WHERE s_temp > (n_temp + :temp_diff);
"""

SOUTH_VS_WEST_WIND_CAP_FAC_P10_SQL = """
SELECT valid_datetime,
       percentile_disc(0.1) WITHIN GROUP (ORDER BY CASE WHEN location = 'south_lcra_aen_cps' THEN ensemble_value END) as south_p10,
       percentile_disc(0.1) WITHIN GROUP (ORDER BY CASE WHEN location = 'west' THEN ensemble_value END) as west_p10
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location IN ('south_lcra_aen_cps', 'west')
  AND variable = 'wind_cap_fac'
GROUP BY 1;
"""

ZONE_HIGHEST_LOAD_VOLATILITY_SQL = """
SELECT location, stddev(ensemble_value)
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location in ('north_raybn', 'south_lcra_aen_cps', 'west', 'houston')
  AND variable = 'load'
GROUP BY 1 ORDER BY 2 DESC;
"""

PROBABILITY_NORTH_ZONE_WINTER_PEAK_SQL = """
SELECT COUNT(*)::float / (1000 * 336)
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'north_raybn'
  AND variable = 'load'
  AND ensemble_value > :peak_threshold;
"""

WEST_SOLAR_AND_WIND_ABOVE_P90_SQL = """
WITH limits AS (
   SELECT valid_datetime,
          percentile_disc(0.9) WITHIN GROUP (ORDER BY CASE WHEN variable='solar_gen' THEN ensemble_value END) as sol_p90,
          percentile_disc(0.9) WITHIN GROUP (ORDER BY CASE WHEN variable='wind_gen' THEN ensemble_value END) as wind_p90
   FROM energy_forecast_ensemble
   WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'west' AND variable in ('solar_gen', 'wind_gen')
   GROUP BY 1
)
SELECT d.valid_datetime, d.ensemble_path
FROM (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN variable = 'solar_gen' THEN ensemble_value END) as s,
           MAX(CASE WHEN variable = 'wind_gen' THEN ensemble_value END) as w
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'west' AND variable in ('solar_gen', 'wind_gen')
    GROUP BY 1, 2
) d
JOIN limits l ON d.valid_datetime = l.valid_datetime
WHERE d.s > l.sol_p90 AND d.w > l.wind_p90;
"""

CORRELATION_SOUTH_GHI_RTO_GSI_SQL = """
SELECT corr(w.ensemble_value, e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = :initialization
  AND w.project_name = 'ercot_generic' AND w.location = 'south_lcra_aen_cps' AND w.variable = 'ghi'
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi';
"""

P50_RENEWABLE_GEN_PER_ZONE_SQL = """
WITH sums AS (
    SELECT valid_datetime, ensemble_path, location, SUM(ensemble_value) as renew_gen
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location in ('north_raybn', 'south_lcra_aen_cps', 'houston', 'west')
      AND variable IN ('wind_gen', 'solar_gen')
    GROUP BY 1, 2, 3
)
SELECT location, valid_datetime, percentile_disc(0.5) WITHIN GROUP (ORDER BY renew_gen)
FROM sums GROUP BY 1, 2;
"""

# =============================================================================
# Section V: Advanced Planning & Tails - Queries 41-50
# =============================================================================

PROBABILITY_NET_DEMAND_EXCEEDS_MONTH_SQL = """
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM energy_base_ensemble
    WHERE initialization = :seasonal_init AND project_name = 'ercot_generic' AND location = 'rto' AND variable='net_demand' AND EXTRACT(MONTH FROM valid_datetime)=:month)
FROM energy_base_ensemble
WHERE initialization = :seasonal_init
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'net_demand'
  AND EXTRACT(MONTH FROM valid_datetime) = :month
  AND ensemble_value > :net_demand_threshold;
"""

NET_DEMAND_UNCERTAINTY_P95_P05_SQL = """
SELECT valid_datetime,
       percentile_disc(0.95) WITHIN GROUP (ORDER BY ensemble_value) -
       percentile_disc(0.05) WITHIN GROUP (ORDER BY ensemble_value) as uncertainty
FROM energy_forecast_ensemble
WHERE initialization = :initialization
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'net_demand'
GROUP BY 1;
"""

AVG_WEST_WIND_TOP_GSI_PATHS_SQL = """
WITH top_gsi AS (
    SELECT valid_datetime, percentile_disc(:gsi_percentile) WITHIN GROUP (ORDER BY ensemble_value) as thresh
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi'
    GROUP BY 1
)
SELECT e.valid_datetime, AVG(w.ensemble_value) as avg_west_wind
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
JOIN top_gsi t ON e.valid_datetime = t.valid_datetime
WHERE e.initialization = :initialization
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi'
  AND e.ensemble_value > t.thresh
  AND w.project_name = 'ercot_generic' AND w.location = 'west' AND w.variable = 'wind_100m_mps'
GROUP BY 1;
"""

LIKELIHOOD_LOW_WIND_HIGH_OUTAGE_SQL = """
WITH stats AS (
   SELECT valid_datetime,
          percentile_disc(0.25) WITHIN GROUP (ORDER BY CASE WHEN variable='wind_gen' THEN ensemble_value END) as low_wind,
          percentile_disc(0.75) WITHIN GROUP (ORDER BY CASE WHEN variable='nonrenewable_outage_mw' THEN ensemble_value END) as high_outage
   FROM energy_forecast_ensemble
   WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'rto'
   GROUP BY 1
)
SELECT x.valid_datetime, COUNT(*)::float/1000.0
FROM (
   SELECT valid_datetime, ensemble_path,
          MAX(CASE WHEN variable='wind_gen' THEN ensemble_value END) as w,
          MAX(CASE WHEN variable='nonrenewable_outage_mw' THEN ensemble_value END) as o
   FROM energy_forecast_ensemble
   WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'rto'
   GROUP BY 1, 2
) x
JOIN stats s ON x.valid_datetime = s.valid_datetime
WHERE x.w < s.low_wind AND x.o > s.high_outage
GROUP BY 1;
"""

AVG_GSI_FREEZING_TRANSITION_SQL = """
SELECT AVG(e.ensemble_value)
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
WHERE e.initialization = :initialization
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi'
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
  AND w.ensemble_value BETWEEN :temp_low AND :temp_high;
"""

DATE_HIGHEST_TAIL_RISK_SQL = """
SELECT valid_date, AVG(spread) AS avg_spread
FROM
(
  SELECT DATE(valid_datetime AT TIME ZONE 'US/Central') AS valid_date,
         percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) -
             percentile_disc(0.50) WITHIN GROUP (ORDER BY ensemble_value) as spread
  FROM energy_forecast_ensemble
  WHERE initialization = :initialization
    AND project_name = 'ercot_generic'
    AND location = 'rto'
    AND variable = 'gsi'
  GROUP BY 1
) x
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

PROBABILITY_ZERO_SOLAR_HIGH_GSI_SQL = """
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM energy_forecast_ensemble WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'rto' AND variable='gsi' AND ensemble_value > :gsi_threshold)
FROM (
   SELECT valid_datetime, ensemble_path,
          MAX(CASE WHEN variable='gsi' THEN ensemble_value END) as gsi,
          MAX(CASE WHEN variable='solar_cap_fac' THEN ensemble_value END) as solar
   FROM energy_forecast_ensemble
   WHERE initialization = :initialization AND project_name = 'ercot_generic' AND location = 'rto'
   GROUP BY 1, 2
) x
WHERE gsi > :gsi_threshold AND solar = 0;
"""

EXPECTED_SHORTFALL_HIGH_GSI_SQL = """
SELECT AVG(nd.ensemble_value)
FROM energy_forecast_ensemble nd
JOIN energy_forecast_ensemble gsi
  ON nd.initialization = gsi.initialization AND nd.ensemble_path=gsi.ensemble_path AND nd.valid_datetime=gsi.valid_datetime
WHERE gsi.initialization = :initialization
  AND gsi.project_name = 'ercot_generic' AND gsi.location = 'rto' AND gsi.variable = 'gsi' AND gsi.ensemble_value >= :gsi_threshold
  AND nd.project_name = 'ercot_generic' AND nd.location = 'rto' AND nd.variable = 'net_demand_plus_outages';
"""

HOURS_HIGH_GSI_PROBABILITY_SQL = """
WITH probs AS (
    SELECT valid_datetime, COUNT(*)::float / 1000.0 as p
    FROM energy_forecast_ensemble
    WHERE initialization = :initialization
      AND project_name = 'ercot_generic'
      AND location = 'rto'
      AND variable = 'gsi'
      AND ensemble_value > :gsi_threshold
    GROUP BY 1
)
SELECT COUNT(*) FROM probs WHERE p > :probability_threshold;
"""

VOLATILITY_PEAK_NET_DEMAND_SQL = """
WITH combined AS (
    SELECT valid_datetime, ensemble_value
    FROM energy_forecast_ensemble
    WHERE initialization = :forecast_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'net_demand'
    UNION ALL
    SELECT valid_datetime, ensemble_value
    FROM energy_base_ensemble
    WHERE initialization = :seasonal_init
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'net_demand'
      AND valid_datetime > CAST(:forecast_init AS timestamptz) + interval '336 hours'
)
SELECT valid_datetime, stddev(ensemble_value) as vol
FROM combined
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;
"""

