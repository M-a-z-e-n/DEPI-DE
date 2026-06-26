#  CosmicTracker — Power BI Dashboard

> **"Asteroid Watch: Defending Earth, One Orbit at a Time"**

## 🔗 Live Dashboard

[![Open in Power BI](https://img.shields.io/badge/Power%20BI-Open%20Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://app.powerbi.com/links/zEz8PI5UQ9?ctid=0bc92751-071a-4e2c-a48b-633206fef374&pbi_source=linkShare)

---

##  Dashboard Preview

### Overview Page — Asteroid Watch
![Asteroid Watch Overview](./screenshots/dashboard_overview.jpg)

**Key metrics displayed:**
-  **1,204** Total Detected Threats
-  **9.92%** Threat Ratio of Close Approaches
-  **158,044 Km/h** Peak Threat Velocity

**Visuals:**
-  Threat Horizon: Annual spike in hazardous asteroids (2020–2026)
-  Mass vs. Velocity scatter plot — identifying rogue cosmic bodies
-  Top 10 Critical Planetary Threats table (sorted by lunar distance)

---

### Detail Page — Comprehensive Near-Earth Object Watchlist
![NEO Watchlist](./screenshots/dashboard_watchlist.jpg)

**Interactive filters:**
- Proximity Category (Close / Distant / Moderate)
- Approach Year range slider (2020 → 2026)
- Estimated Diameter range slider (0.14 → 5.08 Km)

**Columns:**
- Asteroid Name
- Approach Date
- Lunar Distance
- Diameter (Km)
- Velocity (Km/h)

---

##  Data Connection

| Property | Value |
|---|---|
| **Source** | Azure Synapse Analytics Serverless SQL Pool |
| **Endpoint** | `synps-ws-neo-tracker-ondemand.sql.azuresynapse.net` |
| **Database** | `cosmictracker_dw` |
| **Schema** | `gold` |
| **Tables** | `gold.monthly_neo_summary`, `gold.hazardous_asteroids` |
| **Refresh** | Daily (automated via Synapse Pipeline trigger) |

---

##  Note on File Size

The `.pbix` file is **44 MB** and exceeds GitHub's recommended file size limit.
The live dashboard is publicly accessible via the Power BI link above.
