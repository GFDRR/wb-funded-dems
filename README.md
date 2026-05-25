# World Bank Funded DEMs - Procurement Dashboard

Interactive dashboard for exploring World Bank-funded Digital Elevation Model (DEM) procurement metadata. Part of the GFDRR "DEM for Resilience" project.

## Overview

The World Bank has funded 130+ DEM procurements across 65+ countries (2008-2025). This dashboard provides a public, browsable catalog of the procurement metadata to support transparency, reduce duplicate procurement across projects, and surface trends that inform a future centralized acquisition strategy.

**Live dashboard**: [https://cgiovando.github.io/wb-funded-dems/](https://cgiovando.github.io/wb-funded-dems/)

## Features

- **Map view** - MapLibre GL JS world map with proportional circles aggregating procurements by country; click a country for the list of datasets.
- **Charts view** - Procurement trend with linear fit and 15% CAGR projection for 2026-2028, sensor type mix, BE/RE (Bank Executed vs Recipient Executed) split, top vendors, and cost bracket distribution. Every chart updates live with the filters.
- **Table view** - Sortable table with a colored BE/RE badge, sensor type, cost bracket, and a deep link to the corresponding World Bank project page via PCODE.
- **Faceted filters** - Country, sensor type, vendor, BE/RE, cost bracket, and year. Each dropdown dynamically narrows to values still reachable given the other selections, so you never land on an impossible combination.
- **Summary stats strip** - Dataset and country counts, year range, sensor mix, BE/RE split, and availability - all recomputed as filters change.

## Data

The dashboard displays sanitized metadata from the canonical DEM procurement inventory maintained in the private `GFDRR/dem-for-resilience` repository (`repo/data/dem-inventory-expanded.csv` - the single source of truth). The ETL script (`scripts/prepare-data.py`) reads the canonical CSV, strips sensitive fields, converts exact costs to brackets, normalizes sensor-type labels and years, adds country centroids, and writes `data/dem-inventory-public.json`.

### Data sensitivity

- Contact emails are removed entirely
- Exact costs are replaced with cost brackets (< $10K, $10K-$50K, ..., > $1M)
- Internal notes and status fields are stripped
- 3 records with no country of record are dropped

## Tech stack

- Static site - no build step, single `index.html`
- [MapLibre GL JS](https://maplibre.org/) - interactive map with Carto Positron basemap
- [Chart.js](https://www.chartjs.org/) (CDN) - trend, doughnut, and bar charts
- [Tailwind CSS](https://tailwindcss.com/) (CDN) - styling
- Vanilla JavaScript - no framework dependencies
- Python - ETL/data preparation script (run locally)
- GitHub Pages - hosting

## Development

To regenerate the public data files from the master inventory:

```bash
python3 scripts/prepare-data.py
```

To run the dashboard locally:

```bash
python3 -m http.server 8877
# Open http://localhost:8877
```

## AI-assisted development

> This project was developed with significant assistance from AI coding tools.

- **[Claude Code](https://claude.ai/claude-code)** (Anthropic) - code generation, architecture, debugging, and documentation
- All functionality has been tested and verified to work as intended
- Features and infrastructure choices have been reviewed and approved by the maintainer

This disclosure follows emerging best practices for transparency in AI-assisted software development.

## Funding

Funded by the **Japan-GFDRR Trust Fund (Phase 2)**, with support from the Japan-World Bank DRM Hub.

## License

This project is part of the GFDRR/World Bank "DEM for Resilience" project.
