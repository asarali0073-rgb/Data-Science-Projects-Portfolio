import csv
import json
import math
from pathlib import Path
import re


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "amazon.csv"
MODEL_PATH = BASE_DIR / "discount_model.json"


def parse_number(value):
    cleaned = re.sub(r"[^\d.]", "", value or "")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def add_value(groups, key, value):
    group = groups.setdefault(str(key), {"count": 0, "total": 0.0})
    group["count"] += 1
    group["total"] += value


def summarize(groups):
    return {
        key: {"count": group["count"], "mean": group["total"] / group["count"]}
        for key, group in groups.items()
    }


def train():
    category_groups = {}
    bucket_groups = {
        "rating": {},
        "actual_price": {},
        "rating_count": {},
    }
    global_total = 0.0
    row_count = 0

    with DATA_PATH.open(encoding="utf-8-sig", newline="") as data_file:
        for row in csv.DictReader(data_file):
            category = (row.get("category") or "").strip()
            actual_price = parse_number(row.get("actual_price"))
            rating = parse_number(row.get("rating"))
            rating_count = parse_number(row.get("rating_count"))
            discount = parse_number(row.get("discount_percentage"))
            if (
                not category
                or actual_price is None
                or rating is None
                or rating_count is None
                or discount is None
                or actual_price <= 0
                or not 0 <= rating <= 5
                or rating_count < 0
                or not 0 <= discount <= 100
            ):
                continue

            add_value(category_groups, category, discount)
            rating_bucket = min(10, int(rating * 2))
            price_bucket = sum(
                actual_price >= threshold
                for threshold in (500, 1000, 2500, 5000, 10000, 25000)
            )
            count_bucket = sum(
                rating_count >= threshold for threshold in (10, 100, 1000, 10000)
            )
            add_value(bucket_groups["rating"], rating_bucket, discount)
            add_value(bucket_groups["actual_price"], price_bucket, discount)
            add_value(bucket_groups["rating_count"], count_bucket, discount)
            global_total += discount
            row_count += 1

    if not row_count:
        raise ValueError(f"No valid training rows found in {DATA_PATH}.")

    model = {
        "global_mean": global_total / row_count,
        "categories": summarize(category_groups),
        "buckets": {
            feature: summarize(groups) for feature, groups in bucket_groups.items()
        },
    }
    with MODEL_PATH.open("w", encoding="utf-8") as model_file:
        json.dump(model, model_file, separators=(",", ":"))
    print(
        f"Trained on {row_count} rows across "
        f"{len(model['categories'])} categories. Saved {MODEL_PATH.name}."
    )


if __name__ == "__main__":
    train()
