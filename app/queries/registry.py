QUERY_REGISTRY = [
    {
        "query_id": "WEATHER_SINGLE_PATH_TS",
        "description": "Single ensemble path weather time series combining forecast (336 hours) with seasonal data beyond",
        "tables": [
            "weather_forecast_ensemble",
            "weather_seasonal_ensemble"
        ],
        "required_params": [
            "forecast_init",
            "location",
            "variable",
            "ensemble_path"
        ],
        "hardcoded_params": {
            "seasonal_init": "2025-12-04 00:00+00",
            "project_name": "ercot_generic"
        },
        "param_descriptions": {
            "forecast_init": "Timestamptz when the forecast was initialized (e.g., '2026-01-09 12:00')",
            "location": "One of: rto, north_raybn, south_lcra_aen_cps, west, houston",
            "variable": "Weather variable: temp_2m, dew_2m, wind_10m_mps, ghi, wind_100m_mps, ghi_gen, temp_2m_gen",
            "ensemble_path": "Integer 0-999 representing a single probabilistic outcome path"
        },
        "constraints": {
            "project_name": "ercot_generic",
            "ensemble_path_range": [0, 999],
            "locations": ["rto", "north_raybn", "south_lcra_aen_cps", "west", "houston"],
            "variables": ["temp_2m", "dew_2m", "wind_10m_mps", "ghi", "wind_100m_mps", "ghi_gen", "temp_2m_gen"]
        },
        "sql_logic": "Forecast table provides first 336 hours from forecast_init. Seasonal table provides hours beyond that window using its own initialization.",
        "example_questions": [
            "Show me temperature forecast for ERCOT starting Jan 9 2026",
            "Get temp_2m ensemble path 0 from 2026-01-09 12:00 for rto",
            "What is the weather forecast for Houston from Jan 15?"
        ]
    }
]
