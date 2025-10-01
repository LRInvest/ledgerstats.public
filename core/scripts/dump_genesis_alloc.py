#!/usr/bin/env python3
import requests, csv, time

RPC_URL = "http://127.0.0.1:8546"
GENESIS_HASH = "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
BATCH = 5
OUTFILE = "genesis_alloc.csv"
CHECKPOINT = "checkpoint.txt"

def account_range(block_hash, start_key, max_results=BATCH):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "debug_accountRange",
        "params": [block_hash, start_key, max_results, True, False],
    }
    r = requests.post(RPC_URL, json=payload, timeout=None)  # no timeout
    r.raise_for_status()
    return r.json()["result"]

def main():
    # resume if checkpoint exists
    try:
        with open(CHECKPOINT) as f:
            start = f.read().strip()
        print(f"Resuming from checkpoint: {start}")
    except FileNotFoundError:
        start = ""

    total_accounts, total_wei = 0, 0
    t0 = time.time()

    with open(OUTFILE, "a", newline="") as f:
        writer = csv.writer(f)
        if start == "":
            writer.writerow(["address", "balance_wei"])  # header

        while True:
            print(f"→ Requesting from start={start[:8]}…")
            result = account_range(GENESIS_HASH, start, BATCH)

            for addr, acct in (result.get("accounts") or {}).items():
                bal = int(acct["balance"]) if isinstance(acct["balance"], str) and acct["balance"].isdigit() else int(acct["balance"])
                writer.writerow([addr.lower(), str(bal)])
                total_wei += bal
                total_accounts += 1

            f.flush()

            nxt = result.get("next")
            if not nxt or nxt in ("", "0x"):
                print("Reached end of trie")
                break

            # checkpoint
            with open(CHECKPOINT, "w") as c:
                c.write(nxt)

            start = nxt

            if total_accounts % 1000 == 0:
                dt = time.time() - t0
                print(f"… {total_accounts:,} accounts in {dt:.1f}s, wei={total_wei:,}")

    print(f"Done. {total_accounts:,} accounts, total wei={total_wei:,}")
    print(f"Output written to {OUTFILE}, checkpoint saved in {CHECKPOINT}")

if __name__ == "__main__":
    main()
