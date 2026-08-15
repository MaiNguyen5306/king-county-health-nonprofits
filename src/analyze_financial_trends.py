from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BALANCED_PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_balanced_panel_2021_2023.csv"
)

SOURCE_PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "king_county_form990_filing_panel_2019_2023.csv"
)

YEAR_SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_financial_summary_by_year.csv"
)

CATEGORY_SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_financial_summary_by_ntee.csv"
)

GROWTH_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_organization_growth_2021_2023.csv"
)

CONCENTRATION_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_revenue_concentration_by_year.csv"
)


def clean_ein(series):
    """Normalize EINs as nine-character strings."""
    return (
        series.astype("string")
        .str.replace(r"\D", "", regex=True)
        .str.zfill(9)
    )


def safe_growth(ending, beginning):
    """Calculate growth while treating zero beginnings as missing."""
    return ending / beginning.mask(beginning == 0) - 1


def main():
    data = pd.read_csv(
        BALANCED_PANEL_PATH,
        dtype={
            "EIN_XML": "string",
            "OBJECT_ID": "string",
        },
        low_memory=False,
    )

    source = pd.read_csv(
        SOURCE_PANEL_PATH,
        dtype=str,
        low_memory=False,
    )

    data["EIN_CLEAN"] = clean_ein(data["EIN_XML"])
    source["EIN_CLEAN"] = clean_ein(source["EIN"])

    classification = (
        source.sort_values(
            ["EIN_CLEAN", "FILING_YEAR", "OBJECT_ID"],
            kind="stable",
        )
        .drop_duplicates("EIN_CLEAN", keep="last")
        [
            [
                "EIN_CLEAN",
                "NTEE_CD",
                "NTEE_MAJOR",
            ]
        ]
    )

    data = data.merge(
        classification,
        on="EIN_CLEAN",
        how="left",
        validate="many_to_one",
    )

    if len(data) != 267:
        raise ValueError(
            f"Expected 267 balanced-panel rows; found {len(data)}."
        )

    if data["EIN_CLEAN"].nunique() != 89:
        raise ValueError(
            "Expected 89 balanced-panel organizations."
        )

    if data["NTEE_MAJOR"].isna().any():
        raise ValueError(
            "Some organizations are missing NTEE classifications."
        )

    if not data["NTEE_MAJOR"].isin(
        ["E", "F", "G", "H"]
    ).all():
        raise ValueError(
            "An organization falls outside NTEE groups E/F/G/H."
        )

    year_summary = (
        data.groupby("TAX_YEAR_ANALYSIS")
        .agg(
            ORGANIZATIONS=("EIN_CLEAN", "nunique"),
            TOTAL_REVENUE=("TOTAL_REVENUE", "sum"),
            MEDIAN_REVENUE=("TOTAL_REVENUE", "median"),
            TOTAL_EXPENSES=("TOTAL_EXPENSES", "sum"),
            MEDIAN_EXPENSES=("TOTAL_EXPENSES", "median"),
            TOTAL_ASSETS=("TOTAL_ASSETS_EOY", "sum"),
            MEDIAN_ASSETS=("TOTAL_ASSETS_EOY", "median"),
            MEDIAN_OPERATING_MARGIN=(
                "OPERATING_MARGIN",
                "median",
            ),
            NEGATIVE_MARGIN_ORGANIZATIONS=(
                "OPERATING_SURPLUS",
                lambda values: (values < 0).sum(),
            ),
        )
        .reset_index()
    )

    year_summary["NEGATIVE_MARGIN_RATE"] = (
        year_summary["NEGATIVE_MARGIN_ORGANIZATIONS"]
        / year_summary["ORGANIZATIONS"]
    )

    revenue = data.pivot(
        index="EIN_CLEAN",
        columns="TAX_YEAR_ANALYSIS",
        values="TOTAL_REVENUE",
    )

    expenses = data.pivot(
        index="EIN_CLEAN",
        columns="TAX_YEAR_ANALYSIS",
        values="TOTAL_EXPENSES",
    )

    assets = data.pivot(
        index="EIN_CLEAN",
        columns="TAX_YEAR_ANALYSIS",
        values="TOTAL_ASSETS_EOY",
    )

    margins = data.pivot(
        index="EIN_CLEAN",
        columns="TAX_YEAR_ANALYSIS",
        values="OPERATING_MARGIN",
    )

    latest_names = (
        data[data["TAX_YEAR_ANALYSIS"] == 2023]
        .set_index("EIN_CLEAN")["ORGANIZATION_NAME"]
    )

    ntee_code = classification.set_index(
        "EIN_CLEAN"
    )["NTEE_CD"]

    ntee_major = classification.set_index(
        "EIN_CLEAN"
    )["NTEE_MAJOR"]

    growth = pd.DataFrame(
        index=sorted(data["EIN_CLEAN"].unique())
    )

    growth.index.name = "EIN"

    growth["ORGANIZATION_NAME"] = latest_names
    growth["NTEE_CD"] = ntee_code
    growth["NTEE_MAJOR"] = ntee_major
    growth["REVENUE_2021"] = revenue[2021]
    growth["REVENUE_2023"] = revenue[2023]
    growth["REVENUE_GROWTH_2021_2023"] = safe_growth(
        revenue[2023],
        revenue[2021],
    )
    growth["EXPENSES_2021"] = expenses[2021]
    growth["EXPENSES_2023"] = expenses[2023]
    growth["EXPENSE_GROWTH_2021_2023"] = safe_growth(
        expenses[2023],
        expenses[2021],
    )
    growth["ASSETS_2021"] = assets[2021]
    growth["ASSETS_2023"] = assets[2023]
    growth["ASSET_GROWTH_2021_2023"] = safe_growth(
        assets[2023],
        assets[2021],
    )
    growth["OPERATING_MARGIN_2021"] = margins[2021]
    growth["OPERATING_MARGIN_2023"] = margins[2023]
    growth["OPERATING_MARGIN_CHANGE"] = (
        margins[2023] - margins[2021]
    )
    growth["NEGATIVE_MARGIN_2023"] = margins[2023] < 0

    growth = growth.reset_index()

    category_summary = (
        growth.groupby("NTEE_MAJOR")
        .agg(
            ORGANIZATIONS=("EIN", "size"),
            MEDIAN_REVENUE_GROWTH=(
                "REVENUE_GROWTH_2021_2023",
                "median",
            ),
            MEDIAN_EXPENSE_GROWTH=(
                "EXPENSE_GROWTH_2021_2023",
                "median",
            ),
            MEDIAN_MARGIN_2021=(
                "OPERATING_MARGIN_2021",
                "median",
            ),
            MEDIAN_MARGIN_2023=(
                "OPERATING_MARGIN_2023",
                "median",
            ),
            NEGATIVE_MARGIN_RATE_2023=(
                "NEGATIVE_MARGIN_2023",
                "mean",
            ),
        )
        .reset_index()
    )

    concentration_rows = []

    for tax_year, group in data.groupby(
        "TAX_YEAR_ANALYSIS"
    ):
        ordered = group.sort_values(
            "TOTAL_REVENUE",
            ascending=False,
        )

        total_revenue = ordered["TOTAL_REVENUE"].sum()

        concentration_rows.append(
            {
                "TAX_YEAR_ANALYSIS": tax_year,
                "TOTAL_REVENUE": total_revenue,
                "LARGEST_ORGANIZATION": (
                    ordered.iloc[0]["ORGANIZATION_NAME"]
                ),
                "LARGEST_ORGANIZATION_REVENUE": (
                    ordered.iloc[0]["TOTAL_REVENUE"]
                ),
                "TOP_1_REVENUE_SHARE": (
                    ordered.head(1)["TOTAL_REVENUE"].sum()
                    / total_revenue
                ),
                "TOP_10_REVENUE_SHARE": (
                    ordered.head(10)["TOTAL_REVENUE"].sum()
                    / total_revenue
                ),
            }
        )

    concentration = pd.DataFrame(concentration_rows)

    year_summary.to_csv(
        YEAR_SUMMARY_PATH,
        index=False,
    )

    category_summary.to_csv(
        CATEGORY_SUMMARY_PATH,
        index=False,
    )

    growth.to_csv(
        GROWTH_OUTPUT_PATH,
        index=False,
    )

    concentration.to_csv(
        CONCENTRATION_OUTPUT_PATH,
        index=False,
    )

    print("Financial-trend analysis summary")
    print("--------------------------------")
    print(f"Balanced organizations: {growth['EIN'].nunique():,}")
    print(f"Balanced filing rows: {len(data):,}")

    print("\nYear summary:")
    print(year_summary.to_string(index=False))

    print("\nNTEE category summary:")
    print(category_summary.to_string(index=False))

    print("\nRevenue concentration:")
    print(concentration.to_string(index=False))

    print("\nOutputs exported successfully.")


if __name__ == "__main__":
    main()