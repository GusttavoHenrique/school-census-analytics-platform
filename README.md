# School Census Analytics Platform

This repository contains the end-to-end data pipeline developed to automate the ingestion, processing, and analytical modeling of the Brazilian School Census Microdata provided by INEP.

---

## 1. Problem Context & Scope

### The Engineering Challenges
The School Census is the primary statistical research vehicle for basic education in Brazil. However, consuming its raw datasets in a production environment introduces several well-known friction points:
* **Distribution Format:** Data is delivered in massive ZIP archives with nested and inconsistent directory structures that change from year to year.
* **Legacy Layouts:** Raw CSV files utilize non-standard semicolons (`;`) as delimiters.
* **Character Encoding:** Text data is natively encoded in `Latin-1` (ISO-8859-1), requiring proper handling to avoid character corruption inside the database.
* **Data Modeling:** The source tables are heavily normalized but contain thousands of unindexed sparse columns, making them highly inefficient for direct analytical queries.

### Objective & Implemented Solution
The goal was to build a unified **one-shot** pipeline in Python and SQL that handles this entire lifecycle via a single terminal execution:
1. Downloads source data directly from the INEP portal (with automated fallback mechanisms to handle network instabilities).
2. Extracts and isolates the specific files defined within the project scope.
3. Standardizes data types, encodings, and nomenclatures to match database conventions.
4. Loads the raw records into a PostgreSQL instance using high-throughput ingestion strategies.
5. Executes SQL transformations to consolidate a Star Schema dimensional model tailored for BI consumption.

---

## 2. Technology Stack

| Component | Technology | Application in the Project |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core pipeline orchestration, programmatic download, and file parsing |
| **Database** | PostgreSQL | Storage engine for staging tables and the analytical data warehouse |
| **DB Infrastructure**| Neon / Supabase | Serverless cloud-managed PostgreSQL instance |
| **Transformation** | SQL | Dimensional modeling scripts, analytics views, and metrics aggregates |
| **Version Control** | Git / GitHub | Code management, configuration tracking, and schema versioning |
| **Local Ingestion** | Requests / ZipFile | Automated HTTP file streaming and selective disk decompression |
| **Drivers / ORM** | Psycopg2 / SQLAlchemy | Connection pool management and transactional boundary control |
| **Bulk Load Engine**| `copy_expert` (COPY) | High-throughput streaming of raw CSV data directly into Postgres |
| **Data Processing** | Pandas / Regex (`re`) | Basic metadata schema checks and string cleaning/parsing via Regex |
| **Configuration** | JSON / Dotenv | Declarative column-to-table mappings and secure credential management |

---

## 3. Data Architecture & Design Decisions

### Data Flow

```text
       ┌────────────────────────┐
       │      INEP Portal       │
       └───────────┬────────────┘
                   │  (Automated HTTPS Stream)
                   ▼
       ┌────────────────────────┐
       │       RAW Layer        │ -> Ephemeral ZIP file (purged post-extraction)
       └───────────┬────────────┘
                   │  (ZipFile Extraction & Filtering)
                   ▼
       ┌────────────────────────┐
       │     LANDING Layer      │ -> Local CSV persistence with Unix Timestamps
       └───────────┬────────────┘
                   │  (Streaming via Postgres COPY)
                   ▼
       ┌────────────────────────┐
       │     STAGING Layer      │ -> Clean tables inside Postgres (Schema: staging)
       └───────────┬────────────┘
                   │  (SQL Transformations / Dimensional Modeling)
                   ▼
       ┌────────────────────────┐
       │    ANALYTICS Layer     │ -> Fact & Dimension tables (Schema: analytics)
       └────────────────────────┘

```

---

### Layer Breakdown

#### Raw Layer

Acts as the landing zone for the raw `.zip` asset downloaded from INEP.

* **Design Decision:** To optimize local disk space and prevent storage overhead, **the original ZIP archive is treated as an ephemeral asset and completely deleted immediately after the target files are extracted**.

#### Landing Layer

Because the Raw layer is ephemeral, data versioning and auditing live here. The extracted CSV files are organized by entity and reference year:

```text
landing/microdados_censo_escolar/escola/2025/

```

* **Versioning Strategy:** Rather than overwriting data, **every extraction run saves a new table-specific CSV file appended with a unique Unix timestamp suffix** (e.g., `escola_1781632440.csv`). This approach ensures idempotence and provides a clean file-based audit trail without the risk of overlapping previous executions.

#### Staging Layer (Database)

This layer handles initial schema definition inside the PostgreSQL instance under the `staging` schema.

* **Case Standardization:** All column titles and table identifiers are programmatically mutated to `lowercase snake_case` (e.g., `CO_ENTIDADE` is parsed into `co_entidade`).
* **Regex Integration:** Regular expressions are used to sanitize file path strings, extract timestamps from execution logs, and clean invalid characters from headers prior to schema injection.
* **Overcoming Ingestion Bottlenecks:** Initial prototypes relying on Pandas iterative loops or standard `.to_sql()` blocks faced significant latency and memory overhead on larger tables. The solution was refactored to use `psycopg2`'s lower-level interface, opening a high-throughput stream utilizing PostgreSQL's native `COPY` command:
```python
cursor.copy_expert("COPY staging.escola FROM STDIN WITH CSV DELIMITER ';' ENCODING 'latin1'", file_object)

```


This shift minimized the application memory footprint and cut the load time down to a few seconds.

#### Analytics Layer (Data Warehouse)

This layer transforms staging data into an optimized Star Schema model designed to simplify query writing for downstream BI tools.

* **Dimensions Built:** `dim_escola`, `dim_docente`, `dim_turma`, `dim_dependencia_administrativa`, `dim_localizacao`.
* **Fact Table:** `fato_matricula`.
* **Surrogate Keys (`sk_`):** All analytical entities are joined using auto-incrementing identity keys (`GENERATED ALWAYS AS IDENTITY`). Overriding the source operational natural keys (like `co_entidade`) decouples the data warehouse from brittle upstream conventions, isolates the schema from unexpected layout changes, and lays the groundwork for *Slowly Changing Dimensions* (SCD Type 2).

---

## 4. How to Run the Project

### Prerequisites

* Python 3.10 or higher
* Active PostgreSQL instance (Neon, Supabase, or local Docker container)
* Stable internet access to stream source files

### 1. Clone the repository and enter the directory

```bash
git clone <repository-url>
cd school-census-analytics-platform

```

### 2. Configure environment variables

Create a `.env` file in the project root with your database connection parameters:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
DATASET_URL=[https://download.inep.gov.br/dados_abertos/microdados_censo_escolar](https://download.inep.gov.br/dados_abertos/microdados_censo_escolar)
DATASET_NAME=microdados_censo_escolar
DATA_FILE_DIR=dados
DATABASE_STAGING_SCHEMA=staging
DATABASE_ANALYTICS_SCHEMA=analytics

```

### 3. Execution via Makefile Commands

The project includes a `Makefile` to simplify environmental setup and pipeline orchestration. Below is the reference guide for all available shortcuts:

* **Install Environment Dependencies:**
Creates a virtual environment and installs all required Python packages and drivers.
```bash
make install

```


* **Run the Pipeline (Standard Batch Ingestion):**
Triggers the one-shot extraction, staging load, and analytical modeling workflow. You must pass the target execution year as an argument:
```bash
make run YEAR=2025

```


* **Force Database Reset Run:**
Purges all existing tables and active schemas inside the target database before executing a clean ingestion. Highly useful for resolving free-tier storage alerts or deploying manual DDL schema changes:
```bash
make run YEAR=2025 RESET_DB=true

```


* **Run Code Linters and Formatters (Optional):**
Ensures code quality and standardized indentation across Python scripts:
```bash
make lint

```


* **Clean Local Filesystem (Optional):**
Removes temporary landing data caches, local logs, and python bytecode objects:
```bash
make clean

```



---

## 5. Troubleshooting & Operational Support

### SSL Handshake Failures During Download

* **Symptom:** Network request exceptions thrown when handshaking with INEP servers due to upstream security certificate issues.
* **Resolution:** The download client implements an automated fallback mechanism. If a secure connection fails, the script catches the exception, logs a warning, and re-triggers the stream with strict validation disabled (`verify=False`) to ensure execution continuity.

### Storage Caps Reached (`DiskFull` / Size Limit Exceeded)

* **Symptom:** Database transactions error out when testing against cloud free tiers (like Neon's storage limits).
* **Resolution:** Limit execution to the subset scope suggested by the challenge rules (focusing on Schools and Classes within specific boundaries) and ensure you use the `RESET_DB=true` flag to drop residual historical testing schemas.

### Character Encoding Failures

* **Symptom:** Strings appear broken or cause database input exceptions during staging insertion.
* **Resolution:** The underlying ingestion layer enforces strict `Latin-1` decoding parameters during filesystem data piping, standardizing text inputs to `UTF-8` on database commit. Ensure all supplementary extensions default to `encoding="latin1"` when testing modules in isolation.

---

## 6. Architecture Evolution: Scaling to Production (AWS Cloud)

While the current batch solution fulfills the local script requirements, scaling this architecture to an enterprise-grade Big Data platform would leverage the following cloud data roadmap on AWS:

1. **Near Real-Time Ingestion (CDC):** Replace scheduled manual file downloads with log-based Change Data Capture (CDC) utilizing **AWS DMS** or **Debezium**, tracking transactional database write-ahead logs to eliminate application-tier overhead.
2. **Modern Data Lakehouse (S3 Medallion Architecture):**
* **Bronze:** Append-only storage of the raw extracted data files on AWS S3 in their native layout.
* **Silver:** Distributed data processing via PySpark (AWS Glue or EMR) dedicated to encoding standardization, schema validation, and rigorous **record deduplication**, saving outputs in compressed columnar formats (Apache Parquet / Delta Lake).
* **Gold:** Consolidate the Fact and Dimension tables within the S3 Gold layer, using **Amazon Athena** as a serverless query engine to expose data to BI platforms like Metabase.


3. **Data Governance & Granular Security (ABAC):** Implement **AWS Lake Formation** to enforce Attribute-Based Access Control policies. This enables column-level masking and row-level filtering, dynamically obscuring sensitive student or teacher identifiers based on the explicit security tags of the consuming employee or dashboard.

---

## 7. Project Development and AI Usage Statement

This pipeline was built following an incremental, iterative approach. The code was developed block by block, employing Generative AI (ChatGPT) as a technical co-pilot to eliminate boilerplate friction, speed up repetitive tasks, and evaluate modeling trade-offs—mimicking a modern day-to-day data engineering workflow. Crucially, **human engineering oversight drove all final design, testing, and system verification decisions**.

### 7.1 Automated Workstreams and Contributions

* **Metadata Schema Mapping:** Accelerating the creation of the structured configuration JSON files that map INEP's spreadsheet-based data dictionaries into valid database targets.
* **Extraction & Path Traversal Logic:** Building functions to parse nested, variable folder layouts inside compressed ZIP objects for selective extraction.
* **Text Processing & Cleaning:** Generating regular expressions (Regex) to handle string sanitization and convert legacy source headers into clean `snake_case`.
* **SQL Generation:** Drafting initial parameterized SQL templates and designing analytical views to map challenge metrics.
* **Documentation:** Scaffolding the structural foundation of docstrings and the README blueprint.

### 7.2 Core Successes and Efficiency Gains

* **Velocity Gains:** Significantly lowered the time spent writing boilerplate utility logic, handling string mutations, and constructing complex Regex patterns. This freed up engineering bandwidth to focus on schema design and data validity.
* **Design Brainstorming:** Provided an efficient technical sounding board to quickly weigh storage layer alternatives and compare key modeling choices.

### 7.3 Overriding AI Errors: Critical Engineering Oversight

The co-pilot was prone to generating inaccuracies, code duplications, and patterns that conflicted with production-grade data engineering principles, requiring explicit manual overrides:

* **Correcting Layout Hallucinations:** The AI frequently suggested column names and attributes that simply did not exist in the actual INEP files or data dictionaries. These fields were caught via manual layout checks and stripped out from mapping configurations.
* **Replacing Inefficient Ingestion Patterns:** The AI initially pushed for heavy use of Pandas loops to ingest data into PostgreSQL. Recognizing the clear performance bottleneck on medium-to-large datasets, I refactored the pipeline to use Python’s low-level `psycopg2` API combined with the native database `copy_expert` command, cutting ingestion times to seconds.
* **Fixing Edge-Case Parsing Failures:** Early regex scripts and folder path-finding helpers failed when processing complex naming patterns or deep directory structures, yielding empty file lists. These bugs were isolated via test execution logs and corrected manually.
* **Refactoring Redundant Implementations:** The AI tended to duplicate tasks across files, such as initializing database connections inside separate modules. I intervened to enforce the **DRY (Don't Repeat Yourself)** principle, decoupling connection rules into a single centralized `database.py` script.