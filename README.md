# World Bank Funded DEMs - Procurement Dashboard

Interactive dashboard for exploring World Bank-funded Digital Elevation Model (DEM) procurement metadata. Part of the GFDRR "DEM for Resilience" initiative.

## Overview

The World Bank has funded 90+ DEM procurements across 50+ countries totaling approximately $19.5M (2011-2024). This dashboard provides a public, browsable catalog of that procurement metadata to support transparency and reduce duplicate procurement.

**Live dashboard**: [https://cgiovando.github.io/wb-funded-dems/](https://cgiovando.github.io/wb-funded-dems/)

## Features

- **Map View** - Interactive MapLibre GL JS map with proportional circles showing procurement counts by country
- **Table View** - Searchable, sortable table of all procurement records with linked World Bank project codes
- **Filters** - Filter by country, type (LiDAR/Satellite/Drone), vendor, cost bracket, and year
- **Summary Statistics** - Key metrics updated dynamically as filters change

## Data

The dashboard displays sanitized metadata from the DEM procurement inventory. Sensitive fields (contact emails, exact costs) are removed or replaced with cost brackets. The ETL script (`scripts/prepare-data.py`) handles this transformation.

### Data sensitivity

- Email addresses are removed entirely
- Exact costs are replaced with cost brackets
- Internal notes are stripped

## Tech stack

- Static site - no build step, single `index.html`
- [MapLibre GL JS](https://maplibre.org/) - interactive map
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

## License

This project is part of the GFDRR/World Bank "DEM for Resilience" initiative.
