from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BALANCED_DATA_PATH = (
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

STRUCTURAL_CHANGE_EIN = "911935159"

NTEE_LABELS = {
    "E": "E — General and rehabilitative health",
    "F": "F — Mental health and crisis intervention",
    "G": "G — Diseases and medical disciplines",
    "H": "H — Medical research",
}

COLORS = {
    "navy": "#2B5F85",
    "teal": "#2A9D8F",
    "orange": "#E76F51",
    "gold": "#E9C46A",
}


st.set_page_config(
    page_title="King County Health Nonprofits",
    page_icon="🏥",
    layout="wide",
)


def clean_ein(series):
    """Normalize EIN values as nine-character strings."""
    return (
        series.astype("string")
        .str.replace(r"\D", "", regex=True)
        .str.zfill(9)
    )


@st.cache_data
def load_data():
    """Load and enrich the balanced analysis panel."""
    data = pd.read_csv(
        BALANCED_DATA_PATH,
        dtype={
            "EIN_XML": "string",
            "ZIP_CODE": "string",
            "OBJECT_ID": "string",
        },
        low_memory=False,
    )

    source = pd.read_csv(
        SOURCE_PANEL_PATH,
        dtype=str,
        low_memory=False,
    )

    data["EIN_CLEAN"] = clean_ein(
        data["EIN_XML"]
    )

    source["EIN_CLEAN"] = clean_ein(
        source["EIN"]
    )

    classification = (
        source.sort_values(
            [
                "EIN_CLEAN",
                "FILING_YEAR",
                "OBJECT_ID",
            ],
            kind="stable",
        )
        .drop_duplicates(
            "EIN_CLEAN",
            keep="last",
        )
        [
            [
                "EIN_CLEAN",
                "NTEE_CD",
                "NTEE_MAJOR",
            ]
        ]
    )

    return data.merge(
        classification,
        on="EIN_CLEAN",
        how="left",
        validate="many_to_one",
    )


def standard_layout(figure, height=420):
    """Apply consistent formatting to a Plotly figure."""
    figure.update_layout(
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=65,
            b=20,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hoverlabel=dict(
            namelength=-1,
        ),
    )

    return figure


data = load_data()


st.sidebar.header("Dashboard filters")

available_groups = sorted(
    data["NTEE_MAJOR"].dropna().unique()
)

selected_groups = st.sidebar.multiselect(
    "Health categories",
    options=available_groups,
    default=available_groups,
    format_func=lambda value: NTEE_LABELS[value],
)

selected_year = st.sidebar.selectbox(
    "Snapshot tax year",
    options=sorted(
        data["TAX_YEAR_ANALYSIS"].unique(),
        reverse=True,
    ),
)

include_structural_change = st.sidebar.checkbox(
    "Include SCCA–Fred Hutch",
    value=True,
    help=(
        "This organization underwent a major structural "
        "change in April 2022. Its financial growth is not "
        "fully comparable across the period."
    ),
)


if not selected_groups:
    st.warning(
        "Select at least one health category."
    )

    st.stop()


category_filtered = data[
    data["NTEE_MAJOR"].isin(selected_groups)
].copy()

filtered = category_filtered.copy()

if not include_structural_change:
    filtered = filtered[
        filtered["EIN_CLEAN"]
        != STRUCTURAL_CHANGE_EIN
    ].copy()


snapshot = filtered[
    filtered["TAX_YEAR_ANALYSIS"]
    == selected_year
].copy()


st.title("King County Health Nonprofits")

st.write(
    "Financial trends among organizations with comparable "
    "Form 990 filings in tax years 2021–2023."
)

st.caption(
    "Balanced panel: every included organization has one "
    "comparable filing in each of the three tax years."
)


if include_structural_change:
    st.info(
        "Seattle Cancer Care Alliance and Fred Hutchinson "
        "Cancer Research Center combined in April 2022. "
        "Use the sidebar checkbox to view aggregate results "
        "without this structural change."
    )


organization_count = snapshot["EIN_CLEAN"].nunique()
total_revenue = snapshot["TOTAL_REVENUE"].sum()
total_expenses = snapshot["TOTAL_EXPENSES"].sum()

negative_margin_count = (
    snapshot["OPERATING_SURPLUS"] < 0
).sum()

negative_margin_rate = (
    negative_margin_count / organization_count
    if organization_count
    else 0
)


column_1, column_2, column_3, column_4 = st.columns(4)

column_1.metric(
    "Organizations",
    f"{organization_count:,}",
)

column_2.metric(
    f"{selected_year} revenue",
    f"${total_revenue / 1_000_000_000:.2f}B",
)

column_3.metric(
    f"{selected_year} expenses",
    f"${total_expenses / 1_000_000_000:.2f}B",
)

column_4.metric(
    "Operating deficits",
    f"{negative_margin_count:,}",
    delta=f"{negative_margin_rate:.0%} of organizations",
    delta_color="off",
)


overview_tab, category_tab, organization_tab = st.tabs(
    [
        "Sector overview",
        "Category comparison",
        "Organization explorer",
    ]
)


with overview_tab:
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Revenue sensitivity")

        full_trend = (
            category_filtered.groupby(
                "TAX_YEAR_ANALYSIS"
            )["TOTAL_REVENUE"]
            .sum()
            .sort_index()
        )

        excluding_trend = (
            category_filtered[
                category_filtered["EIN_CLEAN"]
                != STRUCTURAL_CHANGE_EIN
            ]
            .groupby(
                "TAX_YEAR_ANALYSIS"
            )["TOTAL_REVENUE"]
            .sum()
            .sort_index()
        )

        revenue_figure = go.Figure()

        revenue_figure.add_trace(
            go.Scatter(
                x=full_trend.index,
                y=full_trend.values / 1_000_000_000,
                mode="lines+markers",
                name="Full selected cohort",
                line=dict(
                    color=COLORS["navy"],
                    width=3,
                ),
                marker=dict(size=9),
                hovertemplate=(
                    "Tax year %{x}<br>"
                    "Revenue: $%{y:.2f}B"
                    "<extra></extra>"
                ),
            )
        )

        if (
            STRUCTURAL_CHANGE_EIN
            in set(category_filtered["EIN_CLEAN"])
        ):
            revenue_figure.add_trace(
                go.Scatter(
                    x=excluding_trend.index,
                    y=(
                        excluding_trend.values
                        / 1_000_000_000
                    ),
                    mode="lines+markers",
                    name="Excluding SCCA–Fred Hutch",
                    line=dict(
                        color=COLORS["teal"],
                        width=3,
                    ),
                    marker=dict(size=9),
                    hovertemplate=(
                        "Tax year %{x}<br>"
                        "Revenue: $%{y:.2f}B"
                        "<extra></extra>"
                    ),
                )
            )

            revenue_figure.add_vline(
                x=2022,
                line_dash="dash",
                line_color="gray",
            )

            revenue_figure.add_annotation(
                x=2022,
                y=0,
                text="Merger effective April 2022",
                showarrow=False,
                xanchor="left",
                yanchor="bottom",
                font=dict(color="gray"),
            )

        revenue_figure.update_layout(
            xaxis=dict(
                title="Tax year",
                tickmode="array",
                tickvals=[2021, 2022, 2023],
            ),
            yaxis_title="Revenue ($ billions)",
            yaxis_rangemode="tozero",
            hovermode="x unified",
        )

        st.plotly_chart(
            standard_layout(revenue_figure),
            width="stretch",
        )

    with right_column:
        st.subheader("Operating pressure")

        deficit_summary = (
            filtered.assign(
                NEGATIVE_MARGIN=(
                    filtered["OPERATING_SURPLUS"] < 0
                )
            )
            .groupby("TAX_YEAR_ANALYSIS")
            .agg(
                ORGANIZATIONS=(
                    "EIN_CLEAN",
                    "nunique",
                ),
                DEFICIT_ORGANIZATIONS=(
                    "NEGATIVE_MARGIN",
                    "sum",
                ),
            )
            .reset_index()
        )

        deficit_summary["DEFICIT_RATE"] = (
            deficit_summary["DEFICIT_ORGANIZATIONS"]
            / deficit_summary["ORGANIZATIONS"]
        )

        deficit_figure = go.Figure(
            go.Bar(
                x=deficit_summary[
                    "TAX_YEAR_ANALYSIS"
                ],
                y=deficit_summary[
                    "DEFICIT_ORGANIZATIONS"
                ],
                marker_color=COLORS["orange"],
                text=[
                    (
                        f"{count} ({rate:.0%})"
                    )
                    for count, rate in zip(
                        deficit_summary[
                            "DEFICIT_ORGANIZATIONS"
                        ],
                        deficit_summary[
                            "DEFICIT_RATE"
                        ],
                    )
                ],
                textposition="outside",
                hovertemplate=(
                    "Tax year %{x}<br>"
                    "Deficit organizations: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        deficit_figure.update_layout(
            xaxis=dict(
                title="Tax year",
                tickmode="array",
                tickvals=[2021, 2022, 2023],
            ),
            yaxis_title="Organizations with deficits",
            yaxis_rangemode="tozero",
            showlegend=False,
        )

        st.plotly_chart(
            standard_layout(deficit_figure),
            width="stretch",
        )


    st.subheader(
        f"Largest organizations by {selected_year} revenue"
    )

    top_organizations = (
        snapshot.nlargest(
            10,
            "TOTAL_REVENUE",
        )
        .sort_values(
            "TOTAL_REVENUE",
        )
        .copy()
    )

    ranking_figure = go.Figure(
        go.Bar(
            x=(
                top_organizations["TOTAL_REVENUE"]
                / 1_000_000
            ),
            y=top_organizations[
                "ORGANIZATION_NAME"
            ],
            orientation="h",
            marker_color=COLORS["navy"],
            text=[
                f"${value / 1_000_000:,.0f}M"
                for value in top_organizations[
                    "TOTAL_REVENUE"
                ]
            ],
            textposition="outside",
            hovertemplate=(
                "%{y}<br>"
                "Revenue: $%{x:,.0f}M"
                "<extra></extra>"
            ),
        )
    )
    ranking_figure.update_traces(
        cliponaxis=False,
    )

    ranking_figure.update_layout(
        xaxis_title=f"{selected_year} revenue ($ millions)",
        yaxis_title="",
        xaxis_rangemode="tozero",
        xaxis_range=[
            0,
            (
                top_organizations[
                    "TOTAL_REVENUE"
                ].max()
                / 1_000_000
                * 1.18
            ),
        ],
        showlegend=False,
    )

    st.plotly_chart(
        standard_layout(
            ranking_figure,
            height=520,
        ),
        width="stretch",
    )


with category_tab:
    st.subheader(
        "Median financial growth by health category"
    )

    revenue_pivot = filtered.pivot(
        index=[
            "EIN_CLEAN",
            "NTEE_MAJOR",
        ],
        columns="TAX_YEAR_ANALYSIS",
        values="TOTAL_REVENUE",
    )

    expense_pivot = filtered.pivot(
        index=[
            "EIN_CLEAN",
            "NTEE_MAJOR",
        ],
        columns="TAX_YEAR_ANALYSIS",
        values="TOTAL_EXPENSES",
    )

    organization_growth = pd.DataFrame(
        {
            "REVENUE_GROWTH": (
                revenue_pivot[2023]
                / revenue_pivot[2021]
                - 1
            ),
            "EXPENSE_GROWTH": (
                expense_pivot[2023]
                / expense_pivot[2021]
                - 1
            ),
        }
    ).reset_index()

    category_growth = (
        organization_growth.groupby(
            "NTEE_MAJOR"
        )
        .agg(
            ORGANIZATIONS=(
                "EIN_CLEAN",
                "nunique",
            ),
            MEDIAN_REVENUE_GROWTH=(
                "REVENUE_GROWTH",
                "median",
            ),
            MEDIAN_EXPENSE_GROWTH=(
                "EXPENSE_GROWTH",
                "median",
            ),
        )
        .reset_index()
    )

    category_growth["LABEL"] = [
        f"{group} (n={count})"
        for group, count in zip(
            category_growth["NTEE_MAJOR"],
            category_growth["ORGANIZATIONS"],
        )
    ]

    category_figure = go.Figure()

    category_figure.add_trace(
        go.Bar(
            x=category_growth["LABEL"],
            y=(
                category_growth[
                    "MEDIAN_REVENUE_GROWTH"
                ]
                * 100
            ),
            name="Median revenue growth",
            marker_color=COLORS["teal"],
            text=[
                f"{value:.1%}"
                for value in category_growth[
                    "MEDIAN_REVENUE_GROWTH"
                ]
            ],
            textposition="outside",
        )
    )

    category_figure.add_trace(
        go.Bar(
            x=category_growth["LABEL"],
            y=(
                category_growth[
                    "MEDIAN_EXPENSE_GROWTH"
                ]
                * 100
            ),
            name="Median expense growth",
            marker_color=COLORS["orange"],
            text=[
                f"{value:.1%}"
                for value in category_growth[
                    "MEDIAN_EXPENSE_GROWTH"
                ]
            ],
            textposition="outside",
        )
    )

    category_figure.update_layout(
        barmode="group",
        xaxis_title="NTEE major health group",
        yaxis_title="Median growth, 2021–2023 (%)",
        yaxis_rangemode="tozero",
    )

    st.plotly_chart(
        standard_layout(
            category_figure,
            height=520,
        ),
        width="stretch",
    )

    st.caption(
        "Interpret G and H cautiously because their balanced "
        "samples are small."
    )


with organization_tab:
    latest_names = (
        filtered.sort_values(
            [
                "EIN_CLEAN",
                "TAX_YEAR_ANALYSIS",
            ]
        )
        .drop_duplicates(
            "EIN_CLEAN",
            keep="last",
        )
        .set_index("EIN_CLEAN")[
            "ORGANIZATION_NAME"
        ]
        .to_dict()
    )

    selected_ein = st.selectbox(
        "Select an organization",
        options=sorted(latest_names),
        format_func=lambda value: latest_names[value],
    )

    organization_history = (
        filtered[
            filtered["EIN_CLEAN"] == selected_ein
        ]
        .sort_values(
            "TAX_YEAR_ANALYSIS"
        )
        .copy()
    )

    organization_figure = go.Figure()

    organization_figure.add_trace(
        go.Scatter(
            x=organization_history[
                "TAX_YEAR_ANALYSIS"
            ],
            y=(
                organization_history[
                    "TOTAL_REVENUE"
                ]
                / 1_000_000
            ),
            mode="lines+markers",
            name="Revenue",
            line=dict(
                color=COLORS["teal"],
                width=3,
            ),
            marker=dict(size=9),
        )
    )

    organization_figure.add_trace(
        go.Scatter(
            x=organization_history[
                "TAX_YEAR_ANALYSIS"
            ],
            y=(
                organization_history[
                    "TOTAL_EXPENSES"
                ]
                / 1_000_000
            ),
            mode="lines+markers",
            name="Expenses",
            line=dict(
                color=COLORS["orange"],
                width=3,
            ),
            marker=dict(size=9),
        )
    )

    organization_figure.update_layout(
        xaxis=dict(
            title="Tax year",
            tickmode="array",
            tickvals=[2021, 2022, 2023],
        ),
        yaxis_title="$ millions",
        hovermode="x unified",
        yaxis_rangemode="tozero",
    )

    st.plotly_chart(
        standard_layout(
            organization_figure,
            height=500,
        ),
        width="stretch",
    )

    organization_table = organization_history[
        [
            "TAX_YEAR_ANALYSIS",
            "TOTAL_REVENUE",
            "TOTAL_EXPENSES",
            "OPERATING_SURPLUS",
            "OPERATING_MARGIN",
            "TOTAL_ASSETS_EOY",
            "TOTAL_EMPLOYEES",
        ]
    ].copy()

    organization_table["OPERATING_MARGIN"] *= 100

    st.dataframe(
        organization_table,
        width="stretch",
        hide_index=True,
        column_config={
            "TAX_YEAR_ANALYSIS": "Tax year",
            "TOTAL_REVENUE": st.column_config.NumberColumn(
                "Revenue",
                format="$%,d",
            ),
            "TOTAL_EXPENSES": st.column_config.NumberColumn(
                "Expenses",
                format="$%,d",
            ),
            "OPERATING_SURPLUS": st.column_config.NumberColumn(
                "Operating surplus",
                format="$%,d",
            ),
            "OPERATING_MARGIN": st.column_config.NumberColumn(
                "Operating margin",
                format="%.1f%%",
            ),
            "TOTAL_ASSETS_EOY": st.column_config.NumberColumn(
                "Year-end assets",
                format="$%,d",
            ),
            "TOTAL_EMPLOYEES": st.column_config.NumberColumn(
                "Employees",
                format="%,d",
            ),
        },
    )


with st.expander("Methodology and limitations"):
    st.markdown(
        """
- **Balanced panel:** 89 organizations with comparable
  Form 990 filings in tax years 2021, 2022, and 2023.
- **Health scope:** IRS NTEE major groups E, F, G, and H.
- **Geography:** IRS mailing ZIP codes assigned primarily
  to King County using Census ZCTA geography.
- **Structural change:** Seattle Cancer Care Alliance and
  Fred Hutchinson Cancer Research Center combined in April
  2022, so their growth is not fully comparable.
- **Missing records:** 77 filings listed in the 2022 IRS
  index were absent from the official XML archive.
- **Interpretation:** Filing availability and small category
  samples may affect representativeness.
        """
    )


download_data = filtered.drop(
    columns=["EIN_CLEAN"],
    errors="ignore",
).to_csv(index=False)

st.download_button(
    "Download filtered balanced-panel data",
    data=download_data,
    file_name="king_county_health_nonprofits_filtered.csv",
    mime="text/csv",
)