"""
profiles.py
Location presets for camera feeds and video uploads in Phylax.
"""

from typing import Dict, List, Any

LOCATION_PROFILES: Dict[str, Dict[str, Any]] = {
    "HOME": {
        "name": "Home / Residential",
        "description": "Monitors perimeter breaches, fall incidents, fire hazards, and suspicious loitering near gates.",
        "active_detectors": ["intrusion", "fall", "fire_smoke", "loitering"],
        "default_thresholds": {
            "loitering": {"max_loiter_sec": 12.0},
            "intrusion": {"cooldown_sec": 10},
        }
    },
    "SHOP_RETAIL": {
        "name": "Shop & Retail Store",
        "description": "Optimized for shoplifting detection, counter loitering, after-hours intrusion, and crowd monitoring.",
        "active_detectors": ["theft", "loitering", "intrusion", "crowd_density", "fire_smoke"],
        "default_thresholds": {
            "theft": {"lingering_threshold_sec": 8.0},
            "crowd_density": {"max_capacity": 6}
        }
    },
    "MALL": {
        "name": "Shopping Mall & Public Space",
        "description": "Detects overcrowding bottlenecks, abandoned luggage, retail theft, fights, and fire risks.",
        "active_detectors": ["crowd_density", "abandoned_object", "theft", "fight", "fire_smoke"],
        "default_thresholds": {
            "crowd_density": {"max_capacity": 15},
            "abandoned_object": {"abandoned_sec_threshold": 12.0}
        }
    },
    "CINEMA_THEATRE": {
        "name": "Cinema / Theatre / Auditorium",
        "description": "Monitors auditorium capacity, projection room intrusion, slips/falls, fights, and fire safety.",
        "active_detectors": ["crowd_density", "abandoned_object", "fight", "fire_smoke", "intrusion", "fall"],
        "default_thresholds": {
            "crowd_density": {"max_capacity": 20},
            "intrusion": {"after_hours_mode": True}
        }
    },
    "OFFICE_WAREHOUSE": {
        "name": "Office & Warehouse Facility",
        "description": "Monitors restricted storage zones, after-hours movements, worker fall safety, and smoke hazards.",
        "active_detectors": ["intrusion", "fire_smoke", "fall"],
        "default_thresholds": {
            "intrusion": {"after_hours_mode": True}
        }
    },
    "ROAD_PARKING": {
        "name": "Roadway & Parking Lot",
        "description": "Detects vehicle collisions, sudden stops, illegal parking/loitering, and car fires.",
        "active_detectors": ["accident", "loitering", "fire_smoke"],
        "default_thresholds": {
            "accident": {"score_threshold": 2},
            "loitering": {"max_loiter_sec": 15.0}
        }
    },
    "CUSTOM": {
        "name": "Custom Profile",
        "description": "User-configured detector set and thresholds.",
        "active_detectors": ["accident", "theft", "intrusion", "loitering", "fire_smoke", "crowd_density", "fall", "fight", "abandoned_object"],
        "default_thresholds": {}
    }
}


def get_profile_detectors(profile_key: str) -> List[str]:
    prof = LOCATION_PROFILES.get(profile_key.upper(), LOCATION_PROFILES["ROAD_PARKING"])
    return prof["active_detectors"]
