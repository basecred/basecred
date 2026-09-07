# BaseCred | Token & Airdrop Launch Guide for Base Network

This step-by-step guide explains how to launch and distribute the real **$CRED** token on **Base Mainnet** (or **Base Sepolia** testnet) using the BaseCred platform.

---

## 🛠️ Step 1: Customize Token Details

Open `contracts/AirdropToken.sol` to verify the name, symbol, and initial supply for BaseCred:

```solidity
string public constant name = "BaseCred Token";
string public constant symbol = "CRED";
uint8 public constant decimals = 18;
```

In the constructor:
- Default supply is `100,000,000 * 10^18` (100 million tokens). You can adjust this as needed.

---

## 🚀 Step 2: Deploy Your Token to Base

You can deploy using **Remix IDE** (easiest & recommended) or **Foundry/Hardhat**:

### Using Remix IDE:
1. Go to [remix.ethereum.org](https://remix.ethereum.org).
2. Create a new file `AirdropToken.sol` and paste the code from `contracts/AirdropToken.sol`.
3. Under **Solidity Compiler**, choose version `0.8.20` or higher and click **Compile**.
4. Under **Deploy & Run Transactions**:
   - Environment: Select **Injected Provider - MetaMask** (ensure your MetaMask is switched to **Base Mainnet** or **Base Sepolia**).
   - Enter `initialSupply` (e.g. `100000000000000000000000000` for 100M tokens).
   - Click **Deploy** and confirm the transaction.
5. 📝 **Copy and save your Deployed Token Address** (e.g. `0x123...`).

---

## 📊 Step 3: Generate Your User Snapshot & Merkle Root

1. Put your target community or eligible wallet addresses into `data/target_wallets.txt` (one address per line):
   ```text
   0x1111111111111111111111111111111111111111
   0x2222222222222222222222222222222222222222
   0x3333333333333333333333333333333333333333
   ```
2. Run the processing script:
   ```bash
   PYTHONPATH=. python3 scripts/process_custom_wallets.py
   ```
3. The script will automatically:
   - Calculate on-chain gas spent, vintage, Base nonces, bridges, and Sybil resistance.
   - Assign tier scores and token rewards.
   - Build the Merkle Tree and output:
     - 🔑 **Merkle Root** (e.g. `0x378f28...`)
     - 🪙 **Total Tokens Allocated** (e.g. `55,000 $BASED`)
     - 📁 File `data/merkle_tree.json` containing all cryptographic proofs.

---

## 🏛️ Step 4: Deploy the MerkleDistributor Contract

1. In Remix (or Foundry), open `contracts/MerkleDistributor.sol`.
2. Compile with `0.8.20`.
3. Under **Deploy**, pass the two constructor parameters:
   - `token_`: The address of your deployed token from **Step 2**.
   - `merkleRoot_`: The exact **Merkle Root** printed in **Step 3**.
4. Click **Deploy** on Base and confirm the transaction.
5. 📝 **Copy and save your MerkleDistributor Contract Address**.

---

## 💰 Step 5: Fund the Distributor Contract

Before users can claim, the distributor contract must hold the tokens:
1. In MetaMask or Remix, call `transfer(distributorAddress, totalTokens)` on your deployed Token contract.
2. Send the exact total airdrop amount (or more) to the `MerkleDistributor` contract address.

---

## ⚙️ Step 6: Configure the Frontend

Open `public/app.js` and update the top configuration section:

```javascript
const PROJECT_CONFIG = {
  tokenName: "Your Token Name",
  tokenSymbol: "MYTOKEN",
  tokenDecimals: 18,
  
  tokenAddress: "PASTE_YOUR_DEPLOYED_TOKEN_ADDRESS_HERE",
  distributorAddress: "PASTE_YOUR_DEPLOYED_DISTRIBUTOR_ADDRESS_HERE",
  
  chainId: 8453,              // 8453 for Base Mainnet (or 84532 for Base Sepolia)
  chainIdHex: "0x2105",
  chainName: "Base",
  rpcUrl: "https://mainnet.base.org",
  explorerUrl: "https://basescan.org"
};
```

---

## 🌐 Step 7: Launch the Website for Users

### Option A: Local / VPS Server (Python API included)
Run on your server:
```bash
python3 server.py
```
Users visit `http://your-server-ip:3000`.

### Option B: Zero-Cost Static Hosting (Vercel / Cloudflare Pages / Netlify / GitHub Pages)
Since the `public/` directory contains standard HTML, CSS, and JS with Ethers.js and client-side Merkle proof support:
1. Upload the contents of `public/` and `data/` to Vercel, Netlify, or Cloudflare Pages.
2. Users worldwide can connect their wallet, check their eligibility, and claim real tokens on Base with 1 click!

---

## 🛡️ Key Security Features
- **Anti-Drain / Non-Reentrant**: Each index can only be claimed once (`claimedBitMap` bitwise check).
- **Cryptographic Merkle Proofs**: No server can be spoofed; only addresses in the root can claim.
- **Emergency Recovery**: The contract owner can withdraw unclaimed tokens after the claim deadline using `emergencyWithdraw(recipient)`.
