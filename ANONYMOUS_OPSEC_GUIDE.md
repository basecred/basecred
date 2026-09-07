# BaseCred | Anonymous Founder & OpSec Guide (100% Privacy Preserving)

In Web3, being an anonymous ("anon") founder is celebrated—from Satoshi Nakamoto to the founders of Yearn, Curve, and top Base protocols. 

This guide details how to publish, deploy, host, and run BaseCred with **100% anonymity and zero personal identity exposure**.

---

## 🔒 1. Anonymous GitHub Account Setup

### Step-by-Step:
1. **Email:** Create a free encrypted email at [proton.me](https://proton.me) or [tuta.com](https://tuta.com) with a pseudonym (e.g., `basecred-team@proton.me`).
2. **GitHub Account:** Register a fresh GitHub account using this privacy email.
3. **Privacy Settings in GitHub:**
   - Go to **Settings** ➔ **Emails**.
   - Check **"Keep my email addresses private"**.
   - Check **"Block command line pushes that expose my email"**.
4. **Local Git Config (Pre-configured):**
   - The git author for this project is already sanitized to:
     `basecred <basecredproject@proton.me>`.

---

## ⛓️ 2. Anonymous Smart Contract Deployment (Crucial OpSec)

> [!CAUTION]
> **NEVER** fund your deployer wallet directly from a KYC exchange (Coinbase, Binance, Kraken) that is linked to your real-world identity! Block explorers can trace the funding transaction back to your KYC account.

### How to Fund a Fresh Deployer Wallet on Base:
Base gas fees are sub-cent (less than $0.01 per transaction). You only need **~0.005 ETH** (approx. $10 - $15) to deploy all contracts!

#### Route A: Non-KYC Crypto Swaps (Fastest & Easiest)
1. Use an instant non-custodial crypto swap (such as [FixedFloat](https://fixedfloat.com), [ChangeNOW](https://changenow.io), or [SideShift](https://sideshift.ai)).
2. Send crypto (e.g. USDT or LTC) and select **Receive ETH on Base Network** directly to your fresh burner MetaMask address.
3. The funding transaction will originate from the swap pool, completely breaking any link to your identity.

#### Route B: Privacy Protocol Route
1. Deposit ETH on Ethereum L1 into a privacy relayer (e.g., [Railgun](https://railgun.org)).
2. Withdraw to a fresh address and bridge to Base via the official Base Bridge.

### Multi-Sig Ownership:
After deploying `AirdropToken` and `MerkleDistributor`:
- Create an anonymous multi-sig at [app.safe.global](https://app.safe.global) on **Base**.
- Call `transferOwnership(safeAddress)` to hand over governance to the multi-sig.

---

## 🌐 3. Decentralized & Anonymous Frontend Hosting

You have two zero-identity hosting methods:

### Method A: Decentralized Web on IPFS (100% Censorship-Resistant)
- Use **[Fleek.co](https://fleek.xyz)** or **[4EVERLAND](https://4everland.org)**.
- Log in using an anonymous Web3 wallet.
- Select the `public/` directory.
- Your dApp is pinned to IPFS and Filecoin, accessible globally through decentralized IPFS gateways without any centralized servers or personal billing.

### Method B: Vercel / Cloudflare with Burner Email
- Log in to [Vercel](https://vercel.com) using your anonymous GitHub account.
- Import the `basecred` repository.
- No credit card or KYC is required on Vercel's free tier.
- You get an instant HTTPS domain (e.g., `basecred.vercel.app`).

---

## 🏷️ 4. Anonymous Domain Names (Optional)

If you want a custom domain like `basecred.xyz`:
- **Purchase with Crypto:** Buy through privacy-first registrars like **[Njalla](https://njal.la)**, **[Porkbun](https://porkbun.com)**, or **Namecheap** paying with Bitcoin, Monero, or USDT.
- **Web3 Native Domain:** Register **`basecred.base.eth`** on [basenames.base.org](https://basenames.base.org) using your burner wallet.

---

## 🤖 5. Anonymous Twitter & Farcaster Accounts

### Farcaster (Warpcast):
- Download Warpcast or visit [warpcast.com](https://warpcast.com).
- Connect your burner Web3 wallet to claim your Farcaster ID.
- Post in the **/base** channel. Farcaster is natively pseudonymous and Web3-first.

### Twitter (X):
- Use a dedicated browser profile with a VPN enabled.
- Sign up using your ProtonMail email.
- If phone verification is requested, use a disposable SMS service paid with crypto.
- Run `scripts/twitter_bot.py` on a free cloud worker (e.g., Render/Railway free tier) with zero personal credentials.

---

## ✅ Summary Checklist
- [x] Code audited: Zero personal paths or names in the codebase
- [x] Git author: Sanitized to `basecred <basecredproject@proton.me>`
- [x] Secrets: Protected by `.gitignore`
- [ ] Wallet: Funded via non-KYC swap (0.005 ETH on Base)
- [ ] GitHub: Created with burner ProtonMail
- [ ] Vercel/Fleek: Deployed anonymously with 1 click
