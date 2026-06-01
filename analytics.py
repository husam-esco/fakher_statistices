import pandas as pd
from datetime import date, timedelta
from database import fetch_cumulative_data


def load_dataframe(section: str, start_date: date = None, end_date: date = None) -> pd.DataFrame:
    rows = fetch_cumulative_data(section, start_date, end_date)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df


class Aggregator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() if not df.empty else df
        if not self.df.empty:
            self.df["report_date"] = pd.to_datetime(self.df["report_date"])
            self.df.sort_values("report_date", inplace=True)

    def total_amount(self) -> float:
        if self.df.empty:
            return 0.0
        return float(self.df["amount"].sum())

    def total_transfer(self) -> float:
        if self.df.empty or "transfer" not in self.df.columns:
            return 0.0
        return float(self.df["transfer"].sum())

    def by_day(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["report_date", "amount", "transfer"])
        return self.df.groupby("report_date").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).reset_index()

    def by_week(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["week_start", "week_end", "amount", "transfer"])
        df = self.df.copy()
        df["week_start"] = df["report_date"] - pd.to_timedelta(df["report_date"].dt.weekday, unit="D")
        df["week_end"] = df["week_start"] + pd.Timedelta(days=6)
        return df.groupby(["week_start", "week_end"]).agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).reset_index()

    def by_month(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["month", "amount", "transfer"])
        df = self.df.copy()
        df["month"] = df["report_date"].dt.to_period("M").dt.to_timestamp()
        return df.groupby("month").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).reset_index()

    def by_quarter(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["quarter", "amount", "transfer"])
        df = self.df.copy()
        df["quarter"] = df["report_date"].dt.to_period("Q").dt.to_timestamp()
        return df.groupby("quarter").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).reset_index()

    def by_year(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["year", "amount", "transfer"])
        df = self.df.copy()
        df["year"] = df["report_date"].dt.to_period("Y").dt.to_timestamp()
        return df.groupby("year").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).reset_index()

    def top_products(self, n: int = 10) -> pd.DataFrame:
        if self.df.empty or "product_name" not in self.df.columns:
            return pd.DataFrame(columns=["product_name", "amount", "transfer"])
        return self.df.groupby("product_name").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).sort_values("amount", ascending=False).head(n).reset_index()

    def category_breakdown(self) -> pd.DataFrame:
        if self.df.empty or "main_name" not in self.df.columns:
            return pd.DataFrame(columns=["main_name", "amount", "transfer"])
        return self.df.groupby("main_name").agg(
            amount=("amount", "sum"),
            transfer=("transfer", "sum")
        ).sort_values("amount", ascending=False).reset_index()


class KPIEngine:
    def __init__(self, section: str):
        self.section = section

    def current_vs_previous(self, period: str = "day") -> dict:
        today = date.today()
        if period == "day":
            current_start = today
            prev_end = today - timedelta(days=1)
            prev_start = prev_end
        elif period == "week":
            current_start = today - timedelta(days=today.weekday())
            prev_start = current_start - timedelta(days=7)
            prev_end = current_start - timedelta(days=1)
        elif period == "month":
            current_start = today.replace(day=1)
            prev_end = current_start - timedelta(days=1)
            prev_start = prev_end.replace(day=1)
        elif period == "quarter":
            q = (today.month - 1) // 3
            current_start = date(today.year, q * 3 + 1, 1)
            prev_q_end = current_start - timedelta(days=1)
            prev_q = (prev_q_end.month - 1) // 3
            prev_start = date(prev_q_end.year, prev_q * 3 + 1, 1)
            prev_end = prev_q_end
        elif period == "year":
            current_start = date(today.year, 1, 1)
            prev_start = date(today.year - 1, 1, 1)
            prev_end = date(today.year - 1, 12, 31)
        else:
            return {}

        current_df = load_dataframe(self.section, current_start, today)
        prev_df = load_dataframe(self.section, prev_start, prev_end)

        current_amount = float(current_df["amount"].sum()) if not current_df.empty else 0.0
        prev_amount = float(prev_df["amount"].sum()) if not prev_df.empty else 0.0

        if prev_amount != 0:
            pct_change = ((current_amount - prev_amount) / prev_amount) * 100
        else:
            pct_change = 100.0 if current_amount > 0 else 0.0

        return {
            "current": current_amount,
            "previous": prev_amount,
            "change": current_amount - prev_amount,
            "pct_change": round(pct_change, 1),
            "period": period,
            "is_positive": current_amount >= prev_amount,
        }

    def date_range_kpis(self, start_date: date, end_date: date) -> dict:
        df = load_dataframe(self.section, start_date, end_date)
        if df.empty:
            return {"amount": 0, "transfer": 0, "avg_daily": 0, "total_days": 0}
        total_days = max(1, (end_date - start_date).days + 1)
        total_amount = float(df["amount"].sum())
        total_transfer = float(df["transfer"].sum()) if "transfer" in df.columns else 0
        return {
            "amount": total_amount,
            "transfer": total_transfer,
            "avg_daily": round(total_amount / total_days, 1),
            "total_days": total_days,
        }
