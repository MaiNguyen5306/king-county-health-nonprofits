import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MAPPING_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_xml_archive_mapping_partial.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_filing_financials_2020_2025.csv"
)

ERROR_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_xml_parse_errors.csv"
)


NUMERIC_COLUMNS = [
    "TAX_YEAR",
    "FORMATION_YEAR",
    "TOTAL_EMPLOYEES",
    "TOTAL_VOLUNTEERS",
    "CONTRIBUTIONS_GRANTS",
    "PROGRAM_SERVICE_REVENUE",
    "INVESTMENT_INCOME",
    "OTHER_REVENUE",
    "TOTAL_REVENUE",
    "GRANTS_PAID",
    "SALARIES_COMPENSATION_BENEFITS",
    "TOTAL_EXPENSES",
    "TOTAL_ASSETS_BOY",
    "TOTAL_ASSETS_EOY",
    "TOTAL_LIABILITIES_BOY",
    "TOTAL_LIABILITIES_EOY",
    "NET_ASSETS_BOY",
    "NET_ASSETS_EOY",
]


def local_name(tag):
    """Remove an XML namespace from a tag or attribute name."""
    return tag.rsplit("}", 1)[-1]


def find_element(scope, tag_name):
    """Find the first descendant with a namespace-free tag name."""
    if scope is None:
        return None

    for element in scope.iter():
        if local_name(element.tag) == tag_name:
            return element

    return None


def first_text(scope, *tag_names):
    """Return the first nonempty value among possible XML tags."""
    for tag_name in tag_names:
        element = find_element(scope, tag_name)

        if element is None or element.text is None:
            continue

        value = element.text.strip()

        if value:
            return value

    return None


def return_version(root):
    """Read the IRS return schema version."""
    for key, value in root.attrib.items():
        if local_name(key).lower() == "returnversion":
            return value

    return None


def parse_xml(xml_path):
    """Parse one IRS Form 990 XML filing into one flat record."""
    root = ET.parse(xml_path).getroot()

    header = find_element(root, "ReturnHeader")
    return_data = find_element(root, "ReturnData")
    form990 = find_element(return_data, "IRS990")

    if header is None:
        raise ValueError("ReturnHeader was not found.")

    if return_data is None:
        raise ValueError("ReturnData was not found.")

    if form990 is None:
        raise ValueError("IRS990 was not found.")

    return {
        "RETURN_VERSION": return_version(root),
        "RETURN_TIMESTAMP": first_text(
            header,
            "ReturnTs",
        ),
        "TAX_PERIOD_BEGIN": first_text(
            header,
            "TaxPeriodBeginDt",
        ),
        "TAX_PERIOD_END": first_text(
            header,
            "TaxPeriodEndDt",
        ),
        "TAX_YEAR": first_text(
            header,
            "TaxYr",
        ),
        "EIN_XML": first_text(
            header,
            "EIN",
        ),
        "ORGANIZATION_NAME": first_text(
            header,
            "BusinessNameLine1Txt",
        ),
        "ADDRESS_LINE_1": first_text(
            header,
            "AddressLine1Txt",
        ),
        "ADDRESS_LINE_2": first_text(
            header,
            "AddressLine2Txt",
        ),
        "CITY": first_text(
            header,
            "CityNm",
        ),
        "STATE": first_text(
            header,
            "StateAbbreviationCd",
        ),
        "ZIP_CODE": first_text(
            header,
            "ZIPCd",
        ),
        "MISSION": first_text(
            form990,
            "ActivityOrMissionDesc",
        ),
        "FORMATION_YEAR": first_text(
            form990,
            "FormationYr",
        ),
        "WEBSITE": first_text(
            form990,
            "WebsiteAddressTxt",
        ),
        "TOTAL_EMPLOYEES": first_text(
            form990,
            "TotalEmployeeCnt",
        ),
        "TOTAL_VOLUNTEERS": first_text(
            form990,
            "TotalVolunteersCnt",
        ),
        "CONTRIBUTIONS_GRANTS": first_text(
            form990,
            "CYContributionsGrantsAmt",
        ),
        "PROGRAM_SERVICE_REVENUE": first_text(
            form990,
            "CYProgramServiceRevenueAmt",
        ),
        "INVESTMENT_INCOME": first_text(
            form990,
            "CYInvestmentIncomeAmt",
        ),
        "OTHER_REVENUE": first_text(
            form990,
            "CYOtherRevenueAmt",
        ),
        "TOTAL_REVENUE": first_text(
            form990,
            "CYTotalRevenueAmt",
        ),
        "GRANTS_PAID": first_text(
            form990,
            "CYGrantsAndSimilarPaidAmt",
        ),
        "SALARIES_COMPENSATION_BENEFITS": first_text(
            form990,
            "CYSalariesCompEmpBnftPaidAmt",
        ),
        "TOTAL_EXPENSES": first_text(
            form990,
            "CYTotalExpensesAmt",
            "CYTotalFunctionalExpensesAmt",
        ),
        "TOTAL_ASSETS_BOY": first_text(
            form990,
            "TotalAssetsBOYAmt",
        ),
        "TOTAL_ASSETS_EOY": first_text(
            form990,
            "TotalAssetsEOYAmt",
        ),
        "TOTAL_LIABILITIES_BOY": first_text(
            form990,
            "TotalLiabilitiesBOYAmt",
        ),
        "TOTAL_LIABILITIES_EOY": first_text(
            form990,
            "TotalLiabilitiesEOYAmt",
        ),
        "NET_ASSETS_BOY": first_text(
            form990,
            "NetAssetsOrFundBalancesBOYAmt",
        ),
        "NET_ASSETS_EOY": first_text(
            form990,
            "NetAssetsOrFundBalancesEOYAmt",
        ),
    }


def main():
    mapping = pd.read_csv(
        MAPPING_PATH,
        dtype=str,
        low_memory=False,
    )

    required_columns = {
        "FILING_YEAR",
        "OBJECT_ID",
        "XML_FILENAME",
        "ARCHIVE_FILENAME",
        "XML_LOCAL_PATH",
    }

    missing_columns = required_columns - set(mapping.columns)

    if missing_columns:
        raise ValueError(
            f"XML mapping is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if mapping["OBJECT_ID"].duplicated().any():
        raise ValueError(
            "XML mapping contains duplicate OBJECT_ID values."
        )

    records = []
    errors = []

    for number, row in enumerate(
        mapping.itertuples(index=False),
        start=1,
    ):
        xml_path = PROJECT_ROOT / row.XML_LOCAL_PATH

        try:
            parsed = parse_xml(xml_path)

            parsed.update(
                {
                    "FILING_YEAR": row.FILING_YEAR,
                    "OBJECT_ID": row.OBJECT_ID,
                    "XML_FILENAME": row.XML_FILENAME,
                    "ARCHIVE_FILENAME": row.ARCHIVE_FILENAME,
                    "XML_LOCAL_PATH": row.XML_LOCAL_PATH,
                }
            )

            records.append(parsed)

        except Exception as error:
            errors.append(
                {
                    "FILING_YEAR": row.FILING_YEAR,
                    "OBJECT_ID": row.OBJECT_ID,
                    "XML_LOCAL_PATH": row.XML_LOCAL_PATH,
                    "ERROR": str(error),
                }
            )

        if number % 100 == 0 or number == len(mapping):
            print(
                f"Processed {number:,}/{len(mapping):,} XML files"
            )

    filings = pd.DataFrame(records)

    for column in NUMERIC_COLUMNS:
        filings[column] = pd.to_numeric(
            filings[column],
            errors="coerce",
        ).astype("Int64")

    filings["OPERATING_SURPLUS"] = (
        filings["TOTAL_REVENUE"]
        - filings["TOTAL_EXPENSES"]
    )

    filings["ASSET_CHANGE"] = (
        filings["TOTAL_ASSETS_EOY"]
        - filings["TOTAL_ASSETS_BOY"]
    )

    filings["NET_ASSET_CHANGE"] = (
        filings["NET_ASSETS_EOY"]
        - filings["NET_ASSETS_BOY"]
    )

    filings = filings.sort_values(
        ["FILING_YEAR", "EIN_XML", "OBJECT_ID"],
        kind="stable",
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    filings.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    parse_errors = pd.DataFrame(
        errors,
        columns=[
            "FILING_YEAR",
            "OBJECT_ID",
            "XML_LOCAL_PATH",
            "ERROR",
        ],
    )

    parse_errors.to_csv(
        ERROR_OUTPUT_PATH,
        index=False,
    )

    print("\nForm 990 parsing summary")
    print("------------------------")
    print(f"Mapped XML files: {len(mapping):,}")
    print(f"Successfully parsed: {len(filings):,}")
    print(f"Parse errors: {len(parse_errors):,}")
    print(
        f"Unique object IDs: "
        f"{filings['OBJECT_ID'].nunique():,}"
    )
    print("\nRows by filing year:")
    print(
        filings["FILING_YEAR"]
        .value_counts()
        .sort_index()
        .to_string()
    )
    print(f"\nFinancial dataset exported: {OUTPUT_PATH}")
    print(f"Parse-error report exported: {ERROR_OUTPUT_PATH}")


if __name__ == "__main__":
    main()