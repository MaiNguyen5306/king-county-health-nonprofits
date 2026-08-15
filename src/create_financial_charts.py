from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BALANCED_PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "form990_balanced_panel_2021_2023.csv"
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

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "reports"
    / "figures"
)

STRUCTURAL_CHANGE_EIN = "911935159"

NAVY = "#24557A"
TEAL = "#2A9D8F"
ORANGE = "#E76F51"
GOLD = "#E9C46A"
GRAY = "#6B7280"


def billions(value, position=None):
    """Format a number as billions of dollars."""
    return f"${value / 1_000_000_000:.1f}B"


def millions(value, position=None):
    """Format a number as millions of dollars."""
    return f"${value:,.0f}M"


def save_figure(figure, filename):
    """Save a consistently formatted project chart."""
    output_path = OUTPUT_DIRECTORY / filename

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)

    print(f"Exported: {output_path}")


def revenue_sensitivity_chart(data):
    """Chart revenue with and without the structural-change EIN."""
    full = (
        data.groupby("TAX_YEAR_ANALYSIS")["TOTAL_REVENUE"]
        .sum()
        .sort_index()
    )

    excluding = (
        data[
            data["EIN_XML"] != STRUCTURAL_CHANGE_EIN
        ]
        .groupby("TAX_YEAR_ANALYSIS")["TOTAL_REVENUE"]
        .sum()
        .sort_index()
    )

    figure, axis = plt.subplots(
        figsize=(9, 5.5)
    )

    axis.plot(
        full.index,
        full.values,
        marker="o",
        linewidth=2.8,
        markersize=8,
        color=NAVY,
        label="Full balanced cohort",
    )

    axis.plot(
        excluding.index,
        excluding.values,
        marker="o",
        linewidth=2.8,
        markersize=8,
        color=TEAL,
        label="Excluding SCCA–Fred Hutch",
    )

    axis.axvline(
        2022,
        color=GRAY,
        linestyle="--",
        linewidth=1.3,
        alpha=0.8,
    )

    axis.text(
        2022.03,
        full.max() * 0.05,
        "Merger effective April 2022",
        color=GRAY,
        fontsize=9,
        va="bottom",
    )

    axis.set_title(
        "Revenue growth is dominated by one structural change",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )

    axis.set_xlabel("Tax year")
    axis.set_ylabel("Total revenue")
    axis.set_xticks(full.index)
    axis.set_ylim(
        0,
        full.max() * 1.12,
    )
    axis.yaxis.set_major_formatter(
        FuncFormatter(billions)
    )
    axis.legend(frameon=False, loc="upper left")

    sns.despine(ax=axis)

    save_figure(
        figure,
        "01_revenue_sensitivity.png",
    )


def operating_pressure_chart(year_summary):
    """Chart organizations reporting operating deficits."""
    years = year_summary[
        "TAX_YEAR_ANALYSIS"
    ].astype(int)

    counts = year_summary[
        "NEGATIVE_MARGIN_ORGANIZATIONS"
    ]

    rates = year_summary[
        "NEGATIVE_MARGIN_RATE"
    ]

    figure, axis = plt.subplots(
        figsize=(8, 5.5)
    )

    bars = axis.bar(
        years.astype(str),
        counts,
        color=ORANGE,
        width=0.58,
    )

    for bar, count, rate in zip(
        bars,
        counts,
        rates,
    ):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{int(count)} ({rate:.0%})",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    axis.set_title(
        "More organizations are operating at a deficit",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )

    axis.set_xlabel("Tax year")
    axis.set_ylabel("Organizations with expenses above revenue")
    axis.set_ylim(0, max(counts) * 1.22)

    sns.despine(ax=axis)

    save_figure(
        figure,
        "02_operating_pressure.png",
    )


def category_growth_chart(category_summary):
    """Compare median revenue and expense growth by NTEE group."""
    category_summary = (
        category_summary
        .sort_values("NTEE_MAJOR")
        .copy()
    )

    labels = [
        f"{row.NTEE_MAJOR}\n(n={int(row.ORGANIZATIONS)})"
        for row in category_summary.itertuples(
            index=False
        )
    ]

    positions = np.arange(
        len(category_summary)
    )

    width = 0.36

    revenue_growth = (
        category_summary["MEDIAN_REVENUE_GROWTH"]
        * 100
    )

    expense_growth = (
        category_summary["MEDIAN_EXPENSE_GROWTH"]
        * 100
    )

    figure, axis = plt.subplots(
        figsize=(9, 5.8)
    )

    revenue_bars = axis.bar(
        positions - width / 2,
        revenue_growth,
        width,
        color=TEAL,
        label="Median revenue growth",
    )

    expense_bars = axis.bar(
        positions + width / 2,
        expense_growth,
        width,
        color=ORANGE,
        label="Median expense growth",
    )

    axis.bar_label(
        revenue_bars,
        labels=[
            f"{value:.1f}%"
            for value in revenue_growth
        ],
        padding=3,
        fontsize=9,
    )

    axis.bar_label(
        expense_bars,
        labels=[
            f"{value:.1f}%"
            for value in expense_growth
        ],
        padding=3,
        fontsize=9,
    )

    axis.set_title(
        "Expenses generally grew faster than revenue",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )

    axis.set_xlabel("NTEE major health group")
    axis.set_ylabel("Median growth, 2021–2023")
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.legend(frameon=False, loc="upper right")
    axis.set_ylim(
        0,
        max(expense_growth.max(), revenue_growth.max())
        * 1.3,
    )

    sns.despine(ax=axis)

    save_figure(
        figure,
        "03_growth_by_ntee_group.png",
    )


def revenue_concentration_chart(data):
    """Chart the ten largest organizations by 2023 revenue."""
    latest = (
        data[
            data["TAX_YEAR_ANALYSIS"] == 2023
        ]
        .nlargest(10, "TOTAL_REVENUE")
        .sort_values("TOTAL_REVENUE")
        .copy()
    )

    latest["REVENUE_MILLIONS"] = (
        latest["TOTAL_REVENUE"]
        / 1_000_000
    )

    total_revenue = data[
        data["TAX_YEAR_ANALYSIS"] == 2023
    ]["TOTAL_REVENUE"].sum()

    top_ten_share = (
        latest["TOTAL_REVENUE"].sum()
        / total_revenue
    )

    figure, axis = plt.subplots(
        figsize=(10, 6.8)
    )

    bars = axis.barh(
        latest["ORGANIZATION_NAME"],
        latest["REVENUE_MILLIONS"],
        color=NAVY,
    )

    axis.bar_label(
        bars,
        labels=[
            f"${value:,.0f}M"
            for value in latest["REVENUE_MILLIONS"]
        ],
        padding=4,
        fontsize=9,
    )

    axis.set_title(
        "Revenue is concentrated among the largest organizations",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=22,
    )

    axis.text(
        0,
        1.01,
        (
            f"Top ten organizations generated "
            f"{top_ten_share:.1%} of balanced-cohort "
            f"revenue in 2023."
        ),
        transform=axis.transAxes,
        fontsize=10,
        color=GRAY,
        va="bottom",
    )

    axis.set_xlabel("2023 revenue")
    axis.set_ylabel("")
    axis.xaxis.set_major_formatter(
        FuncFormatter(millions)
    )

    axis.set_xlim(
        0,
        latest["REVENUE_MILLIONS"].max() * 1.18,
    )

    sns.despine(ax=axis)

    save_figure(
        figure,
        "04_top_ten_revenue.png",
    )


def main():
    sns.set_theme(
        style="whitegrid",
        context="notebook",
    )

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.family": "DejaVu Sans",
            "axes.titlecolor": "#111827",
            "axes.labelcolor": "#374151",
            "xtick.color": "#4B5563",
            "ytick.color": "#4B5563",
            "grid.color": "#E5E7EB",
            "grid.linewidth": 0.8,
        }
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = pd.read_csv(
        BALANCED_PANEL_PATH,
        dtype={"EIN_XML": "string"},
        low_memory=False,
    )

    year_summary = pd.read_csv(
        YEAR_SUMMARY_PATH,
        low_memory=False,
    )

    category_summary = pd.read_csv(
        CATEGORY_SUMMARY_PATH,
        low_memory=False,
    )

    if len(data) != 267:
        raise ValueError(
            f"Expected 267 balanced rows; found {len(data)}."
        )

    revenue_sensitivity_chart(data)
    operating_pressure_chart(year_summary)
    category_growth_chart(category_summary)
    revenue_concentration_chart(data)

    print("\nAll four financial charts exported successfully.")


if __name__ == "__main__":
    main()