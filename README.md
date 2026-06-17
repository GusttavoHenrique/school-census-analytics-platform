# School Census Analytics Platform

This repository contains the end-to-end data pipeline developed to automate the ingestion, processing, and analytical modeling of the Brazilian School Census Microdata published by INEP.

The solution was designed as a metadata-driven, one-shot pipeline capable of downloading, extracting, loading, and transforming raw census data into analytical structures optimized for reporting and business intelligence use cases.

---

## 1. Problem Context & Scope

### The Engineering Challenges
The Brazilian School Census is the primary statistical research vehicle for basic education in Brazil. While the data is publicly available, consuming it in a production-grade environment introduces several engineering challenges:
* **Distribution Format:** Data is delivered through large ZIP archives containing nested and inconsistent directory structures that vary between years.
* **Legacy Layouts:** Source CSV files utilize non-standard semicolons (`;`) instead of commas as delimiters.
* **Character Encoding:** Files are encoded natively using `Latin-1` (ISO-8859-1), requiring special handling during ingestion to prevent text corruption.
* **Complex Data Models:** The raw datasets contain thousands of unindexed sparse attributes spread across multiple entities, making direct analytical consumption highly inefficient.
* **Large Volumes:** Loading large CSV files through traditional row-by-row or database-abstracted insertion methods creates significant network and memory performance bottlenecks.

### Objective & Implemented Solution
The goal of this challenge was to build a unified, automated data pipeline capable of handling the entire lifecycle of School Census data through a single execution context:
1. Download raw data directly from the INEP portal (with automated fallback clients to handle network instabilities).
2. Extract and isolate only the specific files required by the challenge scope.
3. Standardize file paths, table schemas, and column naming conventions.
4. Load raw records into a cloud PostgreSQL cluster using high-throughput ingestion strategies.
5. Transform staging data into highly optimized Star Schema dimensional models.
6. Materialize analytics views to dynamically compute educational infrastructure and operational metrics requested by the challenge.

---

## 2. Technology Stack

| Component | Technology | Application in the Project |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core pipeline orchestration, extraction, ingestion, and execution flows |
| **Database** | PostgreSQL | Storage engine for staging schemas and the analytical data warehouse |
| **Cloud Database** | Neon / Supabase | Serverless managed PostgreSQL cloud infrastructure |
| **Transformations** | SQL | Analytics modeling, relational joins, and metric view generation |
| **Version Control** | Git / GitHub | Source code management, configuration history, and schema tracking |
| **HTTP Client** | Requests | Automated programmatic download of remote census source files |
| **Compression** | ZipFile | Low-level streaming decompression and file filtering of archives |
| **Database Access** | SQLAlchemy | Connection pool management, engine abstraction, and transaction control |
| **Bulk Load Engine**| PostgreSQL COPY | High-performance streaming of raw CSV arrays directly into database memory |
| **Data Processing** | Regex (`re`) / JSON | Metadata extraction, string normalization, and declarative column mappings |
| **Configuration** | Dotenv / JSON | Environment configuration variables and metadata-driven transformations |

---

## 3. Project Structure

```text
school-census-analytics-platform/
│
├── config/
│   └── analytics_table_mappings.json
│
├── data/
│   ├── landing/
│   │   └── microdados_censo_escolar/
│   │       ├── docente/
│   │       │   └── 2025/
│   │       │       ├── docente_1781640066.csv
│   │       │       └── docente_1781643135.csv
│   │       ├── escola/
│   │       ├── matricula/
│   │       └── turma/
│   └── raw/
│       └── microdados_censo_escolar/
│           └── microdados_censo_escolar_2025_zip
│
├── docs/
│   └── dicionário_dados_educação_básica.xlsx
│
├── sql/
│   ├── 01_create_static_dimensions.sql
│   ├── 02_create_analytics_table.sql
│   ├── 03_load_analytics_table.sql
│   └── 04_create_metrics_views.sql
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── extract.py
│   ├── load.py
│   ├── main.py
│   ├── sql_render.py
│   ├── transform.py
│   └── utils.py
│
├── .env
├── .gitignore
├── .neon
├── Makefile
├── README.md
└── requirements.txt

```

### File Responsibilities

#### Configuration

* `config/analytics_table_mappings.json`: Declarative, metadata-driven mapping between source schemas and analytical destination targets.
* `src/config.py`: Centralized configuration manager handling loggers, database target schemas, and safe environment variable injection.

#### Extraction

* `src/extract.py`: Manages network download streams, low-level ZIP decompression, file pattern filtering, and storage mapping.

#### Database

* `src/database.py`: Handles low-level database connection lifecycle management, raw DDL/DML script executions, and schema truncation logic.

#### Loading

* `src/load.py`: Orchestrates runtime database-side target staging table initialization and high-throughput bulk insertions.

#### Transformations

* `src/transform.py`: Coordinates analytics table updates and triggers dimensional warehousing queries.
* `src/sql_render.py`: Handles file-system SQL template tracking, parameter injections, and query rendering.

#### Utilities

* `src/utils.py`: String normalization helpers, regex parsing engines, and schema metadata extractors.

#### SQL Templates

* `sql/01_create_static_dimensions.sql`: Establishes static dimension constraints and lookups.
* `sql/02_create_analytics_table.sql`: Generates analytics schema structures, facts, and dimensional targets.
* `sql/03_load_analytics_table.sql`: Maps, transforms, and loads staging records into analytics structures.
* `sql/04_create_metrics_views.sql`: Materializes semantic layers for BI reporting toolsets.

#### Documentation

* `docs/dicionário_dados_educação_básica.xlsx`: Official INEP data dictionary referenced during modeling and transformation phases.

---

## 4. Data Architecture & Design Decisions

### Data Flow

```text
INEP Portal
    │
    ▼
[ DATA LAKE SIMULATION ]
├── RAW Layer (data/raw/)
└── LANDING Layer (data/landing/)
    │
    ▼
[ DATA WAREHOUSE SIMULATION ]
├── STAGING Schema (PostgreSQL)
└── ANALYTICS Schema (PostgreSQL)
    │
    ▼
Analytics Views
    │
    ▼
BI / SQL Consumers
(DBeaver, Metabase, Superset, Power BI, etc.)

```

---

### Architectural Design & Paradigm Simulation

An intentional architectural choice was made to structure the project as a mini modern ecosystem, simulating corporate big data environments within a single project volume:

* **Data Lake Simulation (File System Layer):** The physical file system separation under the `data/` path functions as a simplified Data Lake. The `raw/` directory acts as the unstructured ingest core, while the `landing/` directory maps to a processed file repository.
* **Data Warehouse Simulation (Database Layer):** The implementation of logical PostgreSQL schemas (`staging` and `analytics`) reflects a traditional corporate Data Warehouse lifecycle. Staging provides raw, standardized landing schemas, while Analytics hosts production-ready dimensional abstractions.

---

### Layer Details

#### Raw Layer

Acts as the physical ingestion point for the original multi-gigabyte compressed `.zip` matrix extracted from INEP.

* **Design Decision & Data Lifecycle:** Unlike transient systems that delete temporary network components dynamically, the pipeline explicitly preserves the downloaded ZIP container under `data/raw/` to avoid unnecessary network overhead and re-downloads during local code debugging. **The files are kept structurally intact until a subsequent execution triggers a full replacement (overwrite) with a newer ZIP package.**

#### Landing Layer

The landing repository manages structured file auditing and local storage persistence.

```text
data/landing/microdados_censo_escolar/docente/2025/

```

* **Design Decision:** Rather than overwriting existing datasets, **every extraction run writes a new table-specific CSV file suffixed with a unique Unix timestamp** (e.g., `docente_1781640066.csv`). This approach maintains strict file-level idempotence, facilitates auditing, and supports clean historical backfills on local volumes.
* **Testing Scope:** Pipeline validation and end-to-end integration tests were performed specifically using the **2025** data structure.

#### Staging Layer

Implemented as a PostgreSQL schema named `staging`. It acts as an internal reflection of the source files while standardizing structure and text properties.

* **Case Standardization:** All column headers and table identifiers are systematically converted to `lowercase snake_case` (e.g., `CO_ENTIDADE` is mutated into `co_entidade`).
* **High-Performance Ingestion & Re-run Safeguards:** To overcome the heavy memory consumption and network latency inherent in Pandas `.to_sql()` loops, ingestion uses the `psycopg2` driver interface to stream raw data files directly into database memory via PostgreSQL's native `COPY` framework:
```python
cursor.copy_expert("COPY staging.escola FROM stdin WITH CSV DELIMITER ';' ENCODING 'latin1'", file_object)
```


This shift minimizes the application memory footprint and cuts data ingestion down to a few seconds. **To completely prevent data duplication during pipeline re-runs, the database execution model executes a full purge of the target year's existing staging data before streaming the new payload. This ensures that re-triggering the same year completely overwrites and recreates the tables cleanly.**

#### Metadata-Driven Architecture (`analytics_table_mappings.json`)

The mapping strategy between the source datasets and the target models was decoupled into a declarative JSON configuration file (`analytics_table_mappings.json`).

* **Design Decision & Benefits:** Instead of hardcoding column aliases and structural selections inside the Python orchestration files or manual DDL definitions, the pipeline implements a **metadata-driven pattern**. This abstracts and simplifies the table normalization process, significantly reducing code duplication (boilerplate) across different data domains.
* **Impact on Scalability:** This abstraction isolates schema handling into a clean configuration contract. As a result, adding new entities, adapting to upstream layout variations, or altering structural business logic does not require code changes in the core extraction or loading scripts, keeping the codebase lean, decoupled, and easy to maintain.


#### Analytics Layer

Implemented as a PostgreSQL schema named `analytics`. This layer strips out operational complexity, exposing a denormalized Star Schema optimized for high-performance BI reporting.

* **Dimensions:** `dim_escola`, `dim_docente`, `dim_turma`, `dim_dependencia_administrativa`, `dim_localizacao`.
* **Facts:** `fato_matricula`.
* **Surrogate Key Strategy:** All analytical tables receive a surrogate key (`sk_*`) generated using PostgreSQL identity columns. Overriding the source operational natural keys (like `co_entidade`) decouples the data warehouse from brittle upstream conventions, prevents reporting breaks during structural source updates, and lays the groundwork for *Slowly Changing Dimensions* (SCD Type 2).
* **SQL Template Strategy:** Core business transformations are decoupled from Python code and maintained entirely within standalone, parameterized SQL scripts. This division of concerns improves script readability, simplifies long-term query maintenance, and mimics dbt-like modeling principles.

#### Analytics Views

After the analytical dimensional tables are populated, the pipeline automatically generates a set of SQL views responsible for exposing the exact business metrics requested by the challenge text.

These views encapsulate complex multi-table metrics aggregation logic and provide a simplified, pre-joined user interface for final data consumption without requiring end users to understand the underlying dimensional layouts. The views are created automatically at the tail end of the workflow through the execution of the `04_create_metrics_views.sql` script.

##### Implemented Views

| View Name | Purpose / Output Metric |
| --- | --- |
| `view_escolas_por_uf_dependencia` | Total number of schools segmented by federative state (UF) and administrative dependency (Federal, State, Municipal, Private) |
| `view_escolas_por_uf_localizacao` | Total number of schools broken down by state (UF) and geographic location zone (Urban / Rural) |
| `view_percentual_escolas_infraestrutura` | Operational infrastructure coverage indicators tracking ratios for water, electricity, internet access, science labs, libraries, and accessibility configurations |
| `view_turmas_por_escola_uf` | Total classroom volume and calculated averages of class sizes per school grouped across state (UF) lines |
| `view_matriculas_por_uf_dependencia` | Total student enrollment records by state (UF) and administrative dependency group |
| `view_razao_alunos_por_turma` | Operational student-to-class size ratio evaluation matrices across states |

##### Querying the Results

Once the pipeline execution finishes, all analytical tables and views become immediately available in the PostgreSQL database. Any standard SQL client can be used to explore the results, including:

* DBeaver
* DataGrip
* pgAdmin

For this project, **DBeaver** was used as the primary database management client to handle:

* Initial exploratory data analysis (EDA)
* Empirical code validation of core transformation rules
* Manual inspection of data state layout changes inside staging and analytics schemas
* Integrity testing of generated metric views

**Example Query Execution:**

```sql
SELECT *
FROM analytics.view_escolas_por_uf_dependencia
ORDER BY quantidade_escolas DESC;
```

---

## 5. How to Run

### Prerequisites

* Python 3.10+
* Active PostgreSQL instance (Neon, Supabase, or local Docker)
* Stable internet access

### 1. Clone the Repository and Enter the Directory

```bash
git clone <repository-url>
cd school-census-analytics-platform
```

### 2. Configure Environment Variables

Create an environment file named `.env` in the root directory of the project. Fill it with the exact configuration block below:

```env
DATASET_URL=[https://download.inep.gov.br/dados_abertos](https://download.inep.gov.br/dados_abertos)
DATASET_NAME=microdados_censo_escolar
DATA_FILE_DIR=dados
SELECTED_FILE_KEYWORDS=TABELA_ESCOLA,tabela_turma,Tabela_Matricula,Tabela_Docente_2025

DATABASE_URL=postgresql://channel_binding=require
```

> ⚠️ **Security Notice:** For security compliance and to prevent unauthorized access to the database cluster, the full `DATABASE_URL` credentials string was **sent exclusively via email** alongside the submission link for this project. Please retrieve the connection string from your inbox and replace the placeholder above.

### 3. Install Dependencies

```bash
make install
```

### 4. Execute the One-Shot Pipeline

To execute the download, extraction, load, and SQL transform phases for a specific year:

```bash
make run YEAR=2025
```

To purge stale database schemas and force a clean, from-scratch run:

```bash
make run YEAR=2025 RESET_DB=true
```

### 5. Clean Filesystem (Optional Shortcut)

* **Clean Filesystem:** Wipes temporary landing caches, log traces, and Python caching footprints:
```bash
make clean
```



### Expected Output

Following a successful operational execution, the relational database engine targets will contain the following structured schema blocks, fully materialized and ready for consumption:

```text
staging/
├── escola (Table)
├── docente (Table)
├── turma (Table)
└── matricula (Table)

analytics/
├── dim_escola (Table)
├── dim_docente (Table)
├── dim_turma (Table)
├── dim_dependencia_administrativa (Table)
├── dim_localizacao (Table)
├── fato_matricula (Table)
│
├── view_escolas_por_uf_dependencia (View)
├── view_escolas_por_uf_localizacao (View)
├── view_percentual_escolas_infraestrutura (View)
├── view_turmas_por_escola_uf (View)
├── view_matriculas_por_uf_dependencia (View)
└── view_razao_alunos_por_turma (View)
```

These relational elements can be extracted, joined, or monitored directly through any standard Postgres-compatible client connection block.

---

## 6. Troubleshooting

### SSL Download Errors

* **Symptom:** Outbound network connection blocks during download handshakes due to certificate authentication issues on the INEP host servers.
* **Resolution:** The extraction client embeds an automatic exception handling routine. If an SSL handshake failure is caught, it flags a warning log and immediately retries the stream with validation disabled (`verify=False`).

### Database Storage Limits

* **Symptom:** Transactions are rolled back with errors such as `DiskFull` or database size quotas exceeded (common on free cloud computing database tiers like Neon).
* **Resolution:** Scale down processing boundaries to the narrow geographic regions required by the MVP test scope and ensure execution runs pass the reset parameter to flush old tests:
```bash
make run YEAR=2025 RESET_DB=true
```


---

## 7. Known Limitations & Scope Discrepancies

* **Single-Year Runtime Blocks:** Each individual pipeline execution handles one specific target reference year at a time.
* **Data Quality Scope:** Data quality checking and schema constraint enforcements were kept lightweight to fit the boundaries of a rapid MVP challenge scope.
* **Schema Drift (2025 vs. Prior Years):** Development, testing, and mapping configurations were restricted strictly to the 2025 data schema. During testing, clear structural changes and column layout modifications were observed between the 2025 data files and prior historical releases. Running the pipeline for years prior to 2025 will require updates to the `analytics_table_mappings.json` metadata rules.
* **Staging Schema Typing (`TEXT` Abstraction):** Columns inside the staging layer are intentionally ingested as generic `TEXT` values to guarantee schema flexibility and protect the pipeline from breaking when source fields change shapes unexpectedly. In a production state, this should be optimized by applying **strict typing** (casting numeric indicators to `INT`/`NUMERIC` and flag tags to `BOOLEAN`) to reduce the relational storage footprint and optimize index scanning performance.
* **Full-Overwrite Reload Strategy:** While the current pipeline safely guarantees zero data duplication by dropping and recreating all relevant records for the target year on each execution, this overwrite model creates unnecessary network and database overhead. An ideal optimization would be transitioning toward a **strictly incremental execution model**, computing delta changes via metadata markers (e.g., `last_modified` fields) to ingest and transform only records that have been modified or added since the previous run.

---

## 8. Conceptual Design Answers

As per the requirements of Section 7 of the technical case, below are the architectural designs for scaling, deduplication, and stakeholder enablement.

### Q5: Daily Data Updates Design

To transition this one-shot pipeline into a production-grade automated daily system, I would use an orchestrator alongside cloud native tools:

```text
[Cron / Event Trigger] ──► [Apache Airflow DAG] ──► [AWS Glue Python Shell] ──► [PostgreSQL]
```

1. **Orchestration Tooling:** Use **Apache Airflow** or **Prefect** to manage the pipeline dependencies. A daily DAG would run at off-peak hours (e.g., 2:00 AM) to pull incremental changes.
2. **Compute Transition:** Wrap the current script inside an execution task such as an **AWS Glue Python Shell** job or a containerized instance running on **AWS ECS Fargate**.
3. **API-Driven Ingestion:** Since INEP data releases are typically annual, a true daily process for an enterprise system implies integrating an internal operational source database. The orchestrator would request data via a REST API or execute an optimized delta query against upstream database tables using updated fields like `updated_at > {{ ds }}`.

### Q6: Data Deduplication Strategy

To maintain an idempotent pipeline where re-running the system does not double-count metrics, I would implement a **two-phase deduplication layer** at the database level:

```text
[Raw Landing File] ──► [Staging Table] ──► [Upsert Join (MERGE)] ──► [Analytics Target]
                                                     ▲
                                        (Drop Duplicates via window functions)
```

1. **Staging Isolation (Transient Ingestion):** The high-performance `COPY` command would always target a clean staging table. Inside staging, duplicate raw rows are isolated using SQL window functions before processing:
```sql
WITH ranked_data AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY co_entidade ORDER BY ingestion_timestamp DESC) as rn
    FROM staging.escola
)
SELECT * FROM ranked_data WHERE rn = 1;
```


2. **Idempotent Upsert (MERGE Pattern):** When writing into final dimension and fact models, native PostgreSQL `INSERT ... ON CONFLICT` clauses are executed:
```sql
INSERT INTO analytics.dim_escola (co_entidade, nu_ano, no_escola)
SELECT co_entidade, nu_ano, no_escola FROM staging.clean_escola
ON CONFLICT (co_entidade) 
DO UPDATE SET 
    no_escola = EXCLUDED.no_escola,
    updated_at = NOW();
```


This ensures that even if identical files are processed multiple times, records are safely updated rather than duplicated.

### Q7: Metabase Stakeholder Enablement

To empower business users to query data reliably without needing deep SQL skills or risking metric drift, I would design a semantic model layer:

```text
[Analytics Star Schema Engine] ──► [Metabase Semantic Views] ──► [Business Users Self-Service]
```

1. **Abstract Complexity via Views:** I hide complex multi-table joins behind flattened semantic database views (e.g., the final `analytics.view_*` aggregates developed in this challenge). Users see clear columns (e.g., `Has Internet`, `Total Classrooms`) rather than needing to manually compute counts or map bitmasks.
2. **Metabase Metadata Caching & Labeling:** Inside Metabase, I would configure custom column aliases, explicit tooltips, and category definitions (e.g., marking `co_uf` explicitly as a State entity).
3. **Pre-Baked Questions & Model Definitions:** Use Metabase's official **Models** feature to pre-join the Fact tables to the appropriate Dimensions. This creates a standard interface for drag-and-drop filtering, ensuring non-technical stakeholders always query the canonical, verified metric logic.

---

## 9. Architecture Evolution: Scaling to Production

Transitioning this standalone local script into an enterprise Big Data platform would focus on migrating the compute and ingestion paths to the AWS Cloud infrastructure.

### 1. Near Real-Time Ingestion (CDC)

Future revisions would replace manual file scraping and automated site downloads with streaming log-based Change Data Capture (CDC). Utilizing tools like **AWS DMS** or **Debezium** to track write-ahead logs of operational databases eliminates heavy network scraping and completely removes resource draw from core operational apps.

### 2. Cloud Lakehouse Integration (AWS S3 Medallion Architecture)

Data storage would shift from local disk space to a flexible cloud architecture using an **AWS S3 Medallion Data Lake Pattern**:

* **Bronze Layer:** Acts as an append-only, immutable storage layer capturing source records exactly as received, building a permanent data auditing track.
* **Silver Layer:** Processes and cleans raw data using distributed Spark compute layers (AWS Glue or Amazon EMR). Tasks include character normalization, strict typing alignment, and complex **record deduplication**, converting outputs into optimized columnar formats like Apache Parquet or Delta Lake.
* **Gold Layer:** Builds the final, business-ready Star Schema. Data models inside the Gold layer are queried serverless using **Amazon Athena**, providing quick, low-latency access for business intelligence engines like Metabase.

### 3. Data Governance & Security

Production environments would introduce centralized access tracking frameworks using **AWS Lake Formation** to enforce **ABAC (Attribute-Based Access Control)** patterns. This configuration enables granular row-level data filtering and column-level masking, ensuring that sensitive student profiles or teacher attributes are automatically hidden based on the security level of the user or connected dashboard.

---

## 10. AI Usage Statement

Generative AI (primarily ChatGPT) was used as a technical co-pilot throughout the project. The development process remained entirely iterative and engineering-driven: code was built block by block, using AI to eliminate boilerplate friction, speed up repetitive coding, and evaluate modeling trade-offs—mimicking a modern day-to-day data engineering workflow. Crucially, **human engineering oversight drove all final architectural decisions, testing validation, and system corrections**.

### Where AI Was Used

#### Data Modeling

* Crafting column configuration mapping structures.
* Accelerating large-scale translation arrays for headers.
* Brainstorming dimension design approaches and tracking surrogate key alternatives.

#### Architecture

* Defining modular layout boundaries for layers (`raw`, `landing`, `staging`, `analytics`).
* Designing table-specific data lifecycle tracks using **timestamp-driven version control in the landing layer** while treating raw ZIP blocks as ephemeral.

#### Ingestion Logic

* Scaffolding file navigation methods inside compressed ZIP objects.
* Handling lower-level file manipulation scripts and character encoding setup.

#### Transformation Logic

* Drafting initial structural query blocks for SQL templates.
* Constructing regular expression filters and parsing case normalization methods (`snake_case`).

#### Debugging & Support

* Isolating root causes for network SSL handshakes.
* Interpreting Postgres transaction failures and optimizing database storage thresholds.

#### Documentation

* Drafting function docstrings, README structural blocks, and compiling core technical design summaries.

### What Worked Well

* **Velocity Acceleration:** Drastically cut down the time required to write boilerplate utilities, manage tedious string mutations, and construct complex regular expressions, allowing more engineering hours to be spent on data quality and system design.
* **Architectural Brainstorming:** Provided an agile, responsive utility to quickly compare alternative technical approaches regarding data modeling limits and ingestion alternatives.
* **Consistent Documentation:** Standardized explanations, structured coherent code comments, and systematically recorded design choices across the code base.

### Where AI Was Wrong and How It Was Corrected

#### 1. Overriding Layout Hallucinations

* **The Issue:** The AI frequently suggested column names and attributes that simply did not exist in the actual INEP files or data dictionaries.
* **The Correction:** Discrepancies were identified by cross-checking layouts against documentation before writing DDL constraints, and the fictional fields were removed manually.

#### 2. Replacing Inefficient Ingestion Patterns

* **The Issue:** Initial AI suggestions relied heavily on iterative Pandas structures to handle PostgreSQL uploads. Performance testing exposed critical latency and memory bottlenecks on medium-to-large files.
* **The Correction:** Replaced the approach with a high-throughput streaming architecture utilizing `psycopg2` and native database `COPY` functions, slashing load times down to seconds.

#### 3. Handling Regex Edge Case Failures

* **The Issue:** Generated regular expression strings failed to handle complex variations in file paths and school name metadata, dropping valid entries during processing.
* **The Correction:** Gaps were caught through validation testing against actual datasets; the expressions were manually rewritten with precise string boundary conditions.

#### 4. Correcting Directory Traversal Logic

* **The Issue:** Early code generated to locate target items within nested ZIP directories ran into structural errors, failing to navigate the files correctly and returning empty arrays.
* **The Correction:** Inspected the actual directory configurations using execution logs, manually rewrote the search script parameters, and mapped the navigation path to the proper directories.

#### 5. Eradicating Code Duplication

* **The Issue:** The AI repeatedly generated duplicated boilerplate code for database connections and queries across different functional scripts.
* **The Correction:** Intervened to enforce the **DRY (Don't Repeat Yourself)** principle, refactoring the platform's layout to isolate shared infrastructure rules inside dedicated reusable modules like `database.py`, `sql_render.py`, and `utils.py`.