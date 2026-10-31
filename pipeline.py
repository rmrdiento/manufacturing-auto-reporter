import sqlite3
from contextlib import closing

import pandas as pd

NUMERIC = ["planned_time_min", "downtime_min", "ideal_rate", "total_output", "defects"]
KEY = ["date", "line", "shift"]

# metric -> (good, warn, higher_is_better)
TARGETS = {
    "oee": (0.85, 0.65, True),
    "availability": (0.90, 0.80, True),
    "performance": (0.95, 0.85, True),
    "quality": (0.98, 0.96, True),
    "scrap_rate": (0.02, 0.04, False),
}


def status(metric, value):
    good, warn, higher = TARGETS[metric]
    if not higher:
        good, warn, value = -good, -warn, -value
    return "good" if value >= good else "warn" if value >= warn else "bad"


def validate(df):
    """Drop duplicate and invalid rows; return (clean_df, {issue: count})."""
    deduped = df.drop_duplicates(KEY)
    bad = (
        deduped[NUMERIC].isna().any(axis=1)
        | (deduped[NUMERIC] < 0).any(axis=1)
        | (deduped.planned_time_min <= 0)
        | (deduped.downtime_min > deduped.planned_time_min)
        | (deduped.defects > deduped.total_output)
    )
    issues = {"duplicates": len(df) - len(deduped), "invalid": int(bad.sum())}
    return deduped[~bad].reset_index(drop=True), issues


def load_db(df, db_path):
    with closing(sqlite3.connect(db_path)) as con:
        df.to_sql("production", con, if_exists="replace", index=False)


def summarize(df, by=None):
    """Availability, performance, quality, OEE and scrap from summed volumes."""
    d = df.assign(run_min=df.planned_time_min - df.downtime_min)
    d["ideal_output"] = d.run_min * d.ideal_rate
    s = d.groupby(by or (lambda _: "All"))[
        ["planned_time_min", "run_min", "downtime_min", "ideal_output", "total_output", "defects"]
    ].sum()
    s["availability"] = s.run_min / s.planned_time_min
    s["performance"] = (s.total_output / s.ideal_output).clip(upper=1)
    s["quality"] = 1 - s.defects / s.total_output
    s["oee"] = s.availability * s.performance * s.quality
    s["scrap_rate"] = 1 - s.quality
    return s


def downtime_pareto(df):
    p = df[df.downtime_min > 0].groupby("downtime_reason").downtime_min.sum()
    p = p.sort_values(ascending=False).to_frame("minutes")
    p["share"] = p.minutes / p.minutes.sum()
    p["cumulative"] = p.share.cumsum()
    return p


def run(csv_path, db_path):
    raw = pd.read_csv(csv_path, keep_default_na=False, na_values=[""], dtype={"downtime_reason": str})
    df, issues = validate(raw.assign(downtime_reason=raw.downtime_reason.fillna("")))
    load_db(df, db_path)
    with closing(sqlite3.connect(db_path)) as con:
        df = pd.read_sql("SELECT * FROM production", con)
    return {
        "period": (df.date.min(), df.date.max()),
        "issues": issues,
        "kpi": summarize(df).iloc[0],
        "matrix": summarize(df, ["line", "shift"]),
        "daily": summarize(df, "date"),
        "trend": summarize(df, ["date", "line"]).scrap_rate.unstack("line"),
        "pareto": downtime_pareto(df),
    }
