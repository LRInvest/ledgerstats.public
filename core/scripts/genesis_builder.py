# core/eth/utils_scripts/genesis_builder.py

import os
import sys
import csv
import pandas as pd
import psycopg2

from core.eth.lib_eth.utils import ZERO_ADDRESS
from core.eth.lib_eth.audit import write_audit, write_supply
from core.eth.lib_eth.config import PG_CONFIG, DELTA_PATH
from deltalake.writer import write_deltalake

EXPECTED_TOTAL_WEI = 72_009_990_499_480_000_000_000_000
GENESIS_TS = pd.Timestamp("2015-07-30 00:00:00", tz="UTC")

# Resolve a friendly default: project-root/genesis_alloc.csv
DEFAULT_GENESIS = os.path.join(os.getcwd(), "genesis_alloc_dedup.csv")
GENESIS_FILE = os.path.expanduser(os.getenv("GENESIS_FILE", DEFAULT_GENESIS))

def get_conn():
    return psycopg2.connect(**PG_CONFIG)

def is_int_string(s: str) -> bool:
    s = s.strip()
    return s.isdigit()

def load_genesis_alloc():
    if not os.path.exists(GENESIS_FILE):
        print(f"❌ GENESIS_FILE not found: {GENESIS_FILE}")
        sys.exit(1)

    allocs = []
    bad = 0
    with open(GENESIS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        required = {"address", "balance_wei"}
        if set(reader.fieldnames or []) >= required:
            pass
        else:
            print(f"❌ CSV header missing required columns. Found: {reader.fieldnames}")
            sys.exit(1)

        for i, row in enumerate(reader, start=2):  # start=2 since header is line 1
            addr = (row.get("address") or "").strip().lower()
            bal_str = (row.get("balance_wei") or "").strip()

            # Skip any garbage/header rows
            if not addr or not is_int_string(bal_str):
                bad += 1
                continue

            allocs.append({"address": addr, "balance": int(bal_str)})

    if bad:
        print(f"⚠️  Skipped {bad} non-numeric/garbage row(s) while loading {GENESIS_FILE}")
    if not allocs:
        print("❌ No valid allocations found after filtering.")
        sys.exit(1)

    return allocs

def stage_genesis():
    print(f"📄 Loading genesis allocs from: {GENESIS_FILE}")
    allocs = load_genesis_alloc()

    rows = []
    for entry in allocs:
        rows.append({
            "block_number": 0,
            "block_ts": GENESIS_TS,
            "tx_hash": "0xgenesis",
            "from_address": ZERO_ADDRESS,
            "to_address": entry["address"],
            "amount_wei": str(entry["balance"]),
            "token_id": 1,
            "tx_type": "alloc",
            "tx_subtype": "issuance",
            "success": True,
        })

    # Verify total BEFORE any writes
    total_wei = sum(int(r["amount_wei"]) for r in rows)
    if total_wei != EXPECTED_TOTAL_WEI:
        print("❌ Mismatch in genesis supply!")
        print(f"   Expected: {EXPECTED_TOTAL_WEI:,}")
        print(f"   Got:      {total_wei:,}")
        sys.exit(1)
    else:
        print(f"✅ Verified genesis supply: {total_wei:,} wei")
        print(f"✅ Accounts: {len(rows):,}")

    # Prepare partitions for Delta
    df = pd.DataFrame(rows)
    df["year"] = df["block_ts"].dt.year
    df["month"] = df["block_ts"].dt.month

    # Append into delta ledger (same schema/partitions as your pipeline)
    write_deltalake(DELTA_PATH, df, mode="append", partition_by=["year", "month"])

    # Audit + supply rows for block 0
    audit_row = {
        "block_number": 0,
        "block_ts": GENESIS_TS,
        "expected_delta": total_wei,
        "actual_delta": total_wei,
        "variance": 0,
        "within_margin": True,
        "balanced": True,
        "posted": True,
        "checked_at": pd.Timestamp.utcnow(),
        "chain_hash": "0xgenesis",
    }

    supply_row = {
        "block_number": 0,
        "block_ts": GENESIS_TS,
        "issuance_wei": total_wei,
        "burn_wei": 0,
        "tips_wei": 0,
        "withdrawals_wei": 0,
        "net_delta_wei": total_wei,
        "tx_count": len(rows),
    }

    with get_conn() as conn:
        write_audit(conn, [audit_row])
        write_supply(conn, [supply_row])

    print("🎉 Staged genesis into ledger, audit, and supply successfully.")

if __name__ == "__main__":
    stage_genesis()
