import argparse
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_zip_archive_manifest_2020_2025.csv"
)

CHUNK_SIZE = 1024 * 1024
TIMEOUT = 120
MAX_ATTEMPTS = 3


def valid_zip(path):
    """Check the ZIP directory without decompressing every XML file."""
    if not path.exists() or path.stat().st_size == 0:
        return False

    try:
        with zipfile.ZipFile(path) as archive:
            return len(archive.infolist()) > 0
    except (zipfile.BadZipFile, OSError):
        return False


def download_archive(url, destination):
    """Download one archive with retry and partial-download support."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_suffix(destination.suffix + ".part")

    if valid_zip(partial_path):
        partial_path.replace(destination)
        print(
            f"RECOVERED completed archive: {destination.name} "
            f"({destination.stat().st_size / 1_048_576:,.1f} MB)"
        )
        return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        existing_bytes = (
            partial_path.stat().st_size
            if partial_path.exists()
            else 0
        )

        headers = {}

        if existing_bytes:
            headers["Range"] = f"bytes={existing_bytes}-"

        print(
            f"DOWNLOAD attempt {attempt}/{MAX_ATTEMPTS}: "
            f"{destination.name}"
        )

        try:
            with requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=TIMEOUT,
                allow_redirects=True,
            ) as response:
                response.raise_for_status()

                # Resume only when the server accepts the Range request.
                if existing_bytes and response.status_code == 206:
                    mode = "ab"
                else:
                    mode = "wb"
                    existing_bytes = 0

                total_bytes = response.headers.get("Content-Length")
                total_bytes = (
                    int(total_bytes) + existing_bytes
                    if total_bytes
                    else None
                )

                downloaded = existing_bytes

                with partial_path.open(mode) as output:
                    for chunk in response.iter_content(
                        chunk_size=CHUNK_SIZE
                    ):
                        if not chunk:
                            continue

                        output.write(chunk)
                        downloaded += len(chunk)

                        if total_bytes:
                            percent = downloaded / total_bytes * 100
                            print(
                                f"\r  {percent:6.2f}% "
                                f"({downloaded / 1_048_576:,.1f} MB)",
                                end="",
                                flush=True,
                            )

                print()

            if not valid_zip(partial_path):
                raise ValueError(
                    f"Downloaded file is not a valid ZIP: "
                    f"{partial_path}"
                )

            partial_path.replace(destination)

            print(
                f"COMPLETE: {destination.name} "
                f"({destination.stat().st_size / 1_048_576:,.1f} MB)"
            )
            return

        except (
            requests.RequestException,
            OSError,
            ValueError,
        ) as error:
            print(f"  Attempt failed: {error}")

            if attempt == MAX_ATTEMPTS:
                raise

            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser(
        description="Download required IRS Form 990 XML ZIP archives."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display planned downloads without downloading files.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N archive rows.",
    )

    args = parser.parse_args()

    manifest = pd.read_csv(
        MANIFEST_PATH,
        dtype=str,
        low_memory=False,
    )

    required_columns = {
        "FILING_YEAR",
        "ARCHIVE_FILENAME",
        "ARCHIVE_URL",
        "ARCHIVE_LOCAL_PATH",
    }

    missing_columns = required_columns - set(manifest.columns)

    if missing_columns:
        raise ValueError(
            f"Archive manifest is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be at least 1.")

        manifest = manifest.head(args.limit)

    print(f"Archive rows selected: {len(manifest):,}")

    if args.dry_run:
        print("\nDry run—no files will be downloaded:\n")

        for row in manifest.itertuples(index=False):
            print(
                f"{row.FILING_YEAR} | "
                f"{row.ARCHIVE_FILENAME} | "
                f"{row.ARCHIVE_URL}"
            )

        return

    completed = 0

    for row in manifest.itertuples(index=False):
        destination = PROJECT_ROOT / row.ARCHIVE_LOCAL_PATH

        download_archive(
            url=row.ARCHIVE_URL,
            destination=destination,
        )

        completed += 1

    print(f"\nArchives processed successfully: {completed:,}")


if __name__ == "__main__":
    main()