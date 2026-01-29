### I. Grid Stress & Scarcity Risk (GSI)

**1. Peak probability of GSI > 0.60 in the next 14 days**

```sql
SELECT valid_datetime, COUNT(*)::float / 1000.0 as probability
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND valid_datetime < '2026-01-09 12:00'::timestamptz + interval '14 days'
  AND ensemble_value > 0.60
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**2. Time of P99 GSI peak over seasonal horizon**

```sql
/* Combined CTE pushes predicates down to the index scan level */
WITH combined_data AS (
    SELECT valid_datetime, ensemble_value 
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'gsi'
    UNION ALL
    SELECT valid_datetime, ensemble_value 
    FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'gsi'
      AND valid_datetime > '2026-01-09 12:00'::timestamptz + interval '336 hours'
)
SELECT valid_datetime, percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) as p99_gsi
FROM combined_data
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**3. Probability of GSI > 0.60 during evening ramp (HB 17-20) next week**

```sql
SELECT EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') as hb, COUNT(*)::float / 7000.0 as probability
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND valid_datetime < '2026-01-09 12:00'::timestamptz + interval '7 days'
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN 17 AND 20
  AND ensemble_value > 0.60
GROUP BY 1 ORDER BY 1;

```

**4. Which ensemble paths show GSI > 0.75**

```sql
SELECT DISTINCT ensemble_path
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'gsi'
  AND ensemble_value > 0.75;

```

**5. Median (P50) vs P90 GSI for February**

```sql
/* Optimization: Direct filters on both parts of the UNION */
WITH combined_data AS (
    SELECT ensemble_value FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi'
      AND EXTRACT(MONTH FROM valid_datetime) = 2
    UNION ALL
    SELECT ensemble_value FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi'
      AND valid_datetime > '2026-01-09 12:00'::timestamptz + interval '336 hours'
      AND EXTRACT(MONTH FROM valid_datetime) = 2
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY ensemble_value) as p50_gsi,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY ensemble_value) as p90_gsi
FROM combined_data;

```

**6. Expected duration of GSI > 0.70 in worst 5% of outcomes**

```sql
WITH high_stress AS (
    SELECT ensemble_path, valid_datetime, 
           CASE WHEN ensemble_value > 0.70 THEN 1 ELSE 0 END as is_stress
    FROM energy_forecast_ensemble
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'gsi'
),
runs AS (
    SELECT ensemble_path, sum(is_stress) as total_hours
    FROM high_stress
    GROUP BY ensemble_path
)
SELECT percentile_disc(0.95) WITHIN GROUP (ORDER BY total_hours) as duration_p95
FROM runs;

```

**7. Average `net_demand_plus_outages` on days with GSI > 0.70**

```sql
SELECT AVG(nd.ensemble_value)
FROM energy_forecast_ensemble gsi
JOIN energy_forecast_ensemble nd 
  ON gsi.initialization = nd.initialization 
  AND gsi.valid_datetime = nd.valid_datetime 
  AND gsi.ensemble_path = nd.ensemble_path
WHERE gsi.initialization = '2026-01-09 12:00'
  AND gsi.project_name = 'ercot_generic' AND gsi.location = 'rto' AND gsi.variable = 'gsi' 
  AND gsi.ensemble_value > 0.70
  AND nd.project_name = 'ercot_generic' AND nd.location = 'rto' AND nd.variable = 'net_demand_plus_outages';

```

**8. Likelihood `nonrenewable_outage_mw` > 15,000 MW during cold snap**

```sql
WITH cold_snaps AS (
    SELECT valid_datetime, ensemble_path 
    FROM weather_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'temp_2m' 
      AND ensemble_value < -5
)
SELECT COUNT(*)::float / NULLIF((SELECT COUNT(*) FROM cold_snaps), 0)
FROM energy_forecast_ensemble e
JOIN cold_snaps c ON e.valid_datetime = c.valid_datetime AND e.ensemble_path = c.ensemble_path
WHERE e.initialization = '2026-01-09 12:00' 
  AND e.project_name = 'ercot_generic' 
  AND e.location = 'rto' 
  AND e.variable = 'nonrenewable_outage_mw' 
  AND e.ensemble_value > 15000;

```

**9. The "Tightest Hour" (Highest average GSI)**

```sql
SELECT valid_datetime, AVG(ensemble_value) as avg_gsi
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'rto' 
  AND variable = 'gsi'
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**10. Probability of GSI > 0.65 lasting > 4 hours**

```sql
WITH flagged AS (
    SELECT ensemble_path, valid_datetime, 
           ensemble_value,
           LEAD(ensemble_value, 1) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h1,
           LEAD(ensemble_value, 2) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h2,
           LEAD(ensemble_value, 3) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as h3
    FROM energy_forecast_ensemble
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'gsi'
)
SELECT COUNT(DISTINCT ensemble_path)::float / 1000.0 
FROM flagged
WHERE ensemble_value > 0.65 AND h1 > 0.65 AND h2 > 0.65 AND h3 > 0.65;

```

---

### II. Load & Temperature Sensitivity

**11. P01 (Extreme Cold) Temp Forecast**

```sql
SELECT valid_datetime, percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as p01_temp
FROM weather_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'rto' 
  AND variable = 'temp_2m'
GROUP BY 1 ORDER BY 1;

```

**12. Average RTO Load when Temp < -5°C**

```sql
SELECT AVG(e.ensemble_value) as avg_load_extreme_cold
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e 
  ON w.initialization = e.initialization 
  AND w.valid_datetime = e.valid_datetime 
  AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = '2026-01-09 12:00' 
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m' 
  AND w.ensemble_value < -5
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'load';

```

**13. Load Zone with highest probability of Temp < 0°C**

```sql
SELECT location, COUNT(*)::float / (1000.0 * 168.0) as prob_freezing
FROM weather_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic'
  AND location in ('north_raybn', 'south_lcra_aen_cps', 'houston', 'west') -- Cannot assume location here, so we scan all load zones
  AND variable = 'temp_2m'
  AND valid_datetime < '2026-01-09 12:00'::timestamptz + interval '7 days'
  AND ensemble_value < 0
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**14. P99 RTO Load for morning peak (HB 07-09) in Feb**

```sql
WITH combined AS (
    SELECT ensemble_value 
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND EXTRACT(MONTH FROM valid_datetime AT TIME ZONE 'US/Central') = 2
      AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN 7 AND 9
    UNION ALL
    SELECT ensemble_value 
    FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND valid_datetime > '2026-01-09 12:00'::timestamptz + interval '336 hours'
      AND EXTRACT(MONTH FROM valid_datetime AT TIME ZONE 'US/Central') = 2
      AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN 7 AND 9
)
SELECT percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) FROM combined;

```

**15. Correlation between `dew_2m` and `load` in Houston**

```sql
SELECT corr(w.ensemble_value, e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e 
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = '2026-01-09 12:00' 
  AND w.project_name = 'ercot_generic' AND w.location = 'houston' AND w.variable = 'dew_2m'
  AND e.project_name = 'ercot_generic' AND e.location = 'houston' AND e.variable = 'load';

```

**16. Load increase per 1°C drop below 5°C (Sensitivity)**

```sql
WITH data AS (
    SELECT w.ensemble_value as temp, e.ensemble_value as load
    FROM weather_forecast_ensemble w
    JOIN energy_forecast_ensemble e 
      ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
    WHERE w.initialization = '2026-01-09 12:00'
      AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
      AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'load'
      AND w.ensemble_value < 5
)
SELECT regr_slope(load, temp) * -1 as mw_increase_per_degree_drop FROM data;

```

**17. Range (P99 - P01) of Load for March 1st**

```sql
SELECT valid_datetime, 
       percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) - 
       percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as load_range
FROM energy_base_ensemble 
WHERE initialization = '2025-12-05 00:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'rto' 
  AND variable = 'load'
  AND valid_datetime >= '2026-03-01 00:00' AND valid_datetime < '2026-03-02 00:00'
GROUP BY 1 ORDER BY 1;

```

**18. Paths where North is 5°C colder than West**

```sql
SELECT w1.valid_datetime, w1.ensemble_path
FROM weather_forecast_ensemble w1
JOIN weather_forecast_ensemble w2 
  ON w1.initialization = w2.initialization AND w1.valid_datetime = w2.valid_datetime AND w1.ensemble_path = w2.ensemble_path
WHERE w1.initialization = '2026-01-09 12:00'
  AND w1.project_name = 'ercot_generic' AND w1.location = 'north_raybn' AND w1.variable = 'temp_2m'
  AND w2.project_name = 'ercot_generic' AND w2.location = 'west' AND w2.variable = 'temp_2m'
  AND w1.ensemble_value < (w2.ensemble_value - 5);

```

**19. Probability of RTO Load > 75,000 MW**

```sql
WITH combined AS (
    SELECT ensemble_value FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
    UNION ALL
    SELECT ensemble_value FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'load'
      AND valid_datetime > '2026-01-09 12:00'::timestamptz + interval '336 hours'
)
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM combined)
FROM combined WHERE ensemble_value > 75000;

```

**20. Median `nonrenewable_outage_mw` during lowest 1% temp**

```sql
WITH p01_temp AS (
    SELECT percentile_disc(0.01) WITHIN GROUP (ORDER BY ensemble_value) as thresh
    FROM weather_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'temp_2m'
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY e.ensemble_value)
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w 
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
JOIN p01_temp t ON 1=1
WHERE w.initialization = '2026-01-09 12:00'
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m' 
  AND w.ensemble_value < t.thresh
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'nonrenewable_outage_mw';

```

---

### III. Renewables

**21. Probability of Dunkelflaute (Wind & Solar < 5%)**

```sql
SELECT valid_datetime, COUNT(*)::float / 1000.0 as prob
FROM (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN variable = 'wind_cap_fac' THEN ensemble_value END) as wind,
           MAX(CASE WHEN variable = 'solar_cap_fac' THEN ensemble_value END) as solar
    FROM energy_forecast_ensemble
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto'
      AND variable IN ('wind_cap_fac', 'solar_cap_fac') -- Optimization: narrow the scan
    GROUP BY 1, 2
) x
WHERE wind < 0.05 AND solar < 0.05 
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN 10 AND 14
GROUP BY 1;

```

**22. P10 Low Wind forecast for evening ramp**

```sql
SELECT valid_datetime, percentile_disc(0.10) WITHIN GROUP (ORDER BY ensemble_value)
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'rto' 
  AND variable = 'wind_gen'
  AND EXTRACT(HOUR FROM valid_datetime AT TIME ZONE 'US/Central') BETWEEN 17 AND 20
GROUP BY 1;

```

**23. Solar ramp (HB 07 to 09) P50 vs P90**

```sql
WITH ramps AS (
    SELECT t1.ensemble_path, t1.ensemble_value as val_09, t2.ensemble_value as val_07
    FROM energy_forecast_ensemble t1
    JOIN energy_forecast_ensemble t2 
      ON t1.initialization = t2.initialization AND t1.ensemble_path = t2.ensemble_path 
      AND t1.valid_datetime = t2.valid_datetime + interval '2 hours'
    WHERE t1.initialization = '2026-01-09 12:00'
      AND t1.project_name = 'ercot_generic' AND t1.location = 'rto' AND t1.variable = 'solar_gen' 
      AND EXTRACT(HOUR FROM t1.valid_datetime AT TIME ZONE 'US/Central') = 9
      AND t2.project_name = 'ercot_generic' AND t2.location = 'rto' AND t2.variable = 'solar_gen'
)
SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY (val_09 - val_07)) as p50_ramp,
       percentile_disc(0.9) WITHIN GROUP (ORDER BY (val_09 - val_07)) as p90_ramp
FROM ramps;

```

**24. Probability of West Wind < 3 m/s**

```sql
SELECT valid_datetime, COUNT(*)::float / 1000.0
FROM weather_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'west' 
  AND variable = 'wind_100m_mps' 
  AND ensemble_value < 3
GROUP BY 1;

```

**25. Solar gen at risk if GHI is 20% below P50**

```sql
WITH stats AS (
    SELECT valid_datetime, percentile_disc(0.5) WITHIN GROUP (ORDER BY ensemble_value) as p50_ghi
    FROM weather_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' 
      AND location = 'rto' AND variable = 'ghi' 
    GROUP BY 1
)
SELECT w.valid_datetime, AVG(e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN stats s ON w.valid_datetime = s.valid_datetime
JOIN energy_forecast_ensemble e 
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = '2026-01-09 12:00' 
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'ghi'
  AND w.ensemble_value < (0.8 * s.p50_ghi)
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'solar_gen'
GROUP BY 1;

```

**26. Max 1-hour downward wind ramp**

```sql
WITH ramps AS (
    SELECT valid_datetime, ensemble_path, 
           ensemble_value - LAG(ensemble_value) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime) as ramp
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'wind_gen'
)
SELECT MIN(ramp) as max_downward_ramp FROM ramps;

```

**27. Probability `solar_gen` > 15k MW during peak GSI**

```sql
SELECT COUNT(*)::float / 1000.0
FROM (
   SELECT ensemble_path, valid_datetime,
          MAX(CASE WHEN variable = 'gsi' THEN ensemble_value END) as gsi,
          MAX(CASE WHEN variable = 'solar_gen' THEN ensemble_value END) as solar
   FROM energy_forecast_ensemble 
   WHERE initialization = '2026-01-09 12:00' 
     AND project_name = 'ercot_generic' 
     AND location = 'rto'
     AND variable IN ('gsi', 'solar_gen')
   GROUP BY 1, 2
) x
WHERE gsi > 0.65 AND solar > 15000;

```

**28. Variance of Wind vs Solar in Feb**

```sql
SELECT variable, var_pop(ensemble_value) 
FROM energy_base_ensemble
WHERE initialization = '2025-12-05 00:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable IN ('wind_gen', 'solar_gen')
  AND EXTRACT(MONTH FROM valid_datetime) = 2
GROUP BY 1;

```

**29. Path with max renewable curtailment risk**

```sql
SELECT ensemble_path, SUM(ensemble_value) as total_potential_gen
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00' 
  AND project_name = 'ercot_generic' 
  AND location = 'rto' 
  AND variable IN ('wind_gen', 'solar_gen')
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**30. Probability `wind_cap_fac` < 15% for > 24 hours**

```sql
WITH flagged AS (
    SELECT ensemble_path, valid_datetime,
           CASE WHEN ensemble_value < 0.15 THEN 1 ELSE 0 END as low_wind
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'wind_cap_fac'
),
grouped AS (
    SELECT ensemble_path, valid_datetime, 
           SUM(low_wind) OVER (PARTITION BY ensemble_path ORDER BY valid_datetime ROWS BETWEEN 23 PRECEDING AND CURRENT ROW) as rolling_sum
    FROM flagged
)
SELECT COUNT(DISTINCT ensemble_path)::float / 1000.0 
FROM grouped WHERE rolling_sum = 24;

```

---

### IV. Zonal Basis & Constraints

**31. North vs West Load Spread (P99)**

```sql
/* Optimization: location IN (...) to scan both zones at once, then conditional agg */
SELECT valid_datetime,
       percentile_disc(0.99) WITHIN GROUP (ORDER BY CASE WHEN location = 'north_raybn' THEN ensemble_value END) - 
       percentile_disc(0.99) WITHIN GROUP (ORDER BY CASE WHEN location = 'west' THEN ensemble_value END)
FROM energy_forecast_ensemble 
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location IN ('north_raybn', 'west')
  AND variable = 'load'
GROUP BY 1;

```

**32. West Wind > 80% of Total RTO Wind**

```sql
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'west' THEN ensemble_value END) as west_wind,
           MAX(CASE WHEN location = 'rto' THEN ensemble_value END) as rto_wind
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location IN ('west', 'rto') 
      AND variable = 'wind_gen'
    GROUP BY 1, 2
)
SELECT valid_datetime, COUNT(*)::float / 1000.0 as prob_constraint
FROM pivoted
WHERE west_wind > (0.8 * rto_wind)
GROUP BY 1;

```

**33. Probability Houston Load > 25% of RTO Load**

```sql
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'houston' THEN ensemble_value END) as h_load,
           MAX(CASE WHEN location = 'rto' THEN ensemble_value END) as rto_load
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic'
      AND location IN ('houston', 'rto')
      AND variable = 'load'
    GROUP BY 1, 2
)
SELECT valid_datetime, COUNT(*)::float / 1000.0
FROM pivoted WHERE h_load > (0.25 * rto_load)
GROUP BY 1;

```

**34. Paths where South is >10°C warmer than North**

```sql
WITH pivoted AS (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN location = 'south_lcra_aen_cps' THEN ensemble_value END) as s_temp,
           MAX(CASE WHEN location = 'north_raybn' THEN ensemble_value END) as n_temp
    FROM weather_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00'
      AND project_name = 'ercot_generic'
      AND location IN ('south_lcra_aen_cps', 'north_raybn')
      AND variable = 'temp_2m'
    GROUP BY 1, 2
)
SELECT * FROM pivoted WHERE s_temp > (n_temp + 10);

```

**35. South vs West Wind Cap Fac in P10 Scenario**

```sql
SELECT valid_datetime, 
       percentile_disc(0.1) WITHIN GROUP (ORDER BY CASE WHEN location = 'south_lcra_aen_cps' THEN ensemble_value END) as south_p10,
       percentile_disc(0.1) WITHIN GROUP (ORDER BY CASE WHEN location = 'west' THEN ensemble_value END) as west_p10
FROM energy_forecast_ensemble 
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location IN ('south_lcra_aen_cps', 'west')
  AND variable = 'wind_cap_fac'
GROUP BY 1;

```

**36. Zone with highest Load Volatility**

```sql
SELECT location, stddev(ensemble_value)
FROM energy_forecast_ensemble 
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location in ('north_raybn', 'south_lcra_aen_cps', 'west', 'houston') 
  AND variable = 'load'
GROUP BY 1 ORDER BY 2 DESC;

```

**37. Probability of North Zone reaching all-time winter peak**

```sql
SELECT COUNT(*)::float / (1000 * 336) 
FROM energy_forecast_ensemble 
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location = 'north_raybn' 
  AND variable = 'load' 
  AND ensemble_value > 25000;

```

**38. West Solar and Wind both > P90**

```sql
WITH limits AS (
   SELECT valid_datetime,
          percentile_disc(0.9) WITHIN GROUP (ORDER BY CASE WHEN variable='solar_gen' THEN ensemble_value END) as sol_p90,
          percentile_disc(0.9) WITHIN GROUP (ORDER BY CASE WHEN variable='wind_gen' THEN ensemble_value END) as wind_p90
   FROM energy_forecast_ensemble 
   WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'west' AND variable in ('solar_gen', 'wind_gen')
   GROUP BY 1
)
SELECT d.valid_datetime, d.ensemble_path
FROM (
    SELECT valid_datetime, ensemble_path,
           MAX(CASE WHEN variable = 'solar_gen' THEN ensemble_value END) as s,
           MAX(CASE WHEN variable = 'wind_gen' THEN ensemble_value END) as w
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'west' AND variable in ('solar_gen', 'wind_gen')
    GROUP BY 1, 2
) d
JOIN limits l ON d.valid_datetime = l.valid_datetime
WHERE d.s > l.sol_p90 AND d.w > l.wind_p90;

```

**39. Correlation South GHI vs RTO GSI**

```sql
SELECT corr(w.ensemble_value, e.ensemble_value)
FROM weather_forecast_ensemble w
JOIN energy_forecast_ensemble e 
  ON w.initialization = e.initialization AND w.valid_datetime = e.valid_datetime AND w.ensemble_path = e.ensemble_path
WHERE w.initialization = '2026-01-09 12:00'
  AND w.project_name = 'ercot_generic' AND w.location = 'south_lcra_aen_cps' AND w.variable = 'ghi'
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi';

```

**40. P50 renewable gen (Wind+Solar) per zone**

```sql
WITH sums AS (
    SELECT valid_datetime, ensemble_path, location, SUM(ensemble_value) as renew_gen
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00'
      AND project_name = 'ercot_generic'
      AND location in ('north_raybn', 'south_lcra_aen_cps', 'houston', 'west')
      AND variable IN ('wind_gen', 'solar_gen')
    GROUP BY 1, 2, 3
)
SELECT location, valid_datetime, percentile_disc(0.5) WITHIN GROUP (ORDER BY renew_gen)
FROM sums GROUP BY 1, 2;

```

---

### V. Advanced Planning & Tails

**41. Probability `net_demand` > 60k MW in March**

```sql
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00' AND project_name = 'ercot_generic' AND location = 'rto' AND variable='net_demand' AND EXTRACT(MONTH FROM valid_datetime)=3)
FROM energy_base_ensemble
WHERE initialization = '2025-12-05 00:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'net_demand' 
  AND EXTRACT(MONTH FROM valid_datetime) = 3 
  AND ensemble_value > 60000;

```

**42. Net Demand Uncertainty (P95 - P05)**

```sql
SELECT valid_datetime,
       percentile_disc(0.95) WITHIN GROUP (ORDER BY ensemble_value) -
       percentile_disc(0.05) WITHIN GROUP (ORDER BY ensemble_value) as uncertainty
FROM energy_forecast_ensemble
WHERE initialization = '2026-01-09 12:00'
  AND project_name = 'ercot_generic'
  AND location = 'rto'
  AND variable = 'net_demand'
GROUP BY 1;

```

**43. West Wind Speed in Top 10% GSI paths**

```sql
WITH top_gsi AS (
    SELECT valid_datetime, percentile_disc(0.9) WITHIN GROUP (ORDER BY ensemble_value) as thresh
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'gsi' 
    GROUP BY 1
)
SELECT e.valid_datetime, AVG(w.ensemble_value) as avg_west_wind
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w 
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
JOIN top_gsi t ON e.valid_datetime = t.valid_datetime
WHERE e.initialization = '2026-01-09 12:00' 
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi' 
  AND e.ensemble_value > t.thresh
  AND w.project_name = 'ercot_generic' AND w.location = 'west' AND w.variable = 'wind_100m_mps'
GROUP BY 1;

```

**44. Likelihood of "Low Wind, High Outage"**

```sql
WITH stats AS (
   SELECT valid_datetime,
          percentile_disc(0.25) WITHIN GROUP (ORDER BY CASE WHEN variable='wind_gen' THEN ensemble_value END) as low_wind,
          percentile_disc(0.75) WITHIN GROUP (ORDER BY CASE WHEN variable='nonrenewable_outage_mw' THEN ensemble_value END) as high_outage
   FROM energy_forecast_ensemble 
   WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'rto' 
   GROUP BY 1
)
SELECT x.valid_datetime, COUNT(*)::float/1000.0
FROM (
   SELECT valid_datetime, ensemble_path,
          MAX(CASE WHEN variable='wind_gen' THEN ensemble_value END) as w,
          MAX(CASE WHEN variable='nonrenewable_outage_mw' THEN ensemble_value END) as o
   FROM energy_forecast_ensemble 
   WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'rto' 
   GROUP BY 1, 2
) x
JOIN stats s ON x.valid_datetime = s.valid_datetime
WHERE x.w < s.low_wind AND x.o > s.high_outage
GROUP BY 1;

```

**45. Average GSI when Temp is between -2°C and 2°C**

```sql
SELECT AVG(e.ensemble_value)
FROM energy_forecast_ensemble e
JOIN weather_forecast_ensemble w 
  ON e.initialization = w.initialization AND e.valid_datetime = w.valid_datetime AND e.ensemble_path = w.ensemble_path
WHERE e.initialization = '2026-01-09 12:00' 
  AND e.project_name = 'ercot_generic' AND e.location = 'rto' AND e.variable = 'gsi'
  AND w.project_name = 'ercot_generic' AND w.location = 'rto' AND w.variable = 'temp_2m'
  AND w.ensemble_value BETWEEN -2 AND 2;

```

**46. Date with highest Tail Risk (P99 - P50 GSI)**

```sql
SELECT valid_date, AVG(spread) AS avg_spread
FROM
(
  SELECT DATE(valid_datetime AT TIME ZONE 'US/Central') AS valid_date, 
         percentile_disc(0.99) WITHIN GROUP (ORDER BY ensemble_value) - 
             percentile_disc(0.50) WITHIN GROUP (ORDER BY ensemble_value) as spread
  FROM energy_forecast_ensemble
  WHERE initialization = '2026-01-09 12:00' 
    AND project_name = 'ercot_generic' 
    AND location = 'rto' 
    AND variable = 'gsi'
  GROUP BY 1
) x
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```

**47. Probability `solar_cap_fac` = 0 when GSI > 0.80**

```sql
SELECT COUNT(*)::float / (SELECT COUNT(*) FROM energy_forecast_ensemble WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'rto' AND variable='gsi' AND ensemble_value > 0.80)
FROM (
   SELECT valid_datetime, ensemble_path,
          MAX(CASE WHEN variable='gsi' THEN ensemble_value END) as gsi,
          MAX(CASE WHEN variable='solar_cap_fac' THEN ensemble_value END) as solar
   FROM energy_forecast_ensemble 
   WHERE initialization = '2026-01-09 12:00' AND project_name = 'ercot_generic' AND location = 'rto' 
   GROUP BY 1, 2
) x
WHERE gsi > 0.80 AND solar = 0;

```

**48. Expected Shortfall for paths where GSI >= 0.65**

```sql
SELECT AVG(nd.ensemble_value)
FROM energy_forecast_ensemble nd
JOIN energy_forecast_ensemble gsi 
  ON nd.initialization = gsi.initialization AND nd.ensemble_path=gsi.ensemble_path AND nd.valid_datetime=gsi.valid_datetime
WHERE gsi.initialization = '2026-01-09 12:00'
  AND gsi.project_name = 'ercot_generic' AND gsi.location = 'rto' AND gsi.variable = 'gsi' AND gsi.ensemble_value >= 0.65
  AND nd.project_name = 'ercot_generic' AND nd.location = 'rto' AND nd.variable = 'net_demand_plus_outages';

```

**49. Hours with >5% probability of GSI > 0.60**

```sql
WITH probs AS (
    SELECT valid_datetime, COUNT(*)::float / 1000.0 as p
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' 
      AND location = 'rto' 
      AND variable = 'gsi' 
      AND ensemble_value > 0.60
    GROUP BY 1
)
SELECT COUNT(*) FROM probs WHERE p > 0.05;

```

**50. Volatility Peak: Hour with highest stddev in `net_demand**`

```sql
WITH combined AS (
    SELECT valid_datetime, ensemble_value 
    FROM energy_forecast_ensemble 
    WHERE initialization = '2026-01-09 12:00' 
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'net_demand'
    UNION ALL
    SELECT valid_datetime, ensemble_value 
    FROM energy_base_ensemble 
    WHERE initialization = '2025-12-05 00:00'
      AND project_name = 'ercot_generic' AND location = 'rto' AND variable = 'net_demand'
      AND valid_datetime > '2026-01-09 12:00'::timestamptz + interval '336 hours'
)
SELECT valid_datetime, stddev(ensemble_value) as vol
FROM combined
GROUP BY 1 ORDER BY 2 DESC LIMIT 1;

```