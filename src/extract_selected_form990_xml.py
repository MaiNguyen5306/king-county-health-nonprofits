import argparse
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FILING_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_xml_download_manifest_2020_2023.csv"
)

ARCHIVE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "form990_archives"
)

XML_ROOT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "form990_xml"
)

MAPPING_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_xml_archive_mapping_partial.csv"
)

SEVEN_ZIP = Path(r"C:\Program Files\7-Zip\7z.exe")


def run_7zip(arguments):
    """Run 7-Zip and return its text output."""
    command = [str(SEVEN_ZIP), *arguments]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"7-Zip failed with exit code {result.returncode}.\n"
            f"{result.stdout}\n{result.stderr}"
        )

    return result.stdout


def list_xml_members(archive_path):
    """Return XML member paths contained in one ZIP archive."""
    output = run_7zip(
        [
            "l",
            "-slt",
            "-sccUTF-8",
            str(archive_path),
        ]
    )

    members = []

    for line in output.splitlines():
        if not line.startswith("Path = "):
            continue

        member_path = line.removeprefix("Path = ").strip()

        if member_path.lower().endswith("_public.xml"):
            members.append(member_path)

    return members


def extract_members(archive_path, member_paths, output_directory):
    """Extract only selected members from one archive."""
    if not member_paths:
        return

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory() as temp_directory:
        list_path = Path(temp_directory) / "selected_xml.txt"

        list_path.write_text(
            "\n".join(member_paths),
            encoding="utf-8",
        )

        run_7zip(
            [
                "e",
                str(archive_path),
                f"@{list_path}",
                "-scsUTF-8",
                f"-o{output_directory}",
                "-aos",
                "-y",
                "-bd",
            ]
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Find and selectively extract required Form 990 XML files "
            "from downloaded IRS ZIP archives."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N downloaded archives.",
    )

    args = parser.parse_args()

    if not SEVEN_ZIP.exists():
        raise FileNotFoundError(
            f"7-Zip was not found at: {SEVEN_ZIP}"
        )

    filings = pd.read_csv(
        FILING_MANIFEST_PATH,
        dtype=str,
        low_memory=False,
    )

    required_columns = {
        "OBJECT_ID",
        "FILING_YEAR",
    }

    missing_columns = required_columns - set(filings.columns)

    if missing_columns:
        raise ValueError(
            f"Filing manifest is missing columns: "
            f"{sorted(missing_columns)}"
        )

    filings["OBJECT_ID"] = (
        filings["OBJECT_ID"]
        .astype("string")
        .str.strip()
    )

    filings["FILING_YEAR"] = (
        filings["FILING_YEAR"]
        .astype("string")
        .str.strip()
    )

    filings["XML_FILENAME"] = (
        filings["OBJECT_ID"] + "_public.xml"
    )

    archives = sorted(
        ARCHIVE_ROOT.glob("*/*.zip")
    )

    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be at least 1.")

        archives = archives[:args.limit]

    print(f"Downloaded ZIP archives found: {len(archives):,}")

    mapping_rows = []
    extracted_filenames = set()

    for archive_number, archive_path in enumerate(
        archives,
        start=1,
    ):
        filing_year = archive_path.parent.name

        wanted = filings[
            filings["FILING_YEAR"] == filing_year
        ].copy()

        wanted_filenames = set(
            wanted["XML_FILENAME"]
        )

        print(
            f"\n[{archive_number}/{len(archives)}] "
            f"Scanning {archive_path.name}"
        )

        members = list_xml_members(archive_path)

        selected_members = [
            member_path
            for member_path in members
            if Path(member_path).name in wanted_filenames
        ]

        print(
            f"  Required XML files found: "
            f"{len(selected_members):,}"
        )

        output_directory = XML_ROOT / filing_year

        extract_members(
            archive_path=archive_path,
            member_paths=selected_members,
            output_directory=output_directory,
        )

        for member_path in selected_members:
            xml_filename = Path(member_path).name

            if xml_filename in extracted_filenames:
                raise ValueError(
                    f"Required XML appeared in multiple archives: "
                    f"{xml_filename}"
                )

            extracted_filenames.add(xml_filename)

            mapping_rows.append(
                {
                    "FILING_YEAR": filing_year,
                    "OBJECT_ID": xml_filename.removesuffix(
                        "_public.xml"
                    ),
                    "XML_FILENAME": xml_filename,
                    "ARCHIVE_FILENAME": archive_path.name,
                    "ARCHIVE_LOCAL_PATH": str(
                        archive_path.relative_to(PROJECT_ROOT)
                    ).replace("\\", "/"),
                    "XML_LOCAL_PATH": str(
                        (
                            output_directory
                            / xml_filename
                        ).relative_to(PROJECT_ROOT)
                    ).replace("\\", "/"),
                }
            )

    mapping = pd.DataFrame(
        mapping_rows,
        columns=[
            "FILING_YEAR",
            "OBJECT_ID",
            "XML_FILENAME",
            "ARCHIVE_FILENAME",
            "ARCHIVE_LOCAL_PATH",
            "XML_LOCAL_PATH",
        ],
    )

    MAPPING_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    mapping.to_csv(
        MAPPING_OUTPUT_PATH,
        index=False,
    )

    missing_files = []

    for row in mapping.itertuples(index=False):
        xml_path = PROJECT_ROOT / row.XML_LOCAL_PATH

        if not xml_path.exists() or xml_path.stat().st_size == 0:
            missing_files.append(row.XML_FILENAME)

    print("\nSelective extraction summary")
    print("----------------------------")
    print(f"Downloaded archives processed: {len(archives):,}")
    print(f"Required XML files located: {len(mapping):,}")
    print(
        f"Missing or empty extracted XML files: "
        f"{len(missing_files):,}"
    )
    print(f"Partial mapping exported: {MAPPING_OUTPUT_PATH}")


if __name__ == "__main__":
    main()