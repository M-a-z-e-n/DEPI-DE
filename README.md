<div align="center">

<img src="https://img.shields.io/badge/NASA-NeoWs%20API-0B3D91?style=for-the-badge&logo=nasa&logoColor=white"/>
<img src="https://img.shields.io/badge/Azure%20Synapse-Analytics-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white"/>
<img src="https://img.shields.io/badge/ADLS-Gen2-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white"/>
<img src="https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black"/>
<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>

# 🌌 CosmicTracker

### *Defending Earth, One Orbit at a Time*

An end-to-end data engineering pipeline that ingests, transforms, and visualizes
**6 years of NASA Near-Earth Object (NEO) data** using the Azure medallion architecture.

</div>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Data Pipeline](#-data-pipeline)
- [Medallion Architecture](#-medallion-architecture)
- [Pipeline Screenshots](#-pipeline-screenshots)
- [Data Schema](#-data-schema)
- [Project Structure](#-project-structure)
- [Setup & Usage](#-setup--usage)
- [ML Model](#-ml-model)
- [Power BI Dashboard](#-power-bi-dashboard)
- [Team](#-team)

---

## 🔭 Project Overview

CosmicTracker is a production-grade data engineering project that tracks Near-Earth Objects (asteroids and comets) using NASA's public NeoWs API. The system:

- Fetches **6 years of historical NEO data** (~313 weekly API chunks)
- Automatically **ingests fresh data daily** via a scheduled Synapse pipeline
- Transforms raw nested JSON through **Bronze → Silver → Gold** layers
- Surfaces clean, aggregated data to a **Power BI dashboard** for threat analysis
- Tracks **1,200+ potentially hazardous asteroids** across 12,000+ close-approach events

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│              NASA NeoWs API (api.nasa.gov)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API (daily, 7-day chunks)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                                │
│         Python Scripts / Synapse Copy Activity                   │
│   step1_fetch_historical.py  │  step2_build_dataset.py          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Raw JSON / CSV
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               AZURE DATA LAKE STORAGE GEN2                       │
│                   (neotracker container)                         │
│                                                                  │
│  source/          bronze/          silver/         gold/         │
│  ├─ *.csv         ├─ neo_bronze/   ├─ neo_silver/  ├─ monthly/  │
│  └─ daily/        │  ├─ *.parquet  │  └─ *.parquet └─ hazard/   │
│     └─ *.json     │  └─ daily_*/   │                            │
└───────────────────┼────────────────┼────────────────────────────┘
                    │                │
                    ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│              AZURE SYNAPSE ANALYTICS                             │
│              (Serverless SQL Pool)                               │
│                                                                  │
│   Database: cosmictracker_dw                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │  source  │→ │  bronze  │→ │  silver  │→ │   gold   │      │
│   │  schema  │  │  schema  │  │  schema  │  │  schema  │      │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                  │
│   Pipeline: pl_cosmictracker_medallion (daily trigger)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Serverless SQL endpoint
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                  Power BI Dashboard                              │
│            "Asteroid Watch" — gold schema                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Cloud Platform** | Microsoft Azure |
| **Storage** | Azure Data Lake Storage Gen2 |
| **Compute** | Azure Synapse Analytics (Serverless SQL Pool) |
| **Orchestration** | Synapse Pipelines (daily schedule trigger) |
| **Ingestion** | Python 3.11, Requests, Pandas |
| **Transformation** | T-SQL, CETAS, OPENROWSET, OPENJSON |
| **File Format** | JSON (raw) → CSV (staging) → Parquet (warehouse) |
| **Visualization** | Power BI Desktop + Power BI Service |
| **Secret Management** | Azure Key Vault |
| **Version Control** | Git + GitHub |
| **Data Source** | NASA NeoWs REST API |

---

## 🔄 Data Pipeline

### Daily Automated Flow

```
[Daily Trigger — 02:00 UTC]
        │
        ▼
Set Run Date (yesterday's date)
        │
        ▼
Set Run Date Compact (YYYYMMDD format)
        │
        ▼
Get NASA API Key (Azure Key Vault)
        │
        ▼
Pull Daily NEO Data (Copy Activity → REST API → ADLS JSON)
        │
        ▼
Flatten & Append to Bronze (OPENROWSET + OPENJSON → Parquet)
        │
        ▼
Load Silver (recursive read bronze/** → deduplicate → enrich)
        │
        ▼
Load Gold ──┬── monthly_neo_summary
            └── hazardous_asteroids
```

### Historical Backfill (one-time)

```bash
# Fetch 6 years of weekly chunks (~313 API calls)
python scripts/step1_fetch_historical.py --years 6

# Flatten all JSON chunks into one CSV
python scripts/step2_build_dataset.py
```

---

## 🥇 Medallion Architecture

### Source Schema
Raw data exactly as received — CSV uploaded to ADLS, all columns as `VARCHAR`.
Serves as the permanent audit trail.

### Bronze Layer
- One Parquet file per daily API pull, stored as `bronze/neo_bronze/daily_YYYYMMDD/`
- All 6 years of historical data stored as a base Parquet file
- Typed columns (`FLOAT`, `BIT`, `DATE`) via `TRY_CAST`
- Metadata columns added: `_ingested_at`, `_source_file`
- **Append-only** — historical data never modified

### Silver Layer
- Full rebuild on every pipeline run, reading all Bronze recursively (`bronze/neo_bronze/**`)
- Deduplication: one row per `(neo_id, close_approach_date)`, keeping latest ingestion
- Derived column: `estimated_diameter_avg_km`
- Enriched column: `proximity_category` (Very Close / Close / Moderate / Distant)
- Result: **12,000+ clean close-approach records**

### Gold Layer
Two business-ready aggregated tables:

**`gold.monthly_neo_summary`** — 73 rows (one per month, 2020–2026)
| Column | Description |
|---|---|
| `approach_year` / `approach_month` | Time dimension |
| `unique_asteroids` | Distinct NEOs tracked |
| `total_approaches` | Total close-approach events |
| `hazardous_approaches` | Count of potentially hazardous |
| `avg_diameter_km` | Average asteroid size |
| `closest_approach_lunar_distance` | Closest pass in lunar distances |
| `avg_velocity_kph` | Average speed |

**`gold.hazardous_asteroids`** — 1,200+ rows
| Column | Description |
|---|---|
| `neo_id` / `name` | Asteroid identifier |
| `close_approach_date` | Date of close pass |
| `estimated_diameter_avg_km` | Size estimate |
| `miss_distance_lunar` / `miss_distance_km` | How close it came |
| `relative_velocity_kph` | Speed at closest approach |
| `proximity_category` | Human-readable threat bucket |

---

## 📸 Pipeline Screenshots

### Synapse Pipeline — Full Orchestration

> 📌 *Screenshot: pl_cosmictracker_medallion pipeline canvas*

```
<img width="1798" height="248" alt="msedge_42cZgIh4p1" src="https://github.com/user-attachments/assets/61ed27cf-934c-47a0-90ab-4ff74ca4f579" />
```

### Pipeline Run — Successful Execution

> 📌 *Screenshot: All activities green after a successful daily run*

```
<img width="1792" height="897" alt="msedge_BZ3JYwEjuZ" src="https://github.com/user-attachments/assets/2d2663c7-b134-4cba-95f0-36912b04c259" />
```

### ADLS Gen2 — Folder Structure
> 📌 *Screenshot: neotracker container folder structure*

```
<img width="1549" height="381" alt="image" src="https://github.com/user-attachments/assets/21a6cb70-01aa-471c-8986-959519754c9c" />
```

### Synapse SQL — Gold Layer Query Results
> 📌 *Screenshot: Gold layer query results in Synapse Studio*

```
<img width="1910" height="915" alt="image" src="https://github.com/user-attachments/assets/de3e4454-1d8f-47a1-8372-b0806e639f9a" />
```

---

## 🗂️ Data Schema

### Raw NASA NeoWs Response (nested JSON)
```json
{
  "near_earth_objects": {
    "2026-06-23": [
      {
        "id": "54016435",
        "name": "(2020 ND)",
        "absolute_magnitude_h": 24.5,
        "is_potentially_hazardous_asteroid": false,
        "estimated_diameter": {
          "kilometers": {
            "estimated_diameter_min": 0.037,
            "estimated_diameter_max": 0.083
          }
        },
        "close_approach_data": [{
          "close_approach_date": "2026-06-23",
          "relative_velocity": { "kilometers_per_hour": "42156.3" },
          "miss_distance": { "kilometers": "1234567.8", "lunar": "3.21" },
          "orbiting_body": "Earth"
        }]
      }
    ]
  }
}
```

### Final Silver Schema (flattened)
```
neo_id                    VARCHAR
neo_reference_id          VARCHAR
name                      VARCHAR
absolute_magnitude_h      FLOAT
estimated_diameter_min_km FLOAT
estimated_diameter_max_km FLOAT
estimated_diameter_avg_km FLOAT   ← derived
is_potentially_hazardous  BIT
is_sentry_object          BIT
close_approach_date       DATE
relative_velocity_kph     FLOAT
miss_distance_km          FLOAT
miss_distance_lunar       FLOAT
miss_distance_au          FLOAT
orbiting_body             VARCHAR
nasa_jpl_url              VARCHAR
proximity_category        VARCHAR  ← derived
```

---

## 📁 Project Structure

```
DEPI-DE/
│
├── scripts/
│   ├── step1_fetch_historical.py     # Fetches 6 years of NASA data
│   └── step2_build_dataset.py        # Combines JSON chunks into CSV
│
├── sql/
│   ├── 00_setup.sql                  # Database, schemas, credentials
│   ├── 01_source_table.sql           # External table over raw CSV
│   ├── 02_bronze.sql                 # Bronze CETAS script
│   ├── 03_silver.sql                 # Silver dedup + enrichment
│   └── 04_gold.sql                   # Gold aggregations
│
├── powerbi/
│   ├── README.md                     # Dashboard documentation
│   └── screenshots/
│       ├── dashboard_overview.jpg
│       └── dashboard_watchlist.jpg
│
├── .env.example                      # Environment variable template
├── .gitignore
└── README.md                         # This file
```

---

## ⚙️ Setup & Usage

### Prerequisites
- Azure subscription (Student or Pay-as-you-go)
- Python 3.11+
- NASA API key (free at [api.nasa.gov](https://api.nasa.gov))

### 1. Clone the repo
```bash
git clone https://github.com/M-a-z-e-n/DEPI-DE.git
cd DEPI-DE
```

### 2. Install Python dependencies
```bash
pip install requests pandas tqdm python-dotenv
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and add your NASA API key:
# NASA_API_KEY=your_key_here
```

### 4. Fetch historical data
```bash
python scripts/step1_fetch_historical.py --years 6
```

### 5. Build the combined CSV
```bash
python scripts/step2_build_dataset.py
```

### 6. Upload to Azure
- Upload `data/processed/neo_dataset.csv` to `source/` folder in ADLS Gen2
- Run the SQL setup scripts in order (`00` → `04`) in Synapse Studio
- Import and trigger `pl_cosmictracker_medallion` pipeline

### Environment Variables
```bash
# .env.example
NASA_API_KEY=your_nasa_api_key_here
```

---

## 🤖 ML Model

> 🚧 *This section will be completed once the ML model is finalized.*

<!-- Add the following when ready:
- Model objective (e.g. hazard classification, miss distance prediction)
- Algorithm used
- Features / target variable
- Training dataset details
- Model performance metrics (accuracy, F1, RMSE, etc.)
- How the model integrates with the pipeline
- Inference results or predictions
-->

---

## 📊 Power BI Dashboard

> 🚧 *This section will be completed with full dashboard documentation.*

<!-- Add the following when ready:
- Live dashboard link
- Screenshot of each page
- Description of visuals and KPIs
- Data refresh schedule
- How to connect your own Power BI to the gold schema
-->

---

## 👥 Team

**Deadlock** — Egypt University of Informatics, DEPI Data Engineering Track

| Name | Role |
|---|---|
| Abdullah Fathy | Team Leader & Pipeline Architect |
| <!-- Team Member 2 --> | <!-- Role --> |
| <!-- Team Member 3 --> | <!-- Role --> |
| <!-- Team Member 4 --> | <!-- Role --> |
| <!-- Team Member 5 --> | <!-- Role --> |

---

<div align="center">

Built with ❤️ for the **DEPI Data Engineering Program**

*Data sourced from [NASA's NeoWs API](https://api.nasa.gov/)*

</div>
