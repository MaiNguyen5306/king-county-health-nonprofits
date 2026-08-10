# Financial Metrics Dictionary

## Purpose

This document defines the financial measures used to evaluate the capacity and resilience of King County community-health nonprofits.

Financial ratios will not be treated as measures of healthcare quality, patient outcomes, or organizational effectiveness.

## Core Metrics

### 1. Total Revenue

**Definition:** All revenue reported by the organization during the tax year.

**Use:** Measures organizational scale and supports comparisons over time.

### 2. Total Expenses

**Definition:** All expenses reported during the tax year.

**Use:** Measures annual spending and supports calculation of other financial ratios.

### 3. Operating Surplus or Deficit

**Formula:**

`Total Revenue - Total Expenses`

**Interpretation:**

- Positive value: annual surplus
- Negative value: annual deficit

A one-year deficit does not automatically mean an organization is financially distressed.

### 4. Operating Margin

**Formula:**

`(Total Revenue - Total Expenses) / Total Revenue`

**Use:** Shows the portion of revenue remaining after annual expenses.

The ratio will be recorded as missing when total revenue is zero or unavailable.

### 5. Program-Expense Share

**Formula:**

`Program-Service Expenses / Total Expenses`

**Use:** Shows the percentage of expenses allocated to programs and services.

This ratio does not independently measure program quality or organizational effectiveness.

### 6. Administrative-Expense Share

**Formula:**

`Management and General Expenses / Total Expenses`

**Use:** Describes the portion of spending allocated to administration and organizational operations.

A higher or lower value will not automatically be labeled good or bad.

### 7. Fundraising-Expense Share

**Formula:**

`Fundraising Expenses / Total Expenses`

**Use:** Describes the portion of expenses associated with fundraising activities.

### 8. Contributions and Grants Share

**Formula:**

`Contributions and Grants / Total Revenue`

**Use:** Estimates how dependent an organization is on charitable contributions and grants.

### 9. Program-Service Revenue Share

**Formula:**

`Program-Service Revenue / Total Revenue`

**Use:** Estimates how much revenue comes from providing services, including fees and reimbursements.

### 10. Liabilities-to-Assets Ratio

**Formula:**

`Total Liabilities at Year End / Total Assets at Year End`

**Use:** Measures the proportion of reported assets financed by liabilities.

The ratio will be recorded as missing when total assets are zero or unavailable.

### 11. Net-Assets Coverage

**Formula:**

`Ending Net Assets / Total Expenses`

**Use:** Provides an approximate measure of how large the organization’s accumulated net assets are relative to one year of expenses.

This does not represent unrestricted cash because Form 990 net assets may include restricted or noncash resources.

### 12. Annual Revenue Growth

**Formula:**

`(Current-Year Revenue - Prior-Year Revenue) / Prior-Year Revenue`

**Use:** Measures year-to-year revenue change for the same organization.

Growth will be recorded as missing when the prior-year revenue is zero, missing, or not comparable.

### 13. Revenue Volatility

**Definition:** Variation in an organization’s annual revenue across available tax years.

**Planned method:** Calculate the coefficient of variation only for organizations with at least three usable annual filings.

**Formula:**

`Standard Deviation of Revenue / Mean Revenue`

A higher value indicates less stable annual revenue, but it does not explain why revenue changed.

## Comparison Groups

Organizations will be compared using:

- Health-service subsector
- Revenue-size group
- Tax year
- Filing history

Revenue-size thresholds will be selected after examining the actual population rather than choosing arbitrary cutoffs in advance.

## Planned Resilience Indicators

The project will examine several indicators together:

- Repeated operating deficits
- Low or negative ending net assets
- High liabilities relative to assets
- Revenue decline
- High revenue volatility
- Dependence on a single broad revenue source

No single metric will be used to declare an organization financially resilient or financially distressed.

## Data-Quality Rules

- Ratios with zero denominators will be recorded as missing.
- Missing values will not automatically be replaced with zero.
- Original reported values will be preserved before calculated fields are created.
- Extreme values will be investigated rather than automatically deleted.
- Duplicate or amended filings will be identified before analysis.
- Comparisons will use tax periods, not file-download years.
- Organizations with incomplete filing histories will remain eligible for annual analysis but may be excluded from trend metrics.