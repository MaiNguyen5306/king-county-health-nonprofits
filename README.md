# Financial Trends of King County Health Nonprofits

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://king-county-health-nonprofits.streamlit.app/)

An end-to-end data analytics project examining financial trends among health-related nonprofit organizations in King County, Washington. The project transforms IRS Form 990 XML filings into a reproducible analytical panel and an interactive Streamlit dashboard.

## Live Dashboard

Explore the public dashboard:

**[King County Health Nonprofits Dashboard](https://king-county-health-nonprofits.streamlit.app/)**

The dashboard supports health-category filtering, year-specific sector snapshots, a sensitivity analysis for the SCCAâ€“Fred Hutch structural change, category comparisons, organization-level exploration, and filtered-data downloads.

## Business Question

How did the financial position of King County health nonprofits change from tax year 2021 through 2023, and how did revenue growth, expense growth, operating pressure, and concentration differ across health subsectors?

## Executive Summary

The final balanced panel contains **89 organizations and 267 Form 990 filings**, with one comparable filing per organization in each tax year from 2021 through 2023.

Key findings include:

- Aggregate revenue increased **41.4%** from 2021 to 2023, but the increase fell to **5.4%** when the SCCAâ€“Fred Hutch structural change was excluded.
- The median organization recorded **15.8% revenue growth** and **22.2% expense growth**, indicating that expenses generally grew faster than revenue.
- Organizations reporting operating deficits increased from **24 (27%) in 2021** to **41 (46%) in 2023**.
- Revenue was highly concentrated in 2023: the largest organization represented **44.5%** of balanced-panel revenue, while the ten largest represented **89.3%**.
- Category-level results should be interpreted carefully because the balanced samples for disease-focused and medical-research organizations are small.

These findings describe reported financial conditions and should not be interpreted as measures of healthcare quality, community impact, or organizational effectiveness.

## Population and Scope

The analysis focuses on organizations that met the following criteria:

- IRS tax-exempt organizations classified under 501(c)(3)
- IRS mailing ZIP codes assigned primarily to King County using Census ZCTA geography
- Health-related NTEE major groups:
  - **E:** General and rehabilitative health
  - **F:** Mental health and crisis intervention
  - **G:** Diseases and medical disciplines
  - **H:** Medical research
- Full Form 990 filers
- One comparable filing in each tax year from 2021 through 2023

The complete filing-extraction workflow also processed records from filing years 2020 through 2025. The final trend analysis uses tax years 2021â€“2023 to create a consistent three-year balanced panel.

## Data Sources

- IRS Tax Exempt Organization Search filing indexes
- IRS Form 990 XML filing archives
- IRS exempt-organization classification fields
- U.S. Census ZIP Code Tabulation Area geography for the King County ZIP crosswalk

Only the compact processed datasets required by the public dashboard are stored in `dashboard/data/`. Raw IRS archives and extracted XML files remain excluded from version control because they are large and reproducible from the source pipeline.

## Data Pipeline

1. Identify preliminary health-related 501(c)(3) candidates in King County.
2. Match candidate EINs to IRS filing indexes.
3. Audit the IRS archive inventory and map filing object IDs to ZIP archives.
4. Download and validate 34 required IRS ZIP archives.
5. Extract the selected Form 990 XML filings.
6. Parse organization, tax-period, financial, and operational fields across multiple IRS XML schema versions.
7. Validate filing counts, duplicate organization-period records, field coverage, and unusual tax periods.
8. Resolve duplicate organization-year filings and flag short reporting periods.
9. Create a full analytical panel and a balanced 2021â€“2023 cohort.
10. Produce trend summaries, static figures, and the interactive Streamlit dashboard.

## Dashboard Features

### Sector Overview

- Year-specific organization, revenue, expense, and deficit metrics
- Aggregate revenue sensitivity with and without SCCAâ€“Fred Hutch
- Annual operating-deficit counts and rates
- Largest organizations by revenue

### Category Comparison

- Balanced-panel composition by NTEE major health group
- Median revenue and expense growth by health category
- Category sample sizes and percentage shares for interpretation

### Organization Explorer

- Organization-specific revenue and expense trends
- Annual operating surplus and margin
- Year-end assets and employee counts
- Filtered organization selection by health category

## Repository Structure

```text
king-county-health-nonprofits/
  .streamlit/          # Streamlit theme configuration
  dashboard/
    app.py             # Interactive Streamlit application
    data/              # Compact deployment datasets
  data/
    raw/               # Local raw source files (Git-ignored)
    processed/         # Local analytical outputs (Git-ignored)
  docs/                # Project documentation
  notebooks/           # Exploratory analysis
  reports/figures/     # Exported static visualizations
  sql/                 # SQL work
  src/                 # Download, extraction, parsing, and analysis scripts
  requirements.txt     # Python dependencies
  README.md
```

## Technology Stack

- **Python:** pandas, requests, ElementTree XML parsin
- **Visualization:** Plotly, Matplotlib, Seaborn
- **Application:** Streamlit
- **Version control and deployment:** Git, GitHub, Streamlit Community Cloud
- **Data formats:** XML and CSV

## Run Locally

Clone the repository:

```bash
git clone https://github.com/MaiNguyen5306/king-county-health-nonprofits.git
cd king-county-health-nonprofits
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Launch the dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

## Data Quality and Limitations

- The balanced-panel design improves year-to-year comparability but excludes organizations without a qualifying filing in every analysis year.
- IRS mailing ZIP codes identify the filing address and do not necessarily describe the full geographic service area.
- Seattle Cancer Care Alliance and Fred Hutchinson Cancer Research Center combined in April 2022; the dashboard includes a sensitivity view because this structural change affects aggregate comparisons.
- Seventy-seven filings listed in the 2022 IRS index were absent from the official XML archive used in the extraction process.
- Short tax periods were retained and flagged when appropriate; four short-period rows remained in the final analytical panel.
- NTEE groups G and H contain small balanced samples, so category estimates are descriptive rather than broadly generalizable.
- Form 990 values are self-reported administrative records and may contain amendments, reporting differences, or classification limitations.

## Analytical Boundary

This project evaluates reported organizational finances, including revenue, expenses, operating margins, assets, and financial concentration. It does **not** evaluate clinical quality, patient outcomes, program effectiveness, or community impact.