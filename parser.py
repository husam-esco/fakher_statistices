import re
import pandas as pd
from datetime import date, datetime


def extract_date_from_filename(filename: str) -> date | None:
    base = filename.rsplit(".", 1)[0]
    patterns = [
        (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%d-%m-%Y"),
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
        (r"(\d{1,2})-(\d{1,2})-(\d{2})", "%d-%m-%y"),
    ]
    for pat, fmt in patterns:
        m = re.search(pat, base)
        if m:
            try:
                return datetime.strptime(m.group(0), fmt).date()
            except ValueError:
                continue
    m = re.search(r"(\d{1,2})", base)
    if m:
        day = int(m.group(1))
        if 1 <= day <= 31:
            today = date.today()
            return date(today.year, today.month, day)
    return None


def parse_excel(file_path: str, report_date: date | None = None) -> dict:
    df_raw = pd.read_excel(file_path, header=None).fillna("")
    if report_date is None:
        report_date = extract_date_from_filename(file_path)
    if report_date is None:
        report_date = date.today()

    production = []
    sells = []

    for idx, row in df_raw.iterrows():
        if idx < 2:
            continue
        vals = [str(v).strip() for v in row.values]

        col0 = vals[0]
        col4 = vals[4]

        prod_name = col0
        prod_amt = _parse_num(vals[1]) if len(vals) > 1 else 0
        prod_trf = _parse_num(vals[2]) if len(vals) > 2 else 0

        if prod_name and prod_name not in ("", "Product Name", "Production Section"):
            if prod_name != "0" or prod_amt != 0 or prod_trf != 0:
                production.append({
                    "product_name": prod_name,
                    "amount": prod_amt,
                    "transfer": prod_trf,
                })

        sells_name = col4
        sells_amt = _parse_num(vals[5]) if len(vals) > 5 else 0
        sells_main = vals[6] if len(vals) > 6 else ""
        sells_trf = _parse_num(vals[7]) if len(vals) > 7 else 0

        if sells_name and sells_name not in ("", "Product Name", "Sells Section"):
            if sells_name != "0" or sells_amt != 0 or sells_trf != 0:
                sells.append({
                    "product_name": sells_name,
                    "amount": sells_amt,
                    "main_name": sells_main,
                    "transfer": sells_trf,
                })

    return {
        "report_date": report_date,
        "production": production,
        "sells": sells,
    }


def _parse_num(val) -> float:
    if isinstance(val, (int, float)):
        return float(val) if not pd.isna(val) else 0.0
    s = str(val).strip().replace(",", "").replace(" ", "")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0
