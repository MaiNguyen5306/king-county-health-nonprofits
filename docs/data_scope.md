# Data Scope and Coverage

## Study population

This project examines King County-headquartered 501(c)(3) health nonprofits that filed the full IRS Form 990. Form 990-EZ, Form 990-PF, and Form 990-T filings are excluded.

## Available source panel

The filing-selection pipeline retains available filings for tax years 2019–2023. When an organization has multiple submissions for the same EIN and tax period, the latest available submission is selected.

## Primary analysis window

The primary analysis uses tax years 2020–2023.

Tax year 2019 remains in the source panel but is treated as supplemental because IRS XML coverage is incomplete. Only 67 organizations were observed in 2019, compared with 162–183 annually from 2020 through 2023. Additionally, 91 organizations appeared in every year from 2020 through 2023 but were missing only in 2019.

This pattern is consistent with the transition to mandatory electronic filing rather than a sudden change in the nonprofit population.

## COVID-19 interpretation

Financial results from 2020 and 2021 may reflect pandemic-related effects. COVID-19 may influence revenue, expenses, contributions, and financial condition, but it does not adequately explain the missing 2019 electronic records.

## Analysis approach

- Main analysis: available observations from 2020–2023
- Robustness check: 151 organizations represented in all four primary years
- Supplemental context: available 2019 records, clearly labeled as incomplete
- Unusual short or changed accounting periods will remain separate until verified from the XML filings