backend/
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── api.py                 # HTTP routes
│   ├── models.py              # Pydantic schemas
│   ├── llm/
│   │   ├── bedrock_client.py
│   │   ├── prompts.py
│   │   └── intent_resolver.py
│   ├── queries/
│   │   ├── registry.py
│   │   └── sql_templates.py
│   ├── db/
│   │   ├── connection.py
│   │   └── executor.py
│   ├── context/
│   │   └── memory.py
│   └── utils/
│       └── sql_guard.py
├── requirements.txt
└── README.md


-------QUERY Understanding-------
We have 4 tables-
1. weather_forecast_ensemble
2. weather_seasonal_ensemble
3. energy_forecast_ensemble
4. energy_base_ensemble

Each table has same structure
1. initialization timestamptz,
2. project_name text,
3. location text,
4. variable text,
5. valid_datetime timestamptz,
6. ensemble_path int,
7. ensemble_value float

-- Current Scope --
project_name --> can only be ercot_generic
location --> can only be one out of five
1. ERCOT-wide (rto)
2. North Load Zone (north_raybn)
3. South Load Zone (south_lcra_aen_cps)
4. West Load Zone (west)
5. Houston Load Zone (houston)

-- Other columns --
initialization --> is the time that the forecast began creation.
--> forecast table is filled typically 2 hrs behind Realtime. And is valid for 336 hrs. After that data is moved to other table.
--> for weather_forecast_ensemble moves to weather_seasonal_ensemble & for energy_forecast_ensemble moves to energy_base_ensemble

valid_datetime --> is the time which the forecast is valid for. valid_datetime is at the beginning of the hour forecast applies to.

ensemble_path --> is a number from 0-999 (inclusive). Each path is a single possible outcome.

ensemble_value --> is the value of that.

variable --> are the variables used.
In case of weather ----
1. temp_2m --> population-weighted temperature from 2m above ground level (°C)
2. dew_2m --> population-weighted dewpoint from 2m above ground level (°C)
3. wind_10m_mps --> population-weighted wind speed from 10m above ground level (m/s)
4. ghi --> population-weighted GHI (W/m²) - this stands for Global Horizontal Irradiance — it measures how sunny it is, from 0 (night time) to ~1100 (full sun, low aerosols)
5. wind_100m_mps --> wind farm installed capacity-weighted wind speed from 100m above ground level (m/s)
6. ghi_gen --> solar farm installed capacity-weighted GHI (W/m²)
7. temp_2m_gen --> solar farm installed capacity-weighted temperature from 2m above ground level (°C)

Energy variables (all 5 locations):
load - how much demand is on the grid (MW)wind_gen - how much wind power is generated (MW)solar_gen - how much solar power is generated (MW)net_demand - load - wind_gen - solar_gen — how much demand needs to be met by controllable resources (MW)wind_cap_fac - how much of installed wind capacity is generating (%)solar_cap_fac - how much of installed solar capacity is generating (%)

Energy variables (ERCOT (rto) only):nonrenewable_outage_mw - how much installed nonrenewable capacity is unavailable (MW)nonrenewable_outage_pct - how much installed nonrenewable capacity is unavailable (%)net_demand_plus_outages - net_demand + nonrenewable_outage_mw (MW)gsi - Grid Stress Index (GSI) — a Sunairio proprietary measure that measures how close the grid is to using all of its controllable capacity (0-1)

