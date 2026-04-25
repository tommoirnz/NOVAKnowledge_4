# test_document.py — stress test for documentation cycle

import os
import re
import json
import math
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from functools import wraps


# ── Decorator (documenter must not confuse the wrapper with the method) ──────
def retry(max_attempts=3):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
            return None
        return wrapper
    return decorator


class DataProcessor:

    def __init__(self, data_dir: str = "data", verbose: bool = False):
        self.data_dir = data_dir
        self.verbose = verbose
        self.records: List[Dict] = []
        self.errors: List[str] = []
        self._cache: Dict[str, Any] = {}
        os.makedirs(data_dir, exist_ok=True)

    # ── Property — getter and setter must each get their own docstring ────────
    @property
    def record_count(self) -> int:
        return len(self.records)

    @record_count.setter
    def record_count(self, value: int):
        raise AttributeError("record_count is read-only")

    # ── Multiline signature ───────────────────────────────────────────────────
    def load_file(
        self,
        filename: str,
        encoding: str = "utf-8",
        strict: bool = False
    ) -> Optional[Dict]:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            self.errors.append(f"File not found: {filename}")
            return None
        try:
            with open(path, "r", encoding=encoding) as f:
                data = json.load(f)
            self.records = data.get("records", [])
            return data
        except Exception as e:
            if strict:
                raise
            self.errors.append(str(e))
            return None

    def save_file(self, filename: str) -> bool:
        path = os.path.join(self.data_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "records": self.records,
                    "saved": datetime.now().isoformat()
                }, f, indent=2)
            return True
        except Exception as e:
            self.errors.append(str(e))
            return False

    # ── Method containing a nested function ───────────────────────────────────
    def transform_records(self, field: str, fn) -> List[Any]:
        def _apply(record):
            val = record.get(field)
            return fn(val) if val is not None else None

        return [_apply(r) for r in self.records]

    # ── Method whose first statement is a real string (NOT a docstring) ───────
    # The documenter must insert the docstring BEFORE this line, not confuse it
    def get_status_label(self) -> str:
        label = "OK" if not self.errors else "ERROR"
        return f"{label} ({len(self.records)} records)"

    # ── Classmethod and staticmethod ──────────────────────────────────────────
    @classmethod
    def from_directory(cls, path: str) -> "DataProcessor":
        return cls(data_dir=path, verbose=True)

    @staticmethod
    def validate_record(record: Dict) -> bool:
        return isinstance(record, dict) and "id" in record

    # ── Decorated method (retry wrapper) ─────────────────────────────────────
    @retry(max_attempts=3)
    def fetch_remote(self, url: str) -> Optional[str]:
        import urllib.request
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.read().decode("utf-8")

    # ── Method with *args and **kwargs ────────────────────────────────────────
    def log(self, *args, level: str = "INFO", **kwargs):
        if self.verbose:
            parts = " ".join(str(a) for a in args)
            extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
            print(f"[{level}] {parts} {extras}".strip())

    # ── Longer method with multiple branches ──────────────────────────────────
    def merge(
        self,
        other: "DataProcessor",
        dedup_key: str = "id",
        overwrite: bool = False
    ) -> Tuple[int, int]:
        seen = {r[dedup_key]: i for i, r in enumerate(self.records) if dedup_key in r}
        added = 0
        updated = 0
        for record in other.records:
            key = record.get(dedup_key)
            if key is None:
                self.records.append(record)
                added += 1
            elif key in seen:
                if overwrite:
                    self.records[seen[key]] = record
                    updated += 1
            else:
                self.records.append(record)
                seen[key] = len(self.records) - 1
                added += 1
        return added, updated

    def filter_records(self, key: str, value: Any) -> List[Dict]:
        return [r for r in self.records if r.get(key) == value]

    def get_errors(self) -> List[str]:
        return list(self.errors)

    def clear(self):
        self.records.clear()
        self.errors.clear()
        self._cache.clear()


# ── Async function — LLM must not strip async keyword ────────────────────────
async def fetch_all(urls: List[str]) -> List[Optional[str]]:
    results = []
    for url in urls:
        try:
            reader, writer = await asyncio.open_connection(url, 80)
            writer.close()
            results.append(url)
        except Exception:
            results.append(None)
    return results


# ── Module-level functions with type hints ────────────────────────────────────
def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return ts


def extract_numbers(text: str) -> List[float]:
    return [float(m) for m in re.findall(r"\d+\.?\d*", text)]

# This does nothing, just a test for checking the auto-documentation system on Nova
# Note, it passes this test but may not work on Nova

def compute_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {}
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return {
        "mean": mean,
        "std": math.sqrt(variance),
        "min": min(values),
        "max": max(values),
        "count": float(n),
    }


def build_index(records: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    index: Dict[Any, List[Dict]] = {}
    for record in records:
        val = record.get(key)
        if val is not None:
            index.setdefault(val, []).append(record)
    return index