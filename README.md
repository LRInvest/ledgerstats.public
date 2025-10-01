# LedgerStats Public

**LedgerStats Public** is the permanent home for canonical blockchain datasets and the scripts that generate them.  
This repository exists to preserve **verifiable, reproducible records** of critical chain data — starting with the Ethereum genesis ledger.

---

## 📂 Repository Layout

```text
ledgerstats.public/
│   README.md        → Project overview
│   LICENSE          → License (MIT, Apache, etc.)
│
└───core/
    ├───scripts/     → Python scripts for extracting and verifying data
    │     dump_genesis_alloc.py   # Crawl genesis allocation from an archive node
    │     genesis_builder.py      # Build structured Delta/CSV/JSON exports
    │
    └───static/      → Canonical dataset exports
          genesis_eth.csv         # Ethereum Genesis Ledger (CSV)
          genesis_eth.json        # Ethereum Genesis Ledger (JSON)
```

---

## 📊 Data Flow

```text
Erigon RPC 
   ↓
dump_genesis_alloc.py 
   ↓
genesis_alloc.csv 
   ↓
genesis_builder.py 
   ↓
{ CSV / JSON + Delta Lake + Postgres }
```

---

## 🔍 What’s Inside

### Ethereum Genesis Ledger
- **CSV Export:** [`genesis_eth.csv`](core/static/genesis_eth.csv)  
- **JSON Export:** [`genesis_eth.json`](core/static/genesis_eth.json)  

This dataset is the canonical allocation at Ethereum genesis (block 0).

- **Total Supply:** `72,009,990.5 ETH`  
- **Source:** Crawled from an Erigon archive node (`debug_accountRange`)  
- **Process:**  
  1. Full genesis trie exported with [`dump_genesis_alloc.py`](core/scripts/dump_genesis_alloc.py)  
  2. Data built and verified with [`genesis_builder.py`](core/scripts/genesis_builder.py)  
  3. Published as CSV + JSON for permanent reference  

---

## 🎯 Why This Repo Exists

LedgerStats aims to make **onchain history transparent and verifiable**.  
Many metrics like **MVRV** or realized price rely on a clean, immutable record of historical supply and balances.  
By publishing these exports openly, we create a shared baseline for researchers, developers, and analysts to build on.

---

## 🚀 Quick Start

You can reproduce the genesis dataset yourself using the included scripts.

### 1. Requirements
- Python 3.9+  
- An [Erigon](https://github.com/ledgerwatch/erigon) archive node with `--private.api` enabled  
- Install dependencies:

```bash
pip install requests pandas psycopg2-binary deltalake
```

### 2. Dump the Genesis Allocation
This script crawls the genesis trie using Erigon’s `debug_accountRange` RPC method.

```bash
cd core/scripts
python dump_genesis_alloc.py
```

- Output: `genesis_alloc.csv`  
- Progress and checkpoints are saved so you can resume if interrupted.  
- Each row includes: `address,balance_wei`.

### 3. Build the Genesis Ledger
Once you have the CSV, stage it into structured exports and (optionally) Delta Lake.

```bash
python genesis_builder.py
```

What it does:
- ✅ Verifies the genesis total = `72,009,990.5 ETH`  
- ✅ Creates structured rows with fields like `block_number`, `from_address`, `to_address`, `amount_wei`, `tx_type`, etc.  
- ✅ Appends the data into your configured **Delta Lake** path (`DELTA_PATH`)  
- ✅ Writes audit & supply records into PostgreSQL (configured in `PG_CONFIG`)  

---

## 📜 License

This project is released under the [MIT License](LICENSE).  
You’re free to use, adapt, and share the code and datasets — attribution is appreciated.
