# Retail Sales Data Pipeline

End-to-end ETL data pipeline for processing retail sales data using Python, PostgreSQL, Docker, and Apache Airflow.

## Overview

This project implements an end-to-end ETL data pipeline for processing the Online Retail dataset.

The pipeline extracts raw sales data from an Excel file, applies data cleaning and business rules, separates valid sales from rejected records, and loads the processed data into PostgreSQL.

Apache Airflow orchestrates the workflow, while Docker provides a reproducible environment for the different services.

The pipeline also includes data quality checks, post-load validation, automatic retries, scheduling, and email notifications when a task fails.

## Architecture

The pipeline follows the architecture below:

```text
                    ┌─────────────────────┐
                    │ Online Retail XLSX  │
                    │      Raw Data       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       EXTRACT       │
                    │   Python / Pandas   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      TRANSFORM      │
                    │ Cleaning + Business │
                    │ Rules + Data Quality│
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌─────────────┐       ┌─────────────┐
             │ Clean Sales │       │  Rejected   │
             │    Data     │       │    Data     │
             └──────┬──────┘       └──────┬──────┘
                    │                     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │        LOAD         │
                    │     PostgreSQL      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    VALIDATE LOAD    │
                    │ Post-load checks    │
                    └─────────────────────┘

              Apache Airflow orchestrates the DAG
              Docker runs the required services
              SMTP sends failure notifications
```

## Tech Stack

- **Python** — ETL logic and data processing
- **Pandas** — Data extraction, transformation, and cleaning
- **PostgreSQL** — Storage of clean and rejected data
- **Apache Airflow** — Pipeline orchestration, scheduling, retries, and task dependencies
- **Docker & Docker Compose** — Containerization and service orchestration
- **SMTP / Gmail** — Email notifications when Airflow tasks fail
- **Git & GitHub** — Version control and remote repository

## Project Structure

```text
retail_sales_pipeline/
│
├── dags/
│   └── retail_sales_dag.py
│
├── scripts/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── validate.py
│   ├── database.py
│   ├── config.py
│   └── logger.py
│
├── sql/
│   └── schema.sql
│
├── data/
│   ├── raw/
│   └── processed/
│
├── Dockerfile
├── Dockerfile.airflow
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── .dockerignore
└── README.md
```

Ici, on documente **l'organisation du projet**. Par exemple :

```text
dags/
   → orchestration Airflow

scripts/
   → logique ETL et validation

sql/
   → structure PostgreSQL

data/raw/
   → données sources

data/processed/
   → données générées
```

## ETL Pipeline

### 1. Extract

The extraction stage reads the raw Online Retail Excel dataset using Pandas.

The source data is kept separate from processed data so that the original dataset remains unchanged.

### 2. Transform

The transformation stage applies data cleaning, business rules, and quality controls.

Transactions are classified into different types:

- `sale` — valid sales transactions
- `cancelled` — invoices whose number starts with `C`
- `stock_adjustment` — transactions with negative quantities
- `invalid_or_free` — transactions with a zero or negative unit price

The pipeline also:

- Detects duplicate transactions
- Identifies missing customer IDs
- Identifies missing descriptions
- Separates clean sales from rejected records
- Stores an `exclusion_reason` for rejected records
- Converts `CustomerID` into a string identifier
- Calculates the total transaction amount

The total amount is calculated as:

```text
total_amount = Quantity × UnitPrice
```

### 3. Load

The load stage writes the transformed datasets into PostgreSQL:

- `clean_sales` — valid sales transactions
- `rejected_sales` — excluded records with their rejection reason

PostgreSQL `COPY` is used for bulk loading instead of inserting records one by one.

The load runs inside a database transaction. If the operation succeeds, the transaction is committed. If an error occurs, the transaction is rolled back.

### 4. Validate Load

After loading, a dedicated Airflow task validates the data stored in PostgreSQL.

The validation compares the number of records produced by the transformation stage with the number of records actually stored in:

- `clean_sales`
- `rejected_sales`

If the expected and actual row counts differ, the validation task fails.


## Airflow Orchestration

Apache Airflow orchestrates the complete ETL workflow:

**extract → transform → load → validate_load**

Each stage is implemented as a separate Airflow task with explicit dependencies.

This architecture makes it possible to monitor each stage independently and identify exactly where a pipeline execution fails.

### Scheduling

The pipeline can be executed automatically according to the schedule configured in the Airflow DAG.

It can also be triggered manually from the Airflow web interface.

### Retries

Airflow automatically retries failed tasks according to the DAG configuration.

The current configuration uses:

- **2 retries**
- **5 minutes between retries**
- **3 maximum attempts in total**

When a task fails, Airflow retries that task without restarting upstream tasks that have already succeeded.

For example:

**extract ✅ → transform ✅ → load ❌ → retry load**

### Monitoring and Logging

Each Airflow task generates execution logs that can be inspected independently.

The logs provide information about:

- Extraction progress
- Transformation results
- Number of clean and rejected records
- PostgreSQL loading
- Data quality checks
- Post-load validation
- Errors and exceptions

### Failure Notifications

The pipeline includes automatic email notifications using SMTP.

When a task reaches a failure state, Airflow uses an `on_failure_callback` to trigger an email notification.

The notification flow is:

**Task Failure → on_failure_callback → SMTP Connection → Gmail Notification**

SMTP credentials and other sensitive configuration values are stored outside the source code and are excluded from Git.

## Docker Architecture

Docker is used to provide an isolated and reproducible environment for the pipeline.

Docker Compose manages the different services required by the project and allows them to communicate through an internal Docker network.

### Main Services

The architecture includes separate containers for:

- **Airflow API Server** — provides the Airflow API and web interface
- **Airflow Scheduler** — schedules and coordinates task execution
- **Airflow DAG Processor** — processes DAG definitions
- **Airflow Metadata Database** — stores Airflow metadata such as DAG runs and task states
- **PostgreSQL** — stores the retail business data

The Airflow metadata database and the retail PostgreSQL database have different responsibilities.

**Airflow DB → Airflow metadata**

**Retail PostgreSQL DB → clean_sales and rejected_sales**

### Docker Networking

Containers communicate with each other through the Docker Compose internal network.

For example, Airflow connects to PostgreSQL using the PostgreSQL service name and its internal port:

**postgres:5432**

From the host machine, PostgreSQL can instead be accessed through the port exposed by Docker Compose.

This avoids using `localhost` for communication between containers.

### Volumes

Docker volumes are used to make project files and data available inside the containers.

Examples include:

- `dags/` → Airflow DAG definitions
- `scripts/` → Python ETL modules
- `data/raw/` → source data
- `data/processed/` → generated intermediate data
- `logs/` → Airflow execution logs

The raw data directory is mounted as read-only where appropriate to protect the original source data.

### Custom Airflow Image

A custom Airflow Docker image is built using `Dockerfile.airflow`.

This makes it possible to install the Python dependencies required by the ETL pipeline, such as Pandas, PostgreSQL drivers, and Excel processing libraries.

As a result, the Airflow environment contains the same required dependencies every time the image is built.

## Database

PostgreSQL is used as the destination database for the processed retail data.

The pipeline loads data into two main tables:

- **clean_sales** — contains valid sales transactions that passed the transformation and data quality rules.
- **rejected_sales** — contains excluded records together with the reason why they were rejected.

The database schema is defined in `sql/schema.sql`.

The load process uses PostgreSQL `COPY` for efficient bulk loading instead of inserting records one by one.

Database operations are executed inside a transaction:

- `COMMIT` validates the changes when the load succeeds.
- `ROLLBACK` cancels uncommitted changes when an error occurs.

After loading, the `validate_load` Airflow task verifies that the expected number of records matches the number of records actually stored in PostgreSQL.

## Data Quality

Data quality checks are applied during the transformation stage to ensure that only valid sales are stored in the `clean_sales` table.

The pipeline checks that:

- `CustomerID` is not missing.
- `Description` is not missing.
- `Quantity` is greater than zero.
- `UnitPrice` is greater than zero.
- Duplicate transactions are excluded.
- Cancelled transactions are not considered valid sales.

Instead of deleting invalid records, the pipeline stores them in the `rejected_sales` table.

Each rejected record contains an `exclusion_reason` that explains why the record was excluded.

Possible exclusion reasons include:

- `not_a_sale`
- `missing_customer`
- `missing_description`
- `duplicate`

The transformation also performs assertions to verify that the resulting clean dataset respects the expected quality rules.

Finally, the `validate_load` task performs post-load validation to ensure that the number of records loaded into PostgreSQL matches the expected number of records.

## How to Run

### 1. Clone the Repository

Clone the repository from GitHub and enter the project directory.

    git clone https://github.com/Joubair-Ayoub/retail-sales-data-pipeline.git
    cd retail-sales-data-pipeline

### 2. Configure Environment Variables

Create a `.env` file at the root of the project and configure the required environment variables.

The configuration includes:

- PostgreSQL host
- PostgreSQL port
- Database name
- Database user
- Database password
- SMTP configuration

The `.env` file contains sensitive information and must not be committed to Git.

### 3. Add the Raw Dataset

Place the Online Retail Excel dataset inside:

    data/raw/

Raw Excel files are excluded from Git through `.gitignore`.

### 4. Build the Docker Environment

Build the Docker images:

    docker compose build

### 5. Start the Services

Start the complete Docker environment:

    docker compose up -d

Check that the containers are running:

    docker compose ps

### 6. Open Apache Airflow

Open the Airflow web interface and locate the `retail_sales_pipeline` DAG.

### 7. Run the Pipeline

Enable the DAG and trigger it manually, or let Airflow execute it according to the configured schedule.

The execution order is:

    extract → transform → load → validate_load

A successful DAG run means that all pipeline stages completed successfully.

### 8. Verify the Data

After a successful execution, verify the PostgreSQL tables:

- `clean_sales`
- `rejected_sales`

The `validate_load` task automatically performs an additional row-count validation after the loading stage.

## Future Improvements

The current pipeline provides a complete batch ETL workflow, but several improvements could make it closer to a production-grade Data Engineering system.

Possible future improvements include:

- Implement incremental loading instead of full table reloads.
- Add automated unit and integration tests.
- Add CI/CD using GitHub Actions.
- Add more advanced data quality checks.
- Improve monitoring and observability.
- Add pipeline execution metrics.
- Replace local intermediate files with object storage.
- Introduce database migrations.
- Add business intelligence dashboards.
- Deploy the pipeline to a cloud environment.
- Add data lineage and metadata management.#   r e t a i l _ s a l e s _ d a t a p i p e l i n e  
 