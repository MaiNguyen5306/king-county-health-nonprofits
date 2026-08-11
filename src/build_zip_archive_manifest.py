from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

FILING_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_xml_download_manifest_2020_2023.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_zip_archive_manifest_2020_2025.csv"
)

BASE_URL = "https://apps.irs.gov/pub/epostcard/990/xml"


def main():
    filings = pd.read_csv(
        FILING_MANIFEST_PATH,
        dtype=str,
        low_memory=False,
    )

    selected_ids = set(
        filings["OBJECT_ID"].astype(str).str.strip()
    )

    archive_rows = [
        ("2020", "download990xml_2020_1.zip"),
        ("2020", "2020_TEOS_XML_CT1.zip"),
        ("2021", "2021_TEOS_XML_01A.zip"),
        ("2022", "2022_TEOS_XML_01A.zip"),
    ]

    # The 2023 index does not identify each filing's archive,
    # so include all twelve official monthly archives.
    for month in range(1, 13):
        archive_rows.append(
            (
                "2023",
                f"2023_TEOS_XML_{month:02d}A.zip",
            )
        )

    # For 2024–2025, retain only batches containing selected filings.
    for filing_year in ["2024", "2025"]:
        index_path = RAW_DIR / f"index_{filing_year}.csv"

        index = pd.read_csv(
            index_path,
            usecols=["OBJECT_ID", "XML_BATCH_ID"],
            dtype=str,
            low_memory=False,
        )

        index["OBJECT_ID"] = (
            index["OBJECT_ID"].astype(str).str.strip()
        )

        selected = index[
            index["OBJECT_ID"].isin(selected_ids)
        ].copy()

        batch_ids = (
            selected["XML_BATCH_ID"]
            .dropna()
            .str.strip()
            .str.upper()
            .drop_duplicates()
            .sort_values()
        )

        for batch_id in batch_ids:
            archive_rows.append(
                (filing_year, f"{batch_id}.zip")
            )

    archives = pd.DataFrame(
        archive_rows,
        columns=["FILING_YEAR", "ARCHIVE_FILENAME"],
    ).drop_duplicates()

    archives["ARCHIVE_URL"] = (
        BASE_URL
        + "/"
        + archives["FILING_YEAR"]
        + "/"
        + archives["ARCHIVE_FILENAME"]
    )

    archives["ARCHIVE_LOCAL_PATH"] = (
        "data/raw/form990_archives/"
        + archives["FILING_YEAR"]
        + "/"
        + archives["ARCHIVE_FILENAME"]
    )

    archives = archives.sort_values(
        ["FILING_YEAR", "ARCHIVE_FILENAME"]
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archives.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("ZIP archive manifest summary")
    print("----------------------------")
    print(f"Unique ZIP archives required: {len(archives):,}")

    print("\nZIP archives by submission year:")
    print(
        archives["FILING_YEAR"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nDuplicate archive rows:", end=" ")
    print(
        archives.duplicated(
            ["FILING_YEAR", "ARCHIVE_FILENAME"]
        ).sum()
    )

    print(f"\nExported archive manifest: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()