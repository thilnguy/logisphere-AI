"""
Mock Data Generator for Logistics Pipeline Testing.
Generates a realistic Logistics_Raw.xlsx with intentional data quality issues
(messy dates, duplicates, PII, carrier name variants, missing values).
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

ROWS = 2500
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Logistics_Raw_July.xlsx")

# --- Carrier name variants (intentionally messy for fuzzy matching) ---
CARRIER_VARIANTS = [
    "DHL", "DHL Express", "DHL - Paris", "DHL Freight",
    "FedEx", "Federal Express", "FedEx Ground",
    "UPS", "United Parcel Service", "UPS Express",
    "Chronopost", "Chrono", "Chronopost FR",
    "GLS", "GLS France", "General Logistics Systems",
    "DB Schenker", "Schenker",
    "Kuehne+Nagel", "KN", "Kuehne Nagel",
    "XPO", "XPO Logistics",
    None, None, "",  # intentional blanks
]

WAREHOUSES = [
    "CDG Hub", "Paris CDG", "Roissy Warehouse",
    "Lyon DC", "Lyon Distribution",
    "Marseille Depot", "Marseille Port",
    "Bordeaux LP", "Bordeaux Park",
]

DEST_CITIES_COORDS = {
    # --- Major Logistics Hubs (high volume) ---
    "Paris":        (48.8566, 2.3522),
    "Lyon":         (45.7640, 4.8357),
    "Marseille":    (43.2965, 5.3698),
    "Toulouse":     (43.6047, 1.4442),
    "Lille":        (50.6292, 3.0573),
    "Bordeaux":     (44.8378, -0.5792),
    "Nantes":       (47.2184, -1.5536),
    "Strasbourg":   (48.5734, 7.7521),
    "Nice":         (43.7102, 7.2620),
    "Rennes":       (48.1173, -1.6778),
    # --- Regional Hubs (medium volume) ---
    "Montpellier":  (43.6108, 3.8767),
    "Grenoble":     (45.1885, 5.7245),
    "Rouen":        (49.4432, 1.0999),
    "Tours":        (47.3941, 0.6848),
    "Clermont-Ferrand": (45.7772, 3.0870),
    "Dijon":        (47.3220, 5.0415),
    "Angers":       (47.4784, -0.5632),
    "Le Mans":      (48.0061, 0.1996),
    "Reims":        (49.2583, 3.2794),
    "Le Havre":     (49.4944, 0.1079),
    "Saint-Étienne":(45.4397, 4.3872),
    "Toulon":       (43.1242, 5.9280),
    "Aix-en-Provence": (43.5297, 5.4474),
    "Brest":        (48.3904, -4.4861),
    "Metz":         (49.1193, 6.1757),
    "Orléans":      (47.9029, 1.9093),
    "Mulhouse":     (47.7508, 7.3359),
    "Caen":         (49.1829, -0.3707),
    "Perpignan":    (42.6887, 2.8948),
    "Amiens":       (49.8941, 2.2957),
    # --- Smaller Towns (low volume, wide coverage) ---
    "Limoges":      (45.8336, 1.2611),
    "Besançon":     (47.2378, 6.0241),
    "Pau":          (43.2951, -0.3708),
    "Poitiers":     (46.5802, 0.3404),
    "La Rochelle":  (46.1603, -1.1511),
    "Bayonne":      (43.4933, -1.4753),
    "Valence":      (44.9334, 4.8924),
    "Avignon":      (43.9493, 4.8055),
    "Calais":       (50.9513, 1.8587),
    "Dunkerque":    (51.0343, 2.3768),
    "Troyes":       (48.2974, 4.0744),
    "Quimper":      (47.9960, -4.0999),
    "Vannes":       (47.6559, -2.7603),
    "Chambéry":     (45.5646, 5.9178),
    "Annecy":       (45.8992, 6.1294),
    "Ajaccio":      (41.9192, 8.7386),
    "Bastia":       (42.6970, 9.4503),
    "Colmar":       (48.0794, 7.3558),
    "Chartres":     (48.4561, 1.4890),
    "Bourges":      (47.0810, 2.3988),
    "Auxerre":      (47.7979, 3.5714),
}
DEST_CITIES = list(DEST_CITIES_COORDS.keys())

# Weighted probabilities: major hubs get more deliveries
_MAJOR = 10  # first 10 cities
_REGIONAL = 20  # next 20
_weights = [0.06] * _MAJOR + [0.012] * _REGIONAL + [0.004] * (len(DEST_CITIES) - _MAJOR - _REGIONAL)
# Normalize
_total = sum(_weights)
DEST_WEIGHTS = [w / _total for w in _weights]

VEHICLE_TYPES = ["petit_camion", "gros_camion", "fourgonnette", "train", "avion"]

STATUSES = ["Livré", "En transit", "Retardé", "Retourné", "En attente"]

# --- Fake French names & phones for PII testing ---
FIRST_NAMES = ["Jean", "Marie", "Pierre", "Sophie", "Luc", "Camille", "Antoine", "Isabelle", "François", "Chloé"]
LAST_NAMES = ["Dupont", "Martin", "Bernard", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Michel"]


def _random_date_string(start: datetime, end: datetime, messy: bool = False) -> str:
    """Generate date strings with intentional format inconsistencies."""
    delta = (end - start).days
    d = start + timedelta(days=np.random.randint(0, delta))
    if messy:
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d %b %Y", "%Y/%m/%d"]
        return d.strftime(np.random.choice(formats))
    return d.strftime("%Y-%m-%d")


def generate() -> str:
    """Generate mock logistics data and save to Excel. Returns output path."""
    np.random.seed(42)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Expand history to 2 years for Year-over-Year seasonality
    end = datetime.now()
    start = end - timedelta(days=730)

    records = []
    for i in range(ROWS):
        tracking_id = f"FR-{np.random.randint(100000, 999999)}"
        
        # Generate actual date objects first, then format to messy strings
        delta = (end - start).days
        order_dt = start + timedelta(days=np.random.randint(0, delta))
        
        # Order date: messy format (to test Cleaner Agent's parsing)
        if True:  # Always messy for testing
            formats = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%Y/%m/%d"]
            order_date = order_dt.strftime(np.random.choice(formats))

        # Delivery date: order + 1-14 days (computed from real date, not parsed string)
        status = np.random.choice(STATUSES, p=[0.55, 0.15, 0.15, 0.05, 0.10])
        if status in ("En attente", "En transit"):
            delivery_date = None
        else:
            delivery_dt = order_dt + timedelta(days=np.random.randint(1, 14))
            delivery_date = delivery_dt.strftime("%Y-%m-%d")

        carrier = np.random.choice(CARRIER_VARIANTS)
        origin = np.random.choice(WAREHOUSES)
        dest = np.random.choice(DEST_CITIES, p=DEST_WEIGHTS)
        city_lat, city_lon = DEST_CITIES_COORDS[dest]
        # Weight and cost based on vehicle type (highly realistic domestic EU B2B logistics)
        vehicle_profiles = {
            "fourgonnette":  {"weight": (0.5,  50),   "cost": (5,    15),  "per_kg": 0.05},  # Local courier / Parcel
            "petit_camion":  {"weight": (50,   800),  "cost": (35,   80),  "per_kg": 0.08},  # LTL (Less-than-truckload)
            "gros_camion":   {"weight": (800,  5000), "cost": (150,  250), "per_kg": 0.04},  # FTL (Full-truckload)
            "train":         {"weight": (500,  8000), "cost": (100,  200), "per_kg": 0.02},  # Intermodal
            "avion":         {"weight": (1,    250),  "cost": (100,  250), "per_kg": 0.60},  # Premium Express Air
        }
        vehicle = np.random.choice(VEHICLE_TYPES)
        profile = vehicle_profiles.get(vehicle, {"weight": (1, 100), "cost": (30, 200), "per_kg": 0.10})
        weight = round(np.random.uniform(*profile["weight"]), 1)
        
        # Add distance and weight combined correlation
        distance = round(np.random.uniform(10, 1200), 1)
        base_cost = np.random.uniform(*profile["cost"])
        weight_surcharge = weight * profile["per_kg"]
        
        cost = round((base_cost + weight_surcharge) * (1 + (distance / 2000)), 2)

        customer = f"{np.random.choice(FIRST_NAMES)} {np.random.choice(LAST_NAMES)}"
        phone = f"+33 6 {np.random.randint(10,99)} {np.random.randint(10,99)} {np.random.randint(10,99)} {np.random.randint(10,99)}"
        lat = round(city_lat + np.random.normal(0, 0.05), 5)
        lon = round(city_lon + np.random.normal(0, 0.05), 5)

        records.append({
            "tracking_id": tracking_id,
            "order_date": order_date,
            "delivery_date": delivery_date,
            "carrier": carrier,
            "origin_warehouse": origin,
            "destination_city": dest,
            "weight_kg": weight if np.random.random() > 0.03 else "N/A",  # intentional bad data
            "distance_km": distance,
            "status": status,
            "vehicle_type": vehicle,
            "shipping_cost_eur": cost,
            "customer_name": customer,
            "phone": phone,
            "lat": lat,
            "lon": lon,
        })

    df = pd.DataFrame(records)

    # --- Introduce duplicates (5% of rows) ---
    dup_indices = np.random.choice(df.index, size=int(ROWS * 0.05), replace=False)
    duplicates = df.loc[dup_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
    print(f"✅ Generated {len(df)} rows -> {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    generate()
