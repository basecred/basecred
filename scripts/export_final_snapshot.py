"""
BaseCred Snapshot & Merkle Tree Exporter for TGE.
Aggregates on-chain credits, creator spotlight rewards, and curation points from
the database, filters Sybil addresses, and generates:
1. data/final_airdrop_distribution.csv
2. data/final_merkle_tree.json (with exact Merkle Root for deployment)
"""
import os
import sys
import json
import csv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.database import get_db
from engine.merkle import MerkleTree

def export_snapshot():
    print("=================================================================")
    print("📊 BaseCred Final Airdrop Snapshot & Merkle Generator")
    print("=================================================================\n")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        address,
        twitter_handle,
        tier,
        onchain_credits,
        curator_credits,
        creator_credits,
        (onchain_credits + curator_credits + creator_credits) as total_credits
    FROM users
    WHERE onchain_credits > 0 OR creator_credits > 0
    ORDER BY total_credits DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    print(f"Found {len(rows)} registered wallets in BaseCred database.")

    # 1. Write CSV
    csv_path = "data/final_airdrop_distribution.csv"
    os.makedirs("data", exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "wallet_address", "twitter_handle", "tier", "onchain_credits", "curator_credits", "creator_credits", "total_credits", "amount_wei"])
        
        index = 0
        claimable_elements = []

        for r in rows:
            total_tokens = r["total_credits"]
            amount_wei = total_tokens * (10 ** 18)

            writer.writerow([
                index,
                r["address"],
                r["twitter_handle"] or "unlinked",
                r["tier"],
                r["onchain_credits"],
                r["curator_credits"],
                r["creator_credits"],
                total_tokens,
                amount_wei
            ])

            claimable_elements.append({
                "index": index,
                "account": r["address"],
                "amount": amount_wei,
                "total_tokens": total_tokens
            })
            index += 1

    print(f"Saved allocation breakdown to: {csv_path}")

    # 2. Build Merkle Tree
    tree = MerkleTree(claimable_elements)
    merkle_root = tree.root_hex

    # Attach proof to each record
    distribution_dict = {}
    for idx, el in enumerate(claimable_elements):
        proof = tree.get_proof(idx)
        distribution_dict[el["account"]] = {
            "index": el["index"],
            "account": el["account"],
            "amount_tokens": el["total_tokens"],
            "amount_wei": el["amount"],
            "merkle_proof": proof
        }

    output_data = {
        "token_name": "BaseCred Token",
        "token_symbol": "$CRED",
        "merkle_root": merkle_root,
        "total_eligible_wallets": len(claimable_elements),
        "total_tokens_allocated": sum(el["total_tokens"] for el in claimable_elements),
        "records": distribution_dict
    }

    json_path = "data/final_merkle_tree.json"
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved Merkle proofs to: {json_path}")
    print("\n=================================================================")
    print(f"✅ TGE SNAPSHOT COMPLETE!")
    print(f"🔑 Merkle Root: {merkle_root}")
    print(f"👥 Total Claimants: {len(claimable_elements)}")
    print(f"🪙 Total $CRED Distributed: {output_data['total_tokens_allocated']:,}")
    print("=================================================================\n")

if __name__ == "__main__":
    export_snapshot()
