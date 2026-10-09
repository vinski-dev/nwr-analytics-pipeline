 Newport World Resorts (NWR) - Enterprise Data Pipeline Architecture

Executive Summary
This project is an end-to-end, enterprise-grade data ingestion and transformation pipeline designed for Newport World Resorts. Built within a 48-hour window, it demonstrates a robust Medallion Architecture capable of handling the complexities of modern casino and hospitality data ecosystems.

The pipeline specifically addresses core operational challenges: siloed identity resolution, late-arriving offline data, and strict historical state tracking (SCD Type 2), all while enforcing absolute data integrity and idempotency.



 Technical Stack
 Cloud Infrastructure: Google Cloud Platform (GCS, BigQuery)
 Ingestion/Orchestration: Python, Google Cloud SDK
 Transformation & Governance: dbt Core (dbt-bigquery, dbt-utils)



 Architecture Overview (The Medallion Approach)

1. Source Generation: Synthetic Python scripts simulate fragmented NWR systems (Legacy Hotel PMS and modern Casino CMS).
2. Landing Zone (GCS): Raw JSON and CSV files land in a Google Cloud Storage bucket, creating an immutable data lake and decoupling source systems from the warehouse.
3. Bronze Layer (BigQuery): Idempotent Python ingestion scripts load data into BigQuery using time-partitioning and schema-forgiving configurations.
4. Silver Layer (dbt): Cleanses types, standardizes column names, and enforces deduplication using `QUALIFY ROW_NUMBER()`.
5. Intermediate Layer (dbt): Bridges fragmented source systems to create unified entities.
6. Gold Layer (dbt): Business-ready conformed dimensions and incremental fact tables optimized for BI consumption.



 Key Engineering Challenges Solved

 1. Identity Resolution & System Drift
 The Problem: 20% of casino floor patrons use a new `CASINO-NEW` ID system, while the rest use legacy `HOTEL` IDs, creating siloed behavioral data.
 The Solution: The `int_guest_identity` model leverages `dbt_utils.generate_surrogate_key` to merge and hash IDs, creating a permanent, stable `global_guest_sk` that bridges the two systems seamlessly for downstream BI.

 2. Late-Arriving Data (Offline Slot Machines)
 The Problem: 5% of casino spin records arrive 48 hours late due to offline or disconnected slot machines. Rebuilding massive fact tables daily is computationally expensive.
 The Solution: The `fct_gaming_revenue` model uses an `incremental` materialization strategy with a dynamic 3-day lookback window (`INTERVAL 3 DAY`). This efficiently absorbs delayed payloads without requiring full table rebuilds.

 3. Historical Integrity (SCD Type 2)
 The Problem: When a hotel guest upgrades their loyalty tier (e.g., Gold to VIP), traditional overwrites destroy historical state, ruining point-in-time revenue analysis.
 The Solution: Implemented a dbt Snapshot (`snp_hotel_guests`) that monitors the `updated_at` timestamp to automatically manage `valid_from` and `valid_to` records. This is subsequently joined in the `dim_guest` conformed dimension to provide an accurate historical ledger.

 4. Idempotent Ingestion
 The Problem: Pipeline failures or duplicate triggers can result in duplicated warehouse data.
 The Solution: The Bronze ingestion script enforces `WRITE_TRUNCATE` logic (or partition replacement in production) combined with downstream Silver layer deduplication, ensuring the pipeline can be rerun infinitely without data duplication.



 Project Structure
```text
nwr_pipeline/
├── 1_generate_data.py              Synthetic data generator (Edge cases included)
├── 2_ingest_to_bronze.py           GCS to BigQuery idempotent loader
├── dbt_project.yml                 dbt configuration
├── packages.yml                    dbt-utils dependency
├── snapshots/
│   └── snp_hotel_guests.sql        SCD Type 2 tracking
├── models/
│   ├── sources.yml                 Bronze layer mappings
│   ├── schema.yml                  Data dictionary & primary key tests
│   ├── silver/
│   │   ├── slv_hotel_guests.sql
│   │   └── slv_casino_spins.sql
│   ├── intermediate/
│   │   └── int_guest_identity.sql  Surrogate key generation
│   └── gold/
│       ├── dim_guest.sql           Conformed SCD Type 2 dimension
│       └── fct_gaming_revenue.sql  Incremental fact table
```



 Runbook / Execution

1. Infrastructure Setup:
 Authenticate locally: `gcloud auth application-default login`
 Update project IDs and bucket names in `2_ingest_to_bronze.py` and `sources.yml`.

2. Generate & Ingest Data:
```bash
python 1_generate_data.py
python 2_ingest_to_bronze.py
```

3. Build the Transformations:
```bash
dbt deps
dbt snapshot
dbt run
```

4. Data Governance & Testing:
```bash
dbt test
dbt docs generate
dbt docs serve
```

 Production Roadmap & Enterprise Governance
While this repository demonstrates the core Medallion data transformations, deploying this to NWR's production environment requires surrounding the logic with enterprise-grade governance. Below is the architecture I would implement to scale this pipeline for a full engineering team.

1. Orchestration & Observability (Pipeline Health)
 Cloud Composer (Airflow): Transition the local Python ingestion scripts into containerized Airflow DAGs triggered by GCS bucket events (Cloud Pub/Sub).
 dbt Artifacts & Alerting: Integrate `dbt-expectations` for anomaly detection on gaming revenue margins. Route dbt run failures and data quality test drops directly to a dedicated Slack/Teams incident triage channel.

2. CI/CD & Code Quality (Engineering Culture)
 Slim CI: Configure GitHub Actions to run a "Slim CI" process on pull requests, ensuring dbt only builds and tests the models modified by the developer, saving BigQuery compute costs.
 Automated Linting: Enforce consistent SQL styling across the team by integrating `SQLFluff` into the pre-commit hooks, reducing code review friction and accelerating PR approvals.

3. Data Contracts (Stakeholder Velocity)
 API Constraints: Establish strict JSON schemas (Data Contracts) with the NWR App Engineering teams to ensure upstream schema drift breaks at the CI level before it can corrupt the downstream analytical models.
 BI Handoff: Expose the `dim_guest` and `fct_gaming_revenue` models to Tableau/Looker through a dedicated BigQuery BI service account with strict row-level security (RLS) masking PII for non-executive users.