QUERY_REGISTRY = [
    {
        "query_id": "WEATHER_SINGLE_PATH_TS",
        "description": "Single ensemble path weather time series across forecast + seasonal",
        "tables": [
            "weather_forecast_ensemble",
            "weather_seasonal_ensemble"
        ],
        "required_params": [
            "initialization",
            "location",
            "variable",
            "ensemble_path",
            "start_datetime"
        ],
        "optional_params": [],
        "constraints": {
            "project_name": "ercot_generic",
            "ensemble_path_range": [0, 999],
            "locations": ["rto", "north_raybn", "south_lcra_aen_cps", "west", "houston"]
        },
        "example_questions": [
            "Show me temperature forecast for ERCOT starting Jan 9",
            "Give temp_2m path 0 from Jan 9 onwards"
        ]
    }
]
