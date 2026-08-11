from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "king_county_health_candidates_preliminary.csv"
)
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "king_county_form990_filing_panel_2019_2023.csv"
)

FILING_YEARS = range(2019, 2026)
TAX_YEARS = {"2019", "2020", "2021", "2022", "2023"}

INDEX_COLUMNS = [
    "EIN",
    "TAX_PERIOD",
    "SUB_DATE",
    "RETURN_TYPE",
    "OBJECT_ID",
]


def normalize_ein(series):
    """Convert EIN values to nine-digit strings."""
    return (
        series.astype("string")
        .str.replace(r"\D", "", regex=True)
        .str.zfill(9)
    )


def load_filing_indexes():
    """Load and combine the seven IRS filing-year indexes."""
    index_frames = []

    for filing_year in FILING_YEARS:
        index_path = (
            RAW_DATA_DIR
            / f"index_{filing_year}.csv"
        )

        if not index_path.exists():
            raise FileNotFoundError(
                f"Missing IRS index file: {index_path}"
            )

        filing_index = pd.read_csv(
            index_path,
            usecols=INDEX_COLUMNS,
            dtype=str,
            low_memory=False,
        )

        filing_index["FILING_YEAR"] = filing_year
        index_frames.append(filing_index)

        print(
            f"Loaded index_{filing_year}.csv: "
            f"{len(filing_index):,} rows"
        )

    return pd.concat(
        index_frames,
        ignore_index=True,
    )


def main():
    # Load the preliminary King County candidate population.
    candidates = pd.read_csv(
        CANDIDATE_PATH,
        dtype=str,
        low_memory=False,
    )

    candidates.columns = candidates.columns.str.strip()
    candidates["EIN"] = normalize_ein(candidates["EIN"])

    # Keep one candidate record per EIN.
    candidates = candidates.drop_duplicates(
        subset="EIN",
        keep="first",
    )

    candidate_eins = set(candidates["EIN"].dropna())

    # Load all IRS filing indexes from 2019 through 2025.
    filings = load_filing_indexes()

    filings.columns = filings.columns.str.strip()
    filings["EIN"] = normalize_ein(filings["EIN"])

    # Standardize fields used for filtering and sorting.
    filings["RETURN_TYPE"] = (
        filings["RETURN_TYPE"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    filings["TAX_PERIOD"] = (
        filings["TAX_PERIOD"]
        .astype("string")
        .str.strip()
    )

    filings["TAX_YEAR"] = filings["TAX_PERIOD"].str[:4]

    filings["SUB_DATE_PARSED"] = pd.to_datetime(
        filings["SUB_DATE"],
        errors="coerce",
    )

    filings["OBJECT_ID_NUM"] = pd.to_numeric(
        filings["OBJECT_ID"],
        errors="coerce",
    )

    # Match the IRS indexes to the 261 preliminary candidates.
    matched = filings[
        filings["EIN"].isin(candidate_eins)
    ].copy()

    # Retain only full Form 990 filings for tax years 2019–2023.
    eligible_filings = matched[
        (matched["RETURN_TYPE"] == "990")
        & (matched["TAX_YEAR"].isin(TAX_YEARS))
    ].copy()

    records_before_deduplication = len(eligible_filings)

    # Retain the latest available submission for each EIN and
    # exact tax period. Filing year and object ID break date ties.
    selected_filings = (
        eligible_filings.sort_values(
            by=[
                "EIN",
                "TAX_PERIOD",
                "SUB_DATE_PARSED",
                "FILING_YEAR",
                "OBJECT_ID_NUM",
            ],
            ascending=True,
            na_position="first",
        )
        .drop_duplicates(
            subset=["EIN", "TAX_PERIOD"],
            keep="last",
        )
        .copy()
    )

    # Diagnose organizations with multiple tax periods ending
    # within the same tax year.
    duplicate_tax_year_groups = (
        selected_filings
        .groupby(["EIN", "TAX_YEAR"])
        .size()
    )

    duplicate_tax_year_groups = (
        duplicate_tax_year_groups[
            duplicate_tax_year_groups > 1
        ]
    )

    # Add organization information to the selected filings.
    candidate_columns = [
        "EIN",
        "NAME",
        "CITY",
        "STATE",
        "ZIP",
        "NTEE_CD",
        "NTEE_MAJOR",
    ]

    filing_columns = [
        "EIN",
        "TAX_YEAR",
        "TAX_PERIOD",
        "SUB_DATE",
        "RETURN_TYPE",
        "OBJECT_ID",
        "FILING_YEAR",
    ]

    panel = selected_filings[filing_columns].merge(
        candidates[candidate_columns],
        on="EIN",
        how="left",
        validate="many_to_one",
    )

    panel = panel[
        [
            "EIN",
            "NAME",
            "CITY",
            "STATE",
            "ZIP",
            "NTEE_CD",
            "NTEE_MAJOR",
            "TAX_YEAR",
            "TAX_PERIOD",
            "SUB_DATE",
            "RETURN_TYPE",
            "OBJECT_ID",
            "FILING_YEAR",
        ]
    ].sort_values(
        by=["EIN", "TAX_PERIOD"]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nFive-year Form 990 panel summary")
    print("--------------------------------")
    print(
        f"Candidate organizations: "
        f"{len(candidates):,}"
    )
    print(
        f"Combined IRS index rows: "
        f"{len(filings):,}"
    )
    print(
        f"Eligible records before deduplication: "
        f"{records_before_deduplication:,}"
    )
    print(
        f"Selected EIN-tax-period records: "
        f"{len(panel):,}"
    )
    print(
        f"Organizations with at least one filing: "
        f"{panel['EIN'].nunique():,}"
    )

    print("\nSelected filings by tax year:")
    print(
        panel["TAX_YEAR"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(
        "\nOrganizations with multiple tax periods "
        "in the same tax year:"
    )

    if duplicate_tax_year_groups.empty:
        print("None")
    else:
        print(duplicate_tax_year_groups.to_string())

    filing_year_counts = (
        panel.groupby("EIN")["TAX_YEAR"]
        .nunique()
        .value_counts()
        .sort_index()
    )

    print("\nOrganizations by number of tax years available:")
    print(filing_year_counts.to_string())

    complete_panel_count = (
        panel.groupby("EIN")["TAX_YEAR"]
        .nunique()
        .eq(5)
        .sum()
    )

    print(
        f"\nOrganizations represented in all five tax years: "
        f"{complete_panel_count:,}"
    )
    print(f"Exported filing panel: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()