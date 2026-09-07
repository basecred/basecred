"""
Generates Airdrop Snapshot & Merkle Tree for seed addresses and provides functions
for dynamic address additions.
"""
import json
import os
from engine.fetcher import fetch_wallet_onchain_state
from engine.eligibility import calculate_eligibility
from engine.merkle import MerkleTree

SEED_ADDRESSES = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    "0x000000000000000000000000000000000000dead",  # Dead address
    "0x3cd751e6b0078be393132286c442345e5dc49699",  # Active Base Trader
    "0x710bda43e60471b47376c67d142145b4bf37715b",  # Aerodrome liquidity provider
    "0x4b48841d4b322d4b12e2f1059ca7154055c53792",  # Coinbase Wallet user
    "0x983110309620d911731ac0932219af06091b6744",  # DeFi Whale
    "0x111111125421ca6dc452d289314280a0f8842a65",  # 1inch Router caller
    "0x000000000022d473030f116ddee9f6b43ac78ba3",  # Permit2 user
    "0x537b01fa83a6b57116cb79d8c76b92fdfbc05374",  # NFT minter
    "0x8888888888888888888888888888888888888888"   # Test User
]

def build_snapshot():
    records = []
    index = 0

    print("Building snapshot for seed addresses...")
    for addr in SEED_ADDRESSES:
        state = fetch_wallet_onchain_state(addr)
        elig = calculate_eligibility(state)
        amount_tokens = elig["allocated_tokens"]
        # Convert to 18 decimals (wei)
        amount_wei = amount_tokens * (10 ** 18)

        records.append({
            "index": index,
            "account": elig["address"],
            "amount_tokens": amount_tokens,
            "amount_wei": amount_wei,
            "tier_name": elig["tier_name"],
            "tier_level": elig["tier_level"],
            "total_score": elig["total_score"],
            "factors": elig["factors"],
            "is_eligible": elig["is_eligible"]
        })
        index += 1

    # Filter only eligible for Merkle Distributor
    claimable_elements = [
        {"index": r["index"], "account": r["account"], "amount": r["amount_wei"]}
        for r in records if r["is_eligible"] and r["amount_wei"] > 0
    ]

    tree = MerkleTree(claimable_elements)

    # Attach proof to each eligible record
    for r in records:
        if r["is_eligible"] and r["amount_wei"] > 0:
            # find index in claimable_elements
            for idx, el in enumerate(claimable_elements):
                if el["account"] == r["account"]:
                    r["merkle_proof"] = tree.get_proof(idx)
                    break
        else:
            r["merkle_proof"] = []

    output_data = {
        "merkle_root": tree.root_hex,
        "token_symbol": "BASED",
        "total_eligible_wallets": len(claimable_elements),
        "total_tokens_allocated": sum(r["amount_tokens"] for r in records),
        "records": {r["account"]: r for r in records}
    }

    os.makedirs("data", exist_ok=True)
    with open("data/merkle_tree.json", "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Snapshot generated! Merkle Root: {tree.root_hex}")
    print(f"Total Eligible Wallets: {len(claimable_elements)}")
    print(f"Total Allocated: {output_data['total_tokens_allocated']:,} $BASED")
    return output_data

if __name__ == "__main__":
    build_snapshot()
