QUERY_REGISTRY = {
    "WEATHER_SINGLE_PATH_TS": {
        "description": "Retrieves weather forecast ensemble data for a single path.",
        "sql_template_name": "WEATHER_SINGLE_PATH_TS_SQL",
        "parameters": {
            "forecast_init": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "location": {
                "type": "text",
                "description": "The location (e.g., 'rto', 'north_raybn', 'south_lcra_aen_cps', 'west', 'houston').",
                "required": True
            },
            "variable": {
                "type": "text",
                "description": "The weather variable (e.g., 'temp_2m', 'dew_2m', 'wind_10m_mps', 'ghi', 'wind_100m_mps', 'ghi_gen', 'temp_2m_gen').",
                "required": True
            },
            "ensemble_path": {
                "type": "int",
                "description": "The ensemble path number (0-999).",
                "required": True
            }
        }
    },
    "GSI_PEAK_PROBABILITY_14_DAYS": {
        "description": "Calculates the peak probability of Grid Stress Index (GSI) exceeding a specified threshold within a given number of days from the forecast initialization.",
        "sql_template_name": "GSI_PEAK_PROBABILITY_14_DAYS_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.60).",
                "required": False,
                "default": 0.60
            },
            "days_ahead": {
                "type": "int",
                "description": "The number of days ahead from initialization to consider.",
                "required": False,
                "default": 14
            }
        }
    },
    "GSI_P99_PEAK_SEASONAL": {
        "description": "Determines the valid datetime of the P99 GSI peak over the seasonal horizon.",
        "sql_template_name": "GSI_P99_PEAK_SEASONAL_SQL",
        "parameters": {
            "forecast_init": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK": {
        "description": "Calculates the probability of GSI exceeding a threshold during the evening ramp (HB 17-20) in the next week.",
        "sql_template_name": "GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.60).",
                "required": False,
                "default": 0.60
            },
            "hours_start": {
                "type": "int",
                "description": "Start hour of the evening ramp (e.g., 17).",
                "required": False,
                "default": 17
            },
            "hours_end": {
                "type": "int",
                "description": "End hour of the evening ramp (e.g., 20).",
                "required": False,
                "default": 20
            },
            "days_ahead": {
                "type": "int",
                "description": "Number of days ahead from initialization to consider (e.g., 7).",
                "required": False,
                "default": 7
            }
        }
    },
    "GSI_PATHS_ABOVE_THRESHOLD": {
        "description": "Identifies ensemble paths where GSI exceeds a specified threshold.",
        "sql_template_name": "GSI_PATHS_ABOVE_THRESHOLD_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.75).",
                "required": False,
                "default": 0.75
            }
        }
    },
    "GSI_P50_P90_FEBRUARY": {
        "description": "Compares the median (P50) and P90 GSI for a specified month.",
        "sql_template_name": "GSI_P50_P90_FEBRUARY_SQL",
        "parameters": {
            "forecast_init": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "month": {
                "type": "int",
                "description": "The month to consider (e.g., 2 for February).",
                "required": False,
                "default": 2
            }
        }
    },
    "GSI_DURATION_WORST_5_PERCENT": {
        "description": "Calculates the expected duration of GSI exceeding a threshold in the worst X% of outcomes.",
        "sql_template_name": "GSI_DURATION_WORST_5_PERCENT_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.70).",
                "required": False,
                "default": 0.70
            },
            "percentile": {
                "type": "float",
                "description": "The percentile for worst outcomes (e.g., 0.95 for worst 5%).",
                "required": False,
                "default": 0.95
            }
        }
    },
    "AVG_NET_DEMAND_PLUS_OUTAGES_HIGH_GSI": {
        "description": "Calculates the average net demand plus outages on days when GSI exceeds a specified threshold.",
        "sql_template_name": "AVG_NET_DEMAND_PLUS_OUTAGES_HIGH_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.70).",
                "required": False,
                "default": 0.70
            }
        }
    },
    "LIKELIHOOD_NONRENEWABLE_OUTAGE_COLD_SNAP": {
        "description": "Determines the likelihood of nonrenewable outage exceeding a threshold during a cold snap (temp < -5°C).",
        "sql_template_name": "LIKELIHOOD_NONRENEWABLE_OUTAGE_COLD_SNAP_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "outage_threshold": {
                "type": "float",
                "description": "The nonrenewable outage threshold in MW (e.g., 15000).",
                "required": False,
                "default": 15000
            },
            "temp_threshold": {
                "type": "float",
                "description": "The temperature threshold for a cold snap in °C (e.g., -5).",
                "required": False,
                "default": -5
            }
        }
    },
    "TIGHTEST_HOUR_GSI": {
        "description": "Identifies the hour with the highest average GSI.",
        "sql_template_name": "TIGHTEST_HOUR_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "GSI_PROBABILITY_LASTING_HOURS": {
        "description": "Calculates the probability of GSI exceeding a threshold and lasting for a specified number of consecutive hours.",
        "sql_template_name": "GSI_PROBABILITY_LASTING_HOURS_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold to exceed (e.g., 0.65).",
                "required": False,
                "default": 0.65
            },
            "duration_hours": {
                "type": "int",
                "description": "The number of consecutive hours the GSI must exceed the threshold (e.g., 4).",
                "required": False,
                "default": 4
            }
        }
    }
}
