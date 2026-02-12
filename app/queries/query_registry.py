QUERY_REGISTRY = {
    # =========================================================================
    # Section I: Grid Stress & Scarcity Risk (GSI) - Queries 1-10
    # =========================================================================
    "GSI_PEAK_PROBABILITY": {
        "description": "Calculates the peak probability of Grid Stress Index (GSI) exceeding a specified threshold within a given number of days from the forecast initialization.",
        "sql_template_name": "GSI_PEAK_PROBABILITY_SQL",
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
    "GSI_PROBABILITY_EVENING_RAMP": {
        "description": "Calculates the probability of GSI exceeding a threshold during the evening ramp (HB 17-20) for a specified number of days ahead.",
        "sql_template_name": "GSI_PROBABILITY_EVENING_RAMP_SQL",
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
    "GSI_P50_P90_MONTH": {
        "description": "Compares the median (P50) and P90 GSI for a specified month.",
        "sql_template_name": "GSI_P50_P90_MONTH_SQL",
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
    "GSI_DURATION_WORST_PERCENT": {
        "description": "Calculates the expected duration of GSI exceeding a threshold in the worst X% of outcomes.",
        "sql_template_name": "GSI_DURATION_WORST_PERCENT_SQL",
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
    },

    # =========================================================================
    # Section II: Load & Temperature Sensitivity - Queries 11-20
    # =========================================================================
    "P01_EXTREME_COLD_TEMP_FORECAST": {
        "description": "Gets the P01 (Extreme Cold) temperature forecast for the RTO over a specified number of days.",
        "sql_template_name": "P01_EXTREME_COLD_TEMP_FORECAST_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "days_ahead": {
                "type": "int",
                "description": "Number of days ahead to forecast.",
                "required": False,
                "default": 10
            }
        }
    },
    "AVG_LOAD_EXTREME_COLD": {
        "description": "Calculates the average RTO Load when temperature drops below a specified threshold.",
        "sql_template_name": "AVG_LOAD_EXTREME_COLD_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "temp_threshold": {
                "type": "float",
                "description": "The temperature threshold in °C (e.g., -5).",
                "required": False,
                "default": -5
            }
        }
    },
    "ZONE_HIGHEST_FREEZING_PROBABILITY": {
        "description": "Identifies which load zone has the highest probability of seeing temperatures below 0°C next week.",
        "sql_template_name": "ZONE_HIGHEST_FREEZING_PROBABILITY_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "days_ahead": {
                "type": "int",
                "description": "Number of days ahead to consider.",
                "required": False,
                "default": 7
            },
            "temp_threshold": {
                "type": "float",
                "description": "The temperature threshold in °C (e.g., 0).",
                "required": False,
                "default": 0
            }
        }
    },
    "P99_RTO_LOAD_MORNING_PEAK": {
        "description": "Calculates the P99 RTO Load for the morning peak (HB 07-09) for a specified month.",
        "sql_template_name": "P99_RTO_LOAD_MORNING_PEAK_SQL",
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
            },
            "hour_start": {
                "type": "int",
                "description": "Start hour of the morning peak (e.g., 7).",
                "required": False,
                "default": 7
            },
            "hour_end": {
                "type": "int",
                "description": "End hour of the morning peak (e.g., 9).",
                "required": False,
                "default": 9
            }
        }
    },
    "CORRELATION_DEW_LOAD_HOUSTON": {
        "description": "Calculates the correlation between dew point temperature and load in the Houston zone.",
        "sql_template_name": "CORRELATION_DEW_LOAD_HOUSTON_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "location": {
                "type": "text",
                "description": "The location/zone to analyze (e.g., 'houston').",
                "required": False,
                "default": "houston"
            }
        }
    },
    "LOAD_SENSITIVITY_TEMP_DROP": {
        "description": "Calculates how much P99 load increases for every 1°C drop in RTO temperature below a threshold.",
        "sql_template_name": "LOAD_SENSITIVITY_TEMP_DROP_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "temp_threshold": {
                "type": "float",
                "description": "The temperature threshold in °C (e.g., 5).",
                "required": False,
                "default": 5
            }
        }
    },
    "LOAD_RANGE_P99_P01_DATE": {
        "description": "Calculates the range (P99 - P01) of Load uncertainty for a specific date.",
        "sql_template_name": "LOAD_RANGE_P99_P01_DATE_SQL",
        "parameters": {
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "target_date": {
                "type": "date",
                "description": "The target date to analyze (e.g., '2026-03-01').",
                "required": True
            }
        }
    },
    "PATHS_NORTH_COLDER_THAN_WEST": {
        "description": "Identifies paths where North Zone temperature is significantly colder than the West Zone.",
        "sql_template_name": "PATHS_NORTH_COLDER_THAN_WEST_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "temp_diff": {
                "type": "float",
                "description": "The temperature difference threshold in °C (e.g., 5).",
                "required": False,
                "default": 5
            }
        }
    },
    "PROBABILITY_RTO_LOAD_EXCEEDS": {
        "description": "Calculates the probability of RTO Load exceeding a specified threshold.",
        "sql_template_name": "PROBABILITY_RTO_LOAD_EXCEEDS_SQL",
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
            "load_threshold": {
                "type": "float",
                "description": "The load threshold in MW (e.g., 75000).",
                "required": False,
                "default": 75000
            }
        }
    },
    "MEDIAN_OUTAGE_LOWEST_1_PERCENT_TEMP": {
        "description": "Calculates the median nonrenewable outage during the lowest 1% of temperature outcomes.",
        "sql_template_name": "MEDIAN_OUTAGE_LOWEST_1_PERCENT_TEMP_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },

    # =========================================================================
    # Section III: Renewables - Queries 21-30
    # =========================================================================
    "PROBABILITY_DUNKELFLAUTE": {
        "description": "Calculates the probability of Dunkelflaute (Wind Cap Factor < 5% AND Solar Cap Factor < 5%) during daylight hours.",
        "sql_template_name": "PROBABILITY_DUNKELFLAUTE_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "wind_threshold": {
                "type": "float",
                "description": "The wind capacity factor threshold (e.g., 0.05).",
                "required": False,
                "default": 0.05
            },
            "solar_threshold": {
                "type": "float",
                "description": "The solar capacity factor threshold (e.g., 0.05).",
                "required": False,
                "default": 0.05
            },
            "daylight_start": {
                "type": "int",
                "description": "Start hour of daylight (e.g., 10).",
                "required": False,
                "default": 10
            },
            "daylight_end": {
                "type": "int",
                "description": "End hour of daylight (e.g., 14).",
                "required": False,
                "default": 14
            }
        }
    },
    "P10_LOW_WIND_EVENING_RAMP": {
        "description": "Gets the P10 (Low Wind) forecast for wind generation during the evening ramp.",
        "sql_template_name": "P10_LOW_WIND_EVENING_RAMP_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
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
            }
        }
    },
    "SOLAR_RAMP_P50_P90": {
        "description": "Calculates the expected solar ramp (MW change) between specified hours in the P50 vs P90 scenarios.",
        "sql_template_name": "SOLAR_RAMP_P50_P90_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "hour_start": {
                "type": "int",
                "description": "Start hour for the ramp (e.g., 7).",
                "required": False,
                "default": 7
            },
            "hour_end": {
                "type": "int",
                "description": "End hour for the ramp (e.g., 9).",
                "required": False,
                "default": 9
            }
        }
    },
    "PROBABILITY_WEST_WIND_BELOW_CUTIN": {
        "description": "Calculates the probability of wind speed dropping below cut-in speed in the West zone.",
        "sql_template_name": "PROBABILITY_WEST_WIND_BELOW_CUTIN_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "wind_speed_threshold": {
                "type": "float",
                "description": "The wind speed threshold in m/s (e.g., 3 for cut-in speed).",
                "required": False,
                "default": 3
            },
            "location": {
                "type": "text",
                "description": "The location to analyze (e.g., 'west').",
                "required": False,
                "default": "west"
            }
        }
    },
    "SOLAR_GEN_AT_RISK_LOW_GHI": {
        "description": "Calculates how much solar generation is at risk if GHI is below a percentage of the P50 forecast.",
        "sql_template_name": "SOLAR_GEN_AT_RISK_LOW_GHI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "ghi_percentage": {
                "type": "float",
                "description": "The percentage below P50 to consider (e.g., 0.8 for 20% below).",
                "required": False,
                "default": 0.8
            }
        }
    },
    "MAX_DOWNWARD_WIND_RAMP": {
        "description": "Finds the maximum 1-hour downward wind ramp observed in any of the ensemble paths.",
        "sql_template_name": "MAX_DOWNWARD_WIND_RAMP_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "PROBABILITY_SOLAR_GEN_DURING_PEAK_GSI": {
        "description": "Calculates the probability that solar generation exceeds a threshold during peak GSI hours.",
        "sql_template_name": "PROBABILITY_SOLAR_GEN_DURING_PEAK_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "solar_threshold": {
                "type": "float",
                "description": "The solar generation threshold in MW (e.g., 15000).",
                "required": False,
                "default": 15000
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold (e.g., 0.65).",
                "required": False,
                "default": 0.65
            }
        }
    },
    "VARIANCE_WIND_VS_SOLAR_MONTH": {
        "description": "Compares the variance of wind generation vs solar generation for a specified month.",
        "sql_template_name": "VARIANCE_WIND_VS_SOLAR_MONTH_SQL",
        "parameters": {
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "month": {
                "type": "int",
                "description": "The month to analyze (e.g., 2 for February).",
                "required": False,
                "default": 2
            }
        }
    },
    "PATH_MAX_RENEWABLE_CURTAILMENT_RISK": {
        "description": "Identifies the ensemble path with the maximum renewable curtailment risk (highest wind + solar).",
        "sql_template_name": "PATH_MAX_RENEWABLE_CURTAILMENT_RISK_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "PROBABILITY_LOW_WIND_CAP_FAC_DURATION": {
        "description": "Calculates the probability of wind capacity factor staying below a threshold for more than specified consecutive hours.",
        "sql_template_name": "PROBABILITY_LOW_WIND_CAP_FAC_DURATION_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "wind_cap_fac_threshold": {
                "type": "float",
                "description": "The wind capacity factor threshold (e.g., 0.15).",
                "required": False,
                "default": 0.15
            },
            "duration_hours": {
                "type": "int",
                "description": "The number of consecutive hours (e.g., 24).",
                "required": False,
                "default": 24
            }
        }
    },

    # =========================================================================
    # Section IV: Zonal Basis & Constraints - Queries 31-40
    # =========================================================================
    "NORTH_VS_WEST_LOAD_SPREAD_P99": {
        "description": "Calculates the difference between North Zone Load and West Zone Load in the P99 scenario.",
        "sql_template_name": "NORTH_VS_WEST_LOAD_SPREAD_P99_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "WEST_WIND_EXPORT_CONSTRAINT_RISK": {
        "description": "Identifies hours where West Zone wind generation exceeds a percentage of total RTO wind generation (Export Constraint Risk).",
        "sql_template_name": "WEST_WIND_EXPORT_CONSTRAINT_RISK_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "percentage_threshold": {
                "type": "float",
                "description": "The percentage threshold (e.g., 0.80 for 80%).",
                "required": False,
                "default": 0.80
            }
        }
    },
    "PROBABILITY_HOUSTON_LOAD_SHARE": {
        "description": "Calculates the probability that Houston Load exceeds a percentage of total RTO Load.",
        "sql_template_name": "PROBABILITY_HOUSTON_LOAD_SHARE_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "percentage_threshold": {
                "type": "float",
                "description": "The percentage threshold (e.g., 0.25 for 25%).",
                "required": False,
                "default": 0.25
            }
        }
    },
    "PATHS_SOUTH_WARMER_THAN_NORTH": {
        "description": "Finds paths where South Zone temperature is significantly warmer than North Zone.",
        "sql_template_name": "PATHS_SOUTH_WARMER_THAN_NORTH_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "temp_diff": {
                "type": "float",
                "description": "The temperature difference threshold in °C (e.g., 10).",
                "required": False,
                "default": 10
            }
        }
    },
    "SOUTH_VS_WEST_WIND_CAP_FAC_P10": {
        "description": "Compares the wind capacity factor in the South vs the West load zones during the P10 wind scenario.",
        "sql_template_name": "SOUTH_VS_WEST_WIND_CAP_FAC_P10_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "ZONE_HIGHEST_LOAD_VOLATILITY": {
        "description": "Identifies which zone shows the highest volatility (Std Dev) in load over the forecast period.",
        "sql_template_name": "ZONE_HIGHEST_LOAD_VOLATILITY_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "PROBABILITY_NORTH_ZONE_WINTER_PEAK": {
        "description": "Calculates the probability of the North Zone reaching its all-time winter load peak.",
        "sql_template_name": "PROBABILITY_NORTH_ZONE_WINTER_PEAK_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "peak_threshold": {
                "type": "float",
                "description": "The peak load threshold in MW (e.g., 25000).",
                "required": False,
                "default": 25000
            }
        }
    },
    "WEST_SOLAR_AND_WIND_ABOVE_P90": {
        "description": "Identifies hours where West Zone Solar and West Zone Wind are both above their P90 values.",
        "sql_template_name": "WEST_SOLAR_AND_WIND_ABOVE_P90_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "CORRELATION_SOUTH_GHI_RTO_GSI": {
        "description": "Calculates the correlation between South Zone GHI and RTO-wide GSI.",
        "sql_template_name": "CORRELATION_SOUTH_GHI_RTO_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "P50_RENEWABLE_GEN_PER_ZONE": {
        "description": "Calculates the P50 total renewable generation (Wind+Solar) for each individual load zone.",
        "sql_template_name": "P50_RENEWABLE_GEN_PER_ZONE_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },

    # =========================================================================
    # Section V: Advanced Planning & Tails - Queries 41-50
    # =========================================================================
    "PROBABILITY_NET_DEMAND_EXCEEDS_MONTH": {
        "description": "Calculates the probability of net demand exceeding a threshold in a specified month.",
        "sql_template_name": "PROBABILITY_NET_DEMAND_EXCEEDS_MONTH_SQL",
        "parameters": {
            "seasonal_init": {
                "type": "timestamptz",
                "description": "The seasonal initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "net_demand_threshold": {
                "type": "float",
                "description": "The net demand threshold in MW (e.g., 60000).",
                "required": False,
                "default": 60000
            },
            "month": {
                "type": "int",
                "description": "The month to analyze (e.g., 3 for March).",
                "required": False,
                "default": 3
            }
        }
    },
    "NET_DEMAND_UNCERTAINTY_P95_P05": {
        "description": "Calculates the Net Demand Uncertainty: (P95 net_demand - P05 net_demand).",
        "sql_template_name": "NET_DEMAND_UNCERTAINTY_P95_P05_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "AVG_WEST_WIND_TOP_GSI_PATHS": {
        "description": "Calculates the average wind speed in the West zone for the top 10% of GSI paths.",
        "sql_template_name": "AVG_WEST_WIND_TOP_GSI_PATHS_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_percentile": {
                "type": "float",
                "description": "The GSI percentile threshold (e.g., 0.9 for top 10%).",
                "required": False,
                "default": 0.9
            }
        }
    },
    "LIKELIHOOD_LOW_WIND_HIGH_OUTAGE": {
        "description": "Calculates the likelihood of a 'Low Wind, High Outage' event occurring simultaneously.",
        "sql_template_name": "LIKELIHOOD_LOW_WIND_HIGH_OUTAGE_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "AVG_GSI_FREEZING_TRANSITION": {
        "description": "Calculates the average GSI when temperature is between specified thresholds (The 'Freezing Transition').",
        "sql_template_name": "AVG_GSI_FREEZING_TRANSITION_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "temp_low": {
                "type": "float",
                "description": "The lower temperature bound in °C (e.g., -2).",
                "required": False,
                "default": -2
            },
            "temp_high": {
                "type": "float",
                "description": "The upper temperature bound in °C (e.g., 2).",
                "required": False,
                "default": 2
            }
        }
    },
    "DATE_HIGHEST_TAIL_RISK": {
        "description": "Finds the date with the highest Tail Risk (The largest gap between P50 and P99 GSI).",
        "sql_template_name": "DATE_HIGHEST_TAIL_RISK_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            }
        }
    },
    "PROBABILITY_ZERO_SOLAR_HIGH_GSI": {
        "description": "Calculates the probability that solar capacity factor is 0 during an hour where GSI exceeds a threshold.",
        "sql_template_name": "PROBABILITY_ZERO_SOLAR_HIGH_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold (e.g., 0.80).",
                "required": False,
                "default": 0.80
            }
        }
    },
    "EXPECTED_SHORTFALL_HIGH_GSI": {
        "description": "Calculates the expected 'Shortfall' (average net demand plus outages) for paths where GSI exceeds a threshold.",
        "sql_template_name": "EXPECTED_SHORTFALL_HIGH_GSI_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold (e.g., 0.65).",
                "required": False,
                "default": 0.65
            }
        }
    },
    "HOURS_HIGH_GSI_PROBABILITY": {
        "description": "Counts how many hours have greater than a specified probability of GSI exceeding a threshold.",
        "sql_template_name": "HOURS_HIGH_GSI_PROBABILITY_SQL",
        "parameters": {
            "initialization": {
                "type": "timestamptz",
                "description": "The forecast initialization timestamp (e.g., 'YYYY-MM-DD HH:MM').",
                "required": True
            },
            "gsi_threshold": {
                "type": "float",
                "description": "The GSI threshold (e.g., 0.60).",
                "required": False,
                "default": 0.60
            },
            "probability_threshold": {
                "type": "float",
                "description": "The probability threshold (e.g., 0.05 for 5%).",
                "required": False,
                "default": 0.05
            }
        }
    },
    "VOLATILITY_PEAK_NET_DEMAND": {
        "description": "Identifies the 'Volatility Peak': The hour with the highest standard deviation in net demand across all paths.",
        "sql_template_name": "VOLATILITY_PEAK_NET_DEMAND_SQL",
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
    }
}
