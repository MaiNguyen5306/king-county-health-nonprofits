from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_filing_financials_2020_2025.csv"
)

FULL_PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_analysis_panel_2021_2023.csv"
)

BALANCED_PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_balanced_panel_2021_2023.csv"
)

EXCLUSIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_analysis_panel_exclusions.csv"
)


def safe_ratio(numerator, denominator):
    """Calculate a ratio while treating zero denominators as missing."""
    denominator = denominator.mask(denominator == 0)

    return numerator / denominator


def main():
    filings = pd.read_csv(
        INPUT_PATH,
        dtype={
            "EIN_XML": "string",
            "ZIP_CODE": "string",
            "OBJECT_ID": "string",
        },
        low_memory=False,
    )

    filings["TAX_PERIOD_BEGIN"] = pd.to_datetime(
        filings["TAX_PERIOD_BEGIN"],
        errors="coerce",
    )

    filings["TAX_PERIOD_END"] = pd.to_datetime(
        filings["TAX_PERIOD_END"],
        errors="coerce",
    )

    filings["RETURN_TIMESTAMP_SORT"] = pd.to_datetime(
        filings["RETURN_TIMESTAMP"],
        errors="coerce",
        utc=True,
    )

    filings["TAX_YEAR_ANALYSIS"] = (
        filings["TAX_PERIOD_END"].dt.year.astype("Int64")
    )

    filings["PERIOD_DAYS"] = (
        filings["TAX_PERIOD_END"]
        - filings["TAX_PERIOD_BEGIN"]
    ).dt.days + 1

    panel_candidates = filings[
        filings["TAX_YEAR_ANALYSIS"].between(
            2021,
            2023,
            inclusive="both",
        )
    ].copy()

    panel_candidates["SHORT_PERIOD_FLAG"] = (
        panel_candidates["PERIOD_DAYS"] < 330
    )

    panel_candidates["LONG_PERIOD_FLAG"] = (
        panel_candidates["PERIOD_DAYS"] > 370
    )

    panel_candidates["COMPARABLE_FULL_YEAR"] = (
        panel_candidates["PERIOD_DAYS"].between(
            330,
            370,
            inclusive="both",
        )
    )

    panel_candidates["NEGATIVE_LIABILITIES_FLAG"] = (
        panel_candidates["TOTAL_LIABILITIES_EOY"] < 0
    )

    panel_candidates["NEGATIVE_NET_ASSETS_FLAG"] = (
        panel_candidates["NET_ASSETS_EOY"] < 0
    )

    panel_candidates["ZERO_ASSETS_FLAG"] = (
        panel_candidates["TOTAL_ASSETS_EOY"] == 0
    )

    panel_candidates["PERIOD_LENGTH_DEVIATION"] = (
        panel_candidates["PERIOD_DAYS"] - 365
    ).abs()

    panel_candidates["OPERATING_MARGIN"] = safe_ratio(
        panel_candidates["OPERATING_SURPLUS"],
        panel_candidates["TOTAL_REVENUE"],
    )

    panel_candidates["CONTRIBUTION_REVENUE_SHARE"] = safe_ratio(
        panel_candidates["CONTRIBUTIONS_GRANTS"],
        panel_candidates["TOTAL_REVENUE"],
    )

    panel_candidates["PROGRAM_SERVICE_REVENUE_SHARE"] = safe_ratio(
        panel_candidates["PROGRAM_SERVICE_REVENUE"],
        panel_candidates["TOTAL_REVENUE"],
    )

    panel_candidates["LIABILITIES_TO_ASSETS"] = safe_ratio(
        panel_candidates["TOTAL_LIABILITIES_EOY"],
        panel_candidates["TOTAL_ASSETS_EOY"],
    )

    panel_candidates["DATA_QUALITY_FLAG_COUNT"] = (
        panel_candidates[
            [
                "SHORT_PERIOD_FLAG",
                "LONG_PERIOD_FLAG",
                "NEGATIVE_LIABILITIES_FLAG",
                "ZERO_ASSETS_FLAG",
            ]
        ]
        .fillna(False)
        .astype(int)
        .sum(axis=1)
    )

    # Prefer a normal full-year filing when an organization has
    # multiple filings ending in the same analysis year.
    panel_candidates = panel_candidates.sort_values(
        [
            "EIN_XML",
            "TAX_YEAR_ANALYSIS",
            "COMPARABLE_FULL_YEAR",
            "PERIOD_LENGTH_DEVIATION",
            "TAX_PERIOD_END",
            "RETURN_TIMESTAMP_SORT",
            "OBJECT_ID",
        ],
        ascending=[
            True,
            True,
            False,
            True,
            False,
            False,
            True,
        ],
        kind="stable",
    )

    duplicate_mask = panel_candidates.duplicated(
        subset=[
            "EIN_XML",
            "TAX_YEAR_ANALYSIS",
        ],
        keep="first",
    )

    exclusions = panel_candidates[
        duplicate_mask
    ].copy()

    exclusions["EXCLUSION_REASON"] = (
        "Additional filing for the same organization and analysis year; "
        "preferred the filing closest to a 365-day period."
    )

    panel = panel_candidates[
        ~duplicate_mask
    ].copy()

    panel = panel.drop(
        columns=["RETURN_TIMESTAMP_SORT"]
    )

    exclusions = exclusions.drop(
        columns=["RETURN_TIMESTAMP_SORT"]
    )

    if panel.duplicated(
        ["EIN_XML", "TAX_YEAR_ANALYSIS"]
    ).any():
        raise ValueError(
            "The analysis panel still contains duplicate "
            "organization-year rows."
        )

    organization_coverage = (
        panel.groupby("EIN_XML")
        .agg(
            YEAR_COUNT=(
                "TAX_YEAR_ANALYSIS",
                "nunique",
            ),
            ALL_PERIODS_COMPARABLE=(
                "COMPARABLE_FULL_YEAR",
                "all",
            ),
        )
    )

    balanced_eins = organization_coverage[
        (organization_coverage["YEAR_COUNT"] == 3)
        & organization_coverage["ALL_PERIODS_COMPARABLE"]
    ].index

    balanced = panel[
        panel["EIN_XML"].isin(balanced_eins)
    ].copy()

    balanced_counts = balanced.groupby(
        "EIN_XML"
    )["TAX_YEAR_ANALYSIS"].nunique()

    if not balanced_counts.eq(3).all():
        raise ValueError(
            "Balanced-panel organizations do not all have three years."
        )

    panel = panel.sort_values(
        [
            "EIN_XML",
            "TAX_YEAR_ANALYSIS",
        ],
        kind="stable",
    ).reset_index(drop=True)

    balanced = balanced.sort_values(
        [
            "EIN_XML",
            "TAX_YEAR_ANALYSIS",
        ],
        kind="stable",
    ).reset_index(drop=True)

    exclusions = exclusions.reset_index(drop=True)

    FULL_PANEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel.to_csv(
        FULL_PANEL_PATH,
        index=False,
    )

    balanced.to_csv(
        BALANCED_PANEL_PATH,
        index=False,
    )

    exclusions.to_csv(
        EXCLUSIONS_PATH,
        index=False,
    )

    print("Analysis-panel summary")
    print("----------------------")
    print(
        f"Candidate filings, 2021-2023: "
        f"{len(panel_candidates):,}"
    )
    print(
        f"Duplicate organization-year filings excluded: "
        f"{len(exclusions):,}"
    )
    print(f"Full panel rows: {len(panel):,}")
    print(
        f"Full panel organizations: "
        f"{panel['EIN_XML'].nunique():,}"
    )
    print(
        f"Short-period rows retained and flagged: "
        f"{panel['SHORT_PERIOD_FLAG'].sum():,}"
    )
    print(
        f"Balanced-panel organizations: "
        f"{balanced['EIN_XML'].nunique():,}"
    )
    print(f"Balanced-panel rows: {len(balanced):,}")

    print("\nFull-panel rows by tax year:")
    print(
        panel["TAX_YEAR_ANALYSIS"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(f"\nFull panel exported: {FULL_PANEL_PATH}")
    print(f"Balanced panel exported: {BALANCED_PANEL_PATH}")
    print(f"Exclusions exported: {EXCLUSIONS_PATH}")


if __name__ == "__main__":
    main()