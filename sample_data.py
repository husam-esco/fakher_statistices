import random
from datetime import date, timedelta
from database import init_db, insert_production, insert_sells, log_upload

PRODUCTS = [
    "فلر 26 عادي", "بركر 14 عادي", "بركر 14 بوليش", "فلر 26 بوليش",
    "بركر 14 بطاطا", "بركر 13 عادي", "بركر 13 بوليش", "بركر 13 بطاطا",
    "فلر 26 سميد", "دبل باسطون", "سابوي", "همام عادي", "همام مشرح",
    "بركر 10 عادي", "مثلث", "بركر 11", "كنتاكي", "سابوي بوليش",
]
MAIN_NAMES = ["كنتاكي", "بركر 14 عادي", "بركر 14 بوليش", "بركر 14 بطاطا",
              "بركر 13 عادي", "بركر 13 بوليش", "بركر 13 بطاطا", "فلر 26 عادي",
              "فلر 26 بوليش", "فلر 26 سميد", "دبل باسطون", "سابوي"]


def generate_sample_data(days: int = 90):
    init_db()
    today = date.today()
    start = today - timedelta(days=days)

    for i in range(days + 1):
        d = start + timedelta(days=i)
        if d >= today:
            continue

        n_prod = random.randint(8, 15)
        prod_records = []
        used_products = random.sample(PRODUCTS, min(n_prod, len(PRODUCTS)))
        for p in used_products:
            amt = random.randint(100, 8000)
            trf = random.randint(0, amt + 2000)
            prod_records.append({"product_name": p, "amount": amt, "transfer": trf})

        n_sells = random.randint(10, 18)
        sells_records = []
        used_sells = random.sample(MAIN_NAMES, min(n_sells, len(MAIN_NAMES)))
        for s in used_sells:
            amt = random.randint(200, 10000)
            main = random.choice(["كنتاكي", "بركر", "فلر", "سابوي", "همام"])
            trf = random.randint(0, amt + 1000)
            sells_records.append({
                "product_name": s,
                "amount": amt,
                "main_name": main,
                "transfer": trf,
            })

        insert_production(d, prod_records)
        insert_sells(d, sells_records)
        log_upload(f"sample_{d.isoformat()}.xlsx", d, len(prod_records), len(sells_records))

    return days + 1
