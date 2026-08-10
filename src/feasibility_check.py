from pathlib import Path

import pandas as pd


# Locate files relative to the project folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

EO_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "eo_wa.csv"
ZCTA_COUNTY_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tab20_zcta520_county20_natl.txt"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "king_county_health_candidates_preliminary.csv"
)

HEALTH_NTEE_GROUPS = ["E", "F", "G", "H"]
KING_COUNTY_GEOID = "53033"


def check_required_columns(dataframe, required_columns, file_name):
    """Stop with a clear message if a required column is missing."""
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"{file_name} is missing these required columns: "
            f"{missing_text}"
        )


def main():
    # Load the IRS Washington nonprofit file.
    organizations = pd.read_csv(
        EO_DATA_PATH,
        dtype=str,
        low_memory=False,
    )

    # Load the pipe-delimited Census ZCTA-to-county file.
    zcta_county = pd.read_csv(
        ZCTA_COUNTY_PATH,
        sep="|",
        dtype=str,
        low_memory=False,
    )

    # Remove accidental spaces from column names.
    organizations.columns = organizations.columns.str.strip()
    zcta_county.columns = zcta_county.columns.str.strip()

    # Drop any completely empty column caused by a trailing pipe.
    zcta_county = zcta_county.dropna(
        axis="columns",
        how="all",
    )

    organization_columns = {
        "EIN",
        "NAME",
        "CITY",
        "STATE",
        "ZIP",
        "SUBSECTION",
        "NTEE_CD",
        "FILING_REQ_CD",
        "PF_FILING_REQ_CD",
    }

    census_columns = {
        "GEOID_ZCTA5_20",
        "GEOID_COUNTY_20",
        "AREALAND_PART",
        "AREAWATER_PART",
    }

    check_required_columns(
        organizations,
        organization_columns,
        "eo_wa.csv",
    )

    check_required_columns(
        zcta_county,
        census_columns,
        "Census ZCTA-to-county file",
    )

    # Convert ZIP+4 values to five-digit ZIP codes.
    organizations["ZIP5"] = organizations["ZIP"].str.extract(
        r"(\d{5})",
        expand=False,
    )

    # Extract the first letter of each NTEE classification.
    organizations["NTEE_MAJOR"] = (
        organizations["NTEE_CD"]
        .str.strip()
        .str.upper()
        .str[:1]
    )

    # Convert the Census overlap measurements to numeric values.
    zcta_county["AREALAND_PART_NUM"] = pd.to_numeric(
        zcta_county["AREALAND_PART"],
        errors="coerce",
    ).fillna(0)

    zcta_county["AREAWATER_PART_NUM"] = pd.to_numeric(
        zcta_county["AREAWATER_PART"],
        errors="coerce",
    ).fillna(0)

    # Assign each ZCTA to the county containing its largest land-area
    # overlap. Water area is used only to break a land-area tie.
    dominant_county_by_zcta = (
        zcta_county.sort_values(
            by=[
                "GEOID_ZCTA5_20",
                "AREALAND_PART_NUM",
                "AREAWATER_PART_NUM",
            ],
            ascending=[True, False, False],
        )
        .drop_duplicates(
            subset="GEOID_ZCTA5_20",
            keep="first",
        )
    )

    # Collect ZCTAs assigned primarily to King County.
    king_county_zips = set(
        dominant_county_by_zcta.loc[
            dominant_county_by_zcta["GEOID_COUNTY_20"]
            == KING_COUNTY_GEOID,
            "GEOID_ZCTA5_20",
        ].dropna()
    )

    # Count all Washington 501(c)(3) organizations.
    section_501c3 = organizations[
        organizations["SUBSECTION"] == "03"
    ].copy()

    # Count all broadly health-related 501(c)(3) organizations.
    statewide_health_501c3 = section_501c3[
        section_501c3["NTEE_MAJOR"].isin(
            HEALTH_NTEE_GROUPS
        )
    ].copy()

    # Create the preliminary candidate pool.
    #
    # Filing code 01 includes both Form 990 and Form 990-EZ.
    # Private foundations with PF filing code 1 are excluded.
    statewide_candidates = statewide_health_501c3[
        (statewide_health_501c3["FILING_REQ_CD"] == "01")
        & (
            statewide_health_501c3["PF_FILING_REQ_CD"]
            .fillna("")
            .str.strip()
            != "1"
        )
    ].copy()

    # Keep candidates in ZCTAs assigned primarily to King County.
    king_county_candidates = statewide_candidates[
        statewide_candidates["ZIP5"].isin(
            king_county_zips
        )
    ].copy()

    # Export selected candidate fields for manual review.
    output_columns = [
        "EIN",
        "NAME",
        "CITY",
        "STATE",
        "ZIP",
        "ZIP5",
        "NTEE_CD",
        "NTEE_MAJOR",
        "FILING_REQ_CD",
        "TAX_PERIOD",
        "ASSET_AMT",
        "INCOME_AMT",
        "REVENUE_AMT",
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    king_county_candidates = king_county_candidates.sort_values(
        by=["NTEE_MAJOR", "NAME"]
    )

    king_county_candidates[output_columns].to_csv(
        OUTPUT_PATH,
        index=False,
    )
    print(
        f"All Washington organizations: "
        f"{len(organizations):,}"
    )
    print(
        f"Washington 501(c)(3) organizations: "
        f"{len(section_501c3):,}"
    )
    print(
        f"Washington health 501(c)(3) organizations: "
        f"{len(statewide_health_501c3):,}"
    )
    print(
        f"Statewide preliminary health candidates: "
        f"{len(statewide_candidates):,}"
    )
    print(
        f"ZCTAs assigned primarily to King County: "
        f"{len(king_county_zips):,}"
    )
    print(
        f"Preliminary King County health candidates: "
        f"{len(king_county_candidates):,}"
    )

    print("\nKing County candidates by NTEE major group:")
    print(
        king_county_candidates["NTEE_MAJOR"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nKing County candidates by city:")
    print(
        king_county_candidates["CITY"]
        .fillna("MISSING CITY")
        .value_counts()
        .head(20)
        .to_string()
    )
    print(f"Exported candidate file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()