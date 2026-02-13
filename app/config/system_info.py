"""
System information configuration for meta-queries.

This module centralizes all system information that can be queried by users.
Update this file to reflect system capabilities - no code changes needed.
"""

# System configuration - Update these as your system evolves
SYSTEM_INFO = {
    "project": {
        "name": "ercot_generic",
        "description": "ERCOT Texas grid",
        "details": {
            "zones": 5,
            "ensemble_paths": 1000,
            "forecast_horizon": "336 hours (14 days)",
            "seasonal_outlook": True,
        }
    },
    
    "locations": [
        {"id": "rto", "name": "RTO", "description": "ERCOT-wide (entire grid)"},
        {"id": "north_raybn", "name": "North", "description": "North Load Zone"},
        {"id": "south_lcra_aen_cps", "name": "South", "description": "South Load Zone"},
        {"id": "west", "name": "West", "description": "West Load Zone"},
        {"id": "houston", "name": "Houston", "description": "Houston Load Zone"},
    ],
    
    "variables": {
        "energy": [
            "gsi", "load", "net_demand", "net_demand_plus_outages",
            "wind_gen", "solar_gen", "wind_cap_fac", "solar_cap_fac",
            "nonrenewable_outage_mw"
        ],
        "weather": [
            "temp_2m", "dew_2m", "wind_100m_mps", "ghi"
        ]
    },
    
    "data_categories": [
        {
            "name": "Grid Stress (GSI)",
            "description": "Peak stress probabilities, scarcity events, stress duration",
            "example": "What is the peak probability of GSI > 0.60 in next 14 days?"
        },
        {
            "name": "Load & Temperature",
            "description": "Extreme forecasts, load-temperature correlations, peak load predictions",
            "example": "Show me average RTO load when temperature drops below -5°C"
        },
        {
            "name": "Renewables",
            "description": "Wind/solar forecasts, Dunkelflaute probability, ramp rate analysis",
            "example": "What is the probability of Dunkelflaute?"
        },
        {
            "name": "Zonal Analysis",
            "description": "Zone comparisons, constraint risks, load distribution",
            "example": "Compare North vs West zone load spread in P99 scenario"
        },
        {
            "name": "Advanced Planning",
            "description": "Tail risks, uncertainty analysis, extreme scenarios",
            "example": "Calculate the net demand uncertainty (P95 - P05)"
        }
    ],
    
    "initialization_times": {
        "forecast": "2026-01-09 12:00",
        "seasonal": "2025-12-05 00:00"
    }
}


def get_project_info_message() -> str:
    """Generate project information message dynamically."""
    proj = SYSTEM_INFO["project"]
    locations = SYSTEM_INFO["locations"]
    
    msg = f"""I work with the **{proj['name']}** project ({proj['description']}).

**Available Data**:
• {len(locations)} load zones ({', '.join([loc['name'] for loc in locations])})
• {proj['details']['ensemble_paths']} probabilistic ensemble paths
• {proj['details']['forecast_horizon']} + seasonal outlook
• Variables: GSI, load, temperature, wind_gen, solar_gen, and more

Would you like to query any forecast data?

Example: '{SYSTEM_INFO['data_categories'][0]['example']}'"""
    
    return msg


def get_locations_info_message() -> str:
    """Generate locations information message dynamically."""
    locations = SYSTEM_INFO["locations"]
    
    msg = "**Available Locations**:\n"
    for loc in locations:
        msg += f"• {loc['id']} - {loc['description']}\n"
    
    msg += f"\nI can query forecast data for any of these {len(locations)} locations!\n\n"
    msg += f"Example: '{SYSTEM_INFO['data_categories'][1]['example']}'"
    
    return msg


def get_capabilities_info_message() -> str:
    """Generate capabilities information message dynamically."""
    categories = SYSTEM_INFO["data_categories"]
    
    msg = "I can help you query ERCOT energy forecast data in these areas:\n\n"
    
    for cat in categories:
        msg += f"**{cat['name']}** - {cat['description']}\n"
    
    msg += "\nExample queries:\n"
    for i, cat in enumerate(categories[:3], 1):  # Show first 3 examples
        msg += f"• '{cat['example']}'\n"
    
    return msg


def get_system_info_for_type(info_type: str) -> str:
    """
    Get system information message for a specific type.
    
    Args:
        info_type: 'project', 'locations', or 'capabilities'
        
    Returns:
        Formatted message string
    """
    if info_type == 'project':
        return get_project_info_message()
    elif info_type == 'locations':
        return get_locations_info_message()
    elif info_type == 'capabilities':
        return get_capabilities_info_message()
    else:
        return "I specialize in ERCOT forecast data. Ask me about projects, locations, or capabilities!"


# For easy imports
__all__ = [
    'SYSTEM_INFO',
    'get_system_info_for_type',
    'get_project_info_message',
    'get_locations_info_message',
    'get_capabilities_info_message'
]
