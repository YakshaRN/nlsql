"""
Configuration for table initialization timestamps.

This module defines the correct initialization times for each data table
to ensure queries use the actual data timestamps instead of current date.
"""

# Fixed initialization times for data tables
TABLE_INITIALIZATION_TIMES = {
    "energy_forecast_ensemble": "2026-01-09 12:00",
    "weather_forecast_ensemble": "2026-01-09 12:00",
    "energy_base_ensemble": "2025-12-05 00:00"
}

# Default initialization time for forecast queries (short-term horizon)
DEFAULT_FORECAST_INIT = "2026-01-09 12:00"

# Default initialization time for seasonal/base queries (long-term horizon)
DEFAULT_SEASONAL_INIT = "2025-12-05 00:00"


def get_forecast_init() -> str:
    """
    Get the correct forecast initialization time.
    
    Returns:
        The forecast initialization timestamp as string.
    """
    return DEFAULT_FORECAST_INIT


def get_seasonal_init() -> str:
    """
    Get the correct seasonal/base initialization time.
    
    Returns:
        The seasonal initialization timestamp as string.
    """
    return DEFAULT_SEASONAL_INIT


def get_initialization_for_query(query_id: str) -> dict:
    """
    Get the appropriate initialization times for a specific query.
    
    Args:
        query_id: The query identifier
        
    Returns:
        Dict with initialization parameter names and values.
        
    Examples:
        For queries needing only 'initialization':
            {'initialization': '2026-01-09 12:00'}
            
        For queries needing both 'forecast_init' and 'seasonal_init':
            {
                'forecast_init': '2026-01-09 12:00',
                'seasonal_init': '2025-12-05 00:00'
            }
    """
    # Queries that need both forecast_init and seasonal_init
    queries_with_both = [
        "GSI_P99_PEAK_SEASONAL",
        "GSI_P50_P90_MONTH",
        "P99_RTO_LOAD_MORNING_PEAK",
        "PROBABILITY_RTO_LOAD_EXCEEDS",
        "VOLATILITY_PEAK_NET_DEMAND"
    ]
    
    # Queries that use only seasonal_init
    queries_with_seasonal_only = [
        "LOAD_RANGE_P99_P01_DATE",
        "VARIANCE_WIND_VS_SOLAR_MONTH",
        "PROBABILITY_NET_DEMAND_EXCEEDS_MONTH"
    ]
    
    if query_id in queries_with_both:
        return {
            "forecast_init": DEFAULT_FORECAST_INIT,
            "seasonal_init": DEFAULT_SEASONAL_INIT
        }
    elif query_id in queries_with_seasonal_only:
        return {
            "seasonal_init": DEFAULT_SEASONAL_INIT
        }
    else:
        # Most queries use 'initialization' parameter
        return {
            "initialization": DEFAULT_FORECAST_INIT
        }
