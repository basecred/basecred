"""
BaseDrop Custom Wallets Processor.
Allows project owners to process any arbitrary list of addresses, compute their
scores and allocations, and generate the final Merkle Root and proofs.

Usage:
  python3 scripts/process_custom_wallets.py [path_to_addresses.txt]
"""
import sys
import os
import json
from engine.fetcher import fetch_wallet_onchain_state
from engine.eligibility import calculate_eligibility
from engine.merkle import MerkleTree

DEFAULT_INPUT = "data/target_wallets.txt"

def process_wallets(file_path: str = DEFAULT_INPUT):
    if not os.path.exists(file_path):
        # Create a sample list if file does not exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("# Enter one EVM address per line\n")
            f.write("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045\n")
            f.write("0x710bda43e60471b47376c67d142145b4bf37715b\n")
            f.write("0x4b48841d4b322d4b12e2f1059ca7154055c53792\n")
            f.write("0x983110309620d911731ac0932219af06091b6744\n")
            f.write("0x111111125421ca6dc452d289314280a0f8842a65\n")
            f.write("0x000000000000000000000000000000000000dead\n")
        print(f"Created sample target wallets file at: {file_path}")

    addresses = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith("#") and line.startswith("0x") and len(line) == 42:
                if line not in addresses:
                    addresses.append(line)

    print(f"\n=======================================================")
    print(f" Processing {len(addresses)} target wallets for Base Airdrop...")
    print(f"=======================================================\n")

    records = []
    index = 0

    for addr in addresses:
        print(f"[{index+1}/{len(addresses)}] Evaluating on-chain state for {addr}...")
        state = fetch_wallet_onchain_state(addr)
        elig = calculate_eligibility(state)

        amount_tokens = elig["allocated_tokens"]
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

    claimable_elements = [
        {"index": r["index"], "account": r["account"], "amount": r["amount_wei"]}
        for r in records if r["is_eligible"] and r["amount_wei"] > 0
    ]

    tree = MerkleTree(claimable_elements)

    for r in records:
        if r["is_eligible"] and r["amount_wei"] > 0:
            for idx, el in enumerate(claimable_elements):
                if el["account"] == r["account"]:
                    r["merkle_proof"] = tree.get_proof(idx)
                    break
        else:
            r["merkle_proof"] = []

    total_tokens = sum(r["amount_tokens"] for r in records)

    output = {
        "merkle_root": tree.root_hex,
        "token_symbol": "BASED",
        "total_eligible_wallets": len(claimable_elements),
        "total_tokens_allocated": total_tokens,
        "records": {r["account"]: r for r in records}
    }

    output_path = "data/merkle_tree.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=======================================================")
    print(f" ✅ MERKLE TREE GENERATION COMPLETE!")
    print(f"=======================================================")
    print(f" 🔑 Merkle Root: {tree.root_hex}")
    print(f" 👥 Eligible Wallets: {len(claimable_elements)} / {len(addresses)}")
    print(f" 🪙 Total Airdrop Allocation: {total_tokens:,} $BASED")
    print(f" 📁 Saved output to: {output_path}")
    print(f"=======================================================\n")
    print(f"NEXT STEPS FOR DEPLOYMENT:")
    print(f"1. Deploy contracts/AirdropToken.sol on Base.")
    print(f"2. Deploy contracts/MerkleDistributor.sol with:")
    print(f"   token: <Token Address>")
    print(f"   merkleRoot: {tree.root_hex}")
    print(f"3. Transfer {total_tokens:,} tokens to MerkleDistributor.")
    print(f"4. Update PROJECT_CONFIG in public/app.js with your contract addresses.")
    print(f"=======================================================\n")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    process_wallets(target_file)
