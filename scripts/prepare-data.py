#!/usr/bin/env python3
"""
ETL script: sanitize the DEM inventory master CSV for public display.

Reads the master inventory from the parent project, removes/redacts sensitive
fields, converts exact costs to brackets, adds country centroids, and writes
a public JSON file plus a countries GeoJSON for the dashboard.
"""

import csv
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MASTER_CSV = os.path.join(
    os.path.dirname(__file__),
    "../../dem-for-resilience/data/dem-inventory-master.csv",
)
OUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
OUT_JSON = os.path.join(OUT_DIR, "dem-inventory-public.json")
OUT_GEOJSON = os.path.join(OUT_DIR, "countries.geojson")

# Fields to remove entirely
REMOVE_FIELDS = {"POC Email", "Size in GB"}

# Fields to strip (contain internal follow-up notes)
STRIP_FIELDS = {"Notes", "Other Notes", "Status of Survey"}

# ---------------------------------------------------------------------------
# Non-standard ISO3 code fixes
# ---------------------------------------------------------------------------

ISO3_FIXES = {
    "BUR": "MMR",   # Burma -> Myanmar
    "EAZ": "TZA",   # Zanzibar -> Tanzania
    "ZAM": "ZMB",   # Zambia
    "TNZ": "TZA",   # Tanzania
    "SEY": "SYC",   # Seychelles
}

# ---------------------------------------------------------------------------
# Country centroids (ISO3 -> [lat, lng])
# ---------------------------------------------------------------------------

COUNTRY_CENTROIDS = {
    "AGO": [-12.29, 17.87],
    "BFA": [12.36, -1.52],
    "BLZ": [17.19, -88.50],
    "BTN": [27.47, 90.43],
    "CAF": [6.61, 20.94],
    "CMR": [5.95, 12.35],
    "COD": [-2.88, 23.66],
    "DMA": [15.41, -61.37],
    "EGY": [26.82, 30.80],
    "FJI": [-17.71, 178.07],
    "GAB": [-0.80, 11.61],
    "GHA": [7.95, -1.02],
    "GMB": [13.44, -15.31],
    "GRD": [12.12, -61.68],
    "GUY": [4.86, -58.93],
    "HTI": [19.07, -72.12],
    "IDN": [-0.79, 113.92],
    "IND": [20.59, 78.96],
    "JAM": [18.11, -77.30],
    "KEN": [-0.02, 37.91],
    "KHM": [12.57, 104.99],
    "LAO": [19.86, 102.50],
    "LBR": [6.43, -9.43],
    "LCA": [13.91, -60.98],
    "MDG": [-18.77, 46.87],
    "MHL": [7.13, 171.18],
    "MLI": [17.57, -4.00],
    "MMR": [21.91, 95.96],
    "MNG": [46.86, 103.85],
    "MOZ": [-18.67, 35.53],
    "MWI": [-13.25, 34.30],
    "NER": [17.61, 8.08],
    "NPL": [28.39, 84.12],
    "ROU": [45.94, 24.97],
    "RWA": [-1.94, 29.87],
    "SEN": [14.50, -14.45],
    "SLE": [8.46, -11.78],
    "SLV": [13.79, -88.90],
    "STP": [0.19, 6.61],
    "SXM": [18.04, -63.05],
    "SYC": [-4.68, 55.49],
    "TGO": [8.62, 1.17],
    "TON": [-21.18, -175.20],
    "TZA": [-6.37, 34.89],
    "UGA": [1.37, 32.29],
    "VNM": [14.06, 108.28],
    "VUT": [-15.38, 166.96],
    "WSM": [-13.76, -172.10],
    "ZMB": [-13.13, 27.85],
}

# ---------------------------------------------------------------------------
# Type normalization - group the messy type values into clean categories
# ---------------------------------------------------------------------------

TYPE_MAP = {
    "Satellite": "Satellite",
    "Satellite - Optical": "Satellite",
    "Drone": "Drone",
    "Drone - Optical": "Drone",
    "Drone - Lidar": "LiDAR",
    "Aircraft - Lidar": "LiDAR",
    "Helicopter - LiDAR": "LiDAR",
    "???": "Unknown",
    "": "Unknown",
}

# ---------------------------------------------------------------------------
# Cost brackets
# ---------------------------------------------------------------------------

def cost_bracket(usd):
    if usd is None:
        return "Unknown"
    if usd < 10_000:
        return "< $10,000"
    if usd < 50_000:
        return "$10,000 - $50,000"
    if usd < 100_000:
        return "$50,000 - $100,000"
    if usd < 500_000:
        return "$100,000 - $500,000"
    if usd < 1_000_000:
        return "$500,000 - $1,000,000"
    return "> $1,000,000"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    src = os.path.abspath(MASTER_CSV)
    if not os.path.exists(src):
        print(f"ERROR: Master CSV not found at {src}", file=sys.stderr)
        sys.exit(1)

    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Read {len(raw_rows)} rows from {src}")

    public_rows = []
    country_counts = {}  # iso3 -> {count, total_cost, ...}

    skipped = 0
    for row in raw_rows:
        # Skip records with no country - too incomplete for public display
        country = row.get("Country", "").strip()
        if not country:
            skipped += 1
            continue

        rec = {}

        # Fix ISO3
        iso3 = row.get("Country ISO3", "").strip()
        iso3 = ISO3_FIXES.get(iso3, iso3)

        # Clean up "???" dataset names
        raw_name = row.get("Dataset Name", "").strip()
        if raw_name.startswith("???"):
            # Build a descriptive name from country + product/vendor/type
            product = row.get("Product", "").strip()
            vendor = row.get("Vendor", "").strip()
            dtype = row.get("Type", "").strip()
            # Extract the useful suffix after "???" (e.g. "DTM", "AW3D")
            suffix = raw_name.replace("???", "").strip()
            # Remove parenthesized country references and clean up
            suffix = re.sub(r'\([^)]*\)', '', suffix).strip()
            suffix = suffix.replace(country, "").strip()
            suffix = suffix.strip("- ")
            if suffix:
                raw_name = f"{country} - {suffix}"
            elif product:
                raw_name = f"{country} - {product}"
            else:
                raw_name = f"{country} - {vendor} DEM"

        # Core fields
        rec["name"] = raw_name
        rec["year"] = row.get("Year", "").strip()
        rec["vendor"] = row.get("Vendor", "").strip()
        rec["product"] = row.get("Product", "").strip()
        rec["type"] = TYPE_MAP.get(row.get("Type", "").strip(), "Unknown")
        rec["resolution_m"] = row.get("Res. (m)", "").strip()
        rec["aoi"] = row.get("AOI", "").strip()
        rec["country"] = row.get("Country", "").strip()
        rec["iso3"] = iso3
        rec["size_km2"] = row.get("Size in Km2", "").strip()
        rec["ttl"] = row.get("TTL", "").strip()
        rec["available"] = row.get("Available?", "").strip()
        rec["url"] = row.get("URL", "").strip()
        rec["license"] = row.get("License", "").strip()
        rec["pcode"] = row.get("PCODE", "").strip()
        rec["be_re"] = row.get("BE/RE*", "").strip()
        rec["project_type"] = row.get("Project Type*", "").strip()
        rec["tf"] = row.get("TF", "").strip()
        rec["main_use"] = row.get("Main Use", "").strip()
        rec["hazards"] = row.get("Natural Hazard(s) to be Addressed", "").strip()
        rec["application"] = row.get("Application", "").strip()
        rec["dsm_dtm_pc"] = row.get("DSM, DTM, PC", "").strip()
        rec["ground_control"] = row.get("Ground Control", "").strip()
        rec["pad_number"] = row.get("PAD number", "").strip()
        rec["consultant"] = row.get("Consultant", "").strip()

        # Cost bracket (redact exact cost)
        cost_raw = row.get("Cost (USD, cleaned)", "").strip()
        cost_usd = None
        if cost_raw:
            try:
                cost_usd = float(cost_raw)
            except ValueError:
                pass
        rec["cost_bracket"] = cost_bracket(cost_usd)

        # Add centroid coordinates
        centroid = COUNTRY_CENTROIDS.get(iso3)
        if centroid:
            rec["lat"] = centroid[0]
            rec["lng"] = centroid[1]
        else:
            rec["lat"] = None
            rec["lng"] = None

        public_rows.append(rec)

        # Aggregate country stats
        if iso3:
            if iso3 not in country_counts:
                country_counts[iso3] = {
                    "count": 0,
                    "total_cost": 0,
                    "country": rec["country"],
                    "lat": rec["lat"],
                    "lng": rec["lng"],
                }
            country_counts[iso3]["count"] += 1
            if cost_usd:
                country_counts[iso3]["total_cost"] += cost_usd

    # Write public JSON
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.abspath(OUT_JSON), "w", encoding="utf-8") as f:
        json.dump(public_rows, f, indent=2, ensure_ascii=False)
    print(f"Skipped {skipped} records with no country")
    print(f"Wrote {len(public_rows)} records to {OUT_JSON}")

    # Build countries GeoJSON (point features at centroids)
    features = []
    for iso3, stats in sorted(country_counts.items()):
        if stats["lat"] is None:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "iso3": iso3,
                "country": stats["country"],
                "count": stats["count"],
                "total_cost": stats["total_cost"],
                "cost_bracket": cost_bracket(stats["total_cost"]) if stats["total_cost"] else "Unknown",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [stats["lng"], stats["lat"]],
            },
        })

    geojson = {"type": "FeatureCollection", "features": features}
    with open(os.path.abspath(OUT_GEOJSON), "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(features)} country features to {OUT_GEOJSON}")

    # Summary
    types = [r["type"] for r in public_rows]
    costs = [r["cost_bracket"] for r in public_rows]
    countries_with_data = len([c for c in country_counts if country_counts[c]["lat"]])
    print(f"\nSummary:")
    print(f"  Records: {len(public_rows)}")
    print(f"  Countries with coordinates: {countries_with_data}")
    print(f"  Types: { {t: types.count(t) for t in sorted(set(types))} }")
    print(f"  Cost brackets: { {c: costs.count(c) for c in sorted(set(costs))} }")


if __name__ == "__main__":
    main()
