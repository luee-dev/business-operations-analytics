# Business Operations & Performance Analytics Platform

## Temporary Project Progress and Handover

**Last checkpoint:** 20 November 2026

**Project location:** `/home/lueedev/projects/business-operations-analytics`

## 1. Project Overview

An end-to-end Business Operations & Performance Analytics Platform developed as a professional Data Analyst portfolio project.

The project uses the Olist Brazilian E-Commerce Public Dataset, containing approximately 100,000 historical orders, primarily from 2016–2018.

### Technology Stack
- Python
- Pandas and NumPy
- PostgreSQL and SQL
- Power BI
- Apache Airflow
- Docker
- pytest
- Ruff
- ReportLab

**Important:** The dataset represents a historical Brazilian marketplace. Its findings should not be presented as current Kenyan business performance.

## 2. Project Completion Status

| Phase | Description | Status |
|---|---|---|
| 1 | Data acquisition and preparation | Complete |
| 2 | Database engineering and modelling | Complete |
| 3 | Data quality and validation | Complete |
| 4 | SQL business analytics | Complete |
| 5 | Python analytics | Complete |
| 6 | Automated testing and reliability | Complete |
| 7 | Power BI dashboards | Complete |
| 8 | Automated PDF reporting | Complete |
| 9 | Airflow orchestration | In progress |
| 10 | Docker, deployment and documentation | Not started |

## 3. Project Environment

Project root:

`/home/lueedev/projects/business-operations-analytics`

### Python environments
- `.venv/`: Main project environment, Python 3.14.4.
- `.airflow-venv/`: Separate Airflow environment, Python 3.14.4.
- Package management: `uv`.

### PostgreSQL
- Docker container: `boa-postgres`
- Host port: `5433`
- Database: `business_analytics`
- User: `boa_user`

Database credentials are stored in `.env`. Never expose or commit these credentials.

### Airflow
- Version: Apache Airflow 3.4.0
- `AIRFLOW_HOME="$PWD/airflow"`
- DAG directory: `airflow/dags`
- Metadata database: SQLite
- Executor: LocalExecutor

The Airflow metadata database is separate from the project's PostgreSQL analytics database.

## 4. Completed Work

### 4.1 Database Engineering and SQL

Completed PostgreSQL analytics schema, fact and dimension structures, and 11 analytical views:

- `vw_order_performance`
- `vw_customer_performance`
- `vw_customer_rfm`
- `vw_product_performance`
- `vw_category_performance`
- `vw_seller_performance`
- `vw_delivery_review_analysis`
- `vw_order_review_performance`
- `vw_category_review_analysis`
- `vw_payment_delivery_analysis`
- `vw_customer_segment_category_analysis`

### 4.2 Data Quality

Important findings and decisions:

- 1,359 approval-after-carrier timestamp anomalies.
- 23 carrier-after-customer-delivery anomalies.
- 8 delivered orders missing delivery timestamps.
- 1,390 orders with at least one timestamp anomaly.
- 261,831 exact geolocation duplicate rows removed.
- 610 products with incomplete metadata.
- 2 products with incomplete physical measurements.
- 789 repeated review IDs (814 excess rows), preserved because they were not confirmed safe duplicates.
- 9 zero-value payment rows and 2 invalid installment records preserved and flagged.
- 1 delivered order without payment; no synthetic payment created.
- 775 orders without items preserved.

### 4.3 Python Analytics and Testing

Reusable analytics modules include:

- `data_loader.py`
- `delivery.py`
- `customers.py`
- `products.py`
- `sellers.py`
- `customer_experience.py`

Statistical analysis is also implemented in:

`src/boa/analysis/payment_discrepancy_model.py`

Last reported complete test run: 116 passing tests.

Last reported validation commands:

```bash
ruff check src tests
ruff format --check src tests
pytest tests/unit -v
```

Rerun these after subsequent code changes.

### 4.4 Power BI

File:

`dashboards/business_operations_analytics.pbix`

Seven completed pages:

1. Executive Overview
2. Customer Analytics
3. Product & Category Performance
4. Seller Performance
5. Delivery & Customer Experience
6. Payments & Financial Performance
7. Cross-Functional Insights

Validated reconciliation figures:

- Delivered product value: R$13,221,498.11
- Delivered item lines: 110,197

### 4.5 Automated Reporting

Reporting modules:

- `src/boa/reporting/data.py`
- `src/boa/reporting/pdf.py`

Generated PDF:

`reports/automated/business_operations_performance_report.pdf`

The report was last confirmed as an eight-page A4 landscape document.

The reporting data layer contains 13 report sections, covering delivery, customer, product, category, seller and customer-experience analysis.

CLI commands:

```bash
python -m boa.main check-db
python -m boa.main generate-report
```

Both commands were successfully tested.

## 5. Important Business Insights

### Delivery
- Total orders: 99,441
- Delivered orders: 96,478
- Late delivered orders: 7,826
- Eligible delivery orders: 96,470
- Late delivery rate: approximately 8.11%
- Average delivery time: 12.56 days
- Median delivery time: 10.22 days
- 90th percentile: 23.10 days

### Customer Experience
- Late orders had an average review score of approximately 2.57.
- On-time orders had an average review score of approximately 4.29.
- Negative review rate was approximately 54% for late orders versus 9% for on-time orders.

These are associations, not proof of causation.

### Customers
- Distinct customers: 96,096
- Customers with delivered orders: 93,358
- Repeat customers: 2,801
- Repeat customer rate: approximately 3.00%

### Products and Categories
- Delivered product value: R$13,221,498.11
- Top five categories represented approximately 39.83% of delivered value.
- Top ten categories represented approximately 62.43%.

### Sellers
- Total sellers: 3,095
- Sellers with delivered sales: 2,970
- Top ten sellers represented approximately 13.27% of delivered value.

Seller risk screening is exploratory and does not establish seller fault.

## 6. Airflow Orchestration — Current Status

### DAG file

`airflow/dags/business_operations_reporting.py`

### DAG ID

`business_operations_reporting`

### Tasks

The DAG contains three tasks:

1. `check_database`
2. `generate_report`
3. `validate_report`

Execution order:

```text
check_database
      |
      v
generate_report
      |
      v
validate_report
```

The tasks invoke the main project's `.venv` Python interpreter.

### Confirmed achievements

- Airflow 3.4.0 installed.
- Airflow metadata database initialized.
- DAG imports successfully.
- DAG appears in `airflow dags list`.
- No DAG import errors were reported at the time.
- Scheduler health check previously returned `Found one alive job.`
- Executor configured as `LocalExecutor`.
- API server was listening on port 8080.
- DAG processor logs were generated.

### Outstanding problem

Two manually triggered DAG runs remained queued:

```text
manual__2026-11-20T11:10:39.133030+00:00
manual__2026-11-20T11:09:17.946131+00:00
```

Task inspection showed no task states or start/end times.

The scheduler process was observed earlier but a subsequent process check did not confirm that the same scheduler PID was still running.

The standalone Airflow terminal continuously printed DAG processor informational messages.

No successful task execution has yet been confirmed.

**Airflow orchestration is therefore not complete.**

### Next Airflow objective

Diagnose why tasks remain queued, restore scheduler/executor task execution, successfully run the DAG and confirm all three tasks succeed.

Do not delete Airflow metadata, reinstall Airflow, or change the executor without evidence.

Do not modify the analytics PostgreSQL database or expose `.env` credentials.

## 7. Next Project Phases

### Phase 9 — Airflow
- Diagnose scheduler and executor.
- Resolve queued DAG runs.
- Run the reporting workflow successfully.
- Validate PDF output.
- Document successful orchestration.

### Phase 10 — Deployment and Documentation
- Dockerise the application where appropriate.
- Finalise deployment configuration.
- Add comprehensive project documentation.
- Document architecture and data flow.
- Add reproducibility instructions.
- Perform final testing and validation.

## 8. Working Instructions for Future Sessions

- Continue from the current checkpoint.
- Do not repeat completed phases.
- Work one step at a time.
- Wait for command output before moving to the next step.
- Never assume a command succeeded.
- Do not request database passwords or `.env` values.
- Distinguish completed work from work still in progress.
- Do not claim Airflow is complete until the DAG and all three tasks succeed.
