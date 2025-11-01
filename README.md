# 🌌 Astral Draw – The Cosmic NFT Lottery on Hedera

![Astral Draw Logo](media/astral-draw-logo.png)

**Astral Draw** is a next-generation, blockchain-powered lottery platform built on **Hedera Hashgraph**.  
We reimagine the traditional lottery experience through an **immersive cosmic narrative**, **NFT-gated participation**,  
and **provable fairness** that anyone can verify on-chain.

---

## 🚀 Vision & Mission

The global lottery industry is worth **$300B+**, yet it suffers from:
- Lack of transparency  
- Trust issues with centralized operators  
- Limited accessibility for global players  

**Astral Draw’s Mission:**  
> Build the **most trusted** and **exciting lottery platform** worldwide,  
> enabling $100B+ in lifetime payouts through fair, inclusive, and verifiable technology.

---

## ❌ The Problem vs. ✅ The Astral Draw Solution

| Traditional Pain Points | Astral Draw Solution |
|------------------------|---------------------|
| ❌ **Opaque & Centralized** – Draws are trust-based and off-chain | ✅ **Provably Fair** – Uses Hedera’s VRF-powered PRNG; results are on-chain and verifiable |
| ❌ **Paper Tickets** – Easily lost/damaged, non-transferable | ✅ **NFT Star Keys** – Each ticket is a unique, tradable asset minted via Hedera Token Service (HTS) |
| ❌ **High Operational Costs** – Lower prize pools for players | ✅ **Low Gas Fees & Automation** – Hedera’s efficiency maximizes prize pool payouts |
| ❌ **Limited Access** – Geographic & banking restrictions | ✅ **Global & Inclusive** – Entry via HBAR, USDC, or fiat onramps |

---

## ✨ Core Features

| Feature | Icon | Description |
|--------|------|-------------|
| **Star Key NFTs** | 🛠️ | Each lottery ticket is a unique, verifiable, and tradable NFT on Hedera HTS |
| **Provably Fair Draws** | 🎲 | Powered by Hedera `getPrng()`, guaranteeing cryptographic randomness |
| **Nebula Vault** | 💰 | Automated prize pool smart contract that instantly distributes rewards |
| **On-Chain Transparency** | 🔗 | All ticket sales, draws, and payouts are logged immutably on Hedera |
| **Modern UI/UX** | 📱 | Cosmic-themed, responsive dashboard with real-time draw countdowns |
| **Multi-Payment Support** | 🌐 | Pay with HBAR, USDC, or Fiat via secure onramps |

---

## 🛠 Technology Stack

![Architecture](media/00.png)

| Layer | Technology |
|------|-------------|
| **Ledger** | Hedera Hashgraph |
| **Smart Contracts** | Hedera Smart Contract Service (Solidity/EVM) |
| **NFT Ticketing** | Hedera Token Service (HTS) |
| **Randomness** | Hedera PRNG (`getPrng()`) |
| **Backend** | Python (FastAPI/Django) |
| **Frontend** | htmx + Tailwind CSS + Framer Motion |
| **Database** | PostgreSQL |
| **Payments** | HBAR, USDC, Fiat via onramp |

---

## 🧩 How It Works – The Player’s Journey

### 1️⃣ Forge a Star Key (Buy Ticket)
- Player buys a ticket → Star Key NFT is minted instantly  
- NFT metadata stores ticket numbers + draw ID  
- Payment accepted in HBAR, USDC, or Fiat  

### 2️⃣ Astral Convergence (The Draw)
- When draw ends, backend calls **Hedera PRNG** to generate 6 numbers (0-9 range)  
- Random seed & results submitted to **Hedera Consensus Service (HCS)** for public verification  

### 3️⃣ Select Champions of the Cosmos (Winner Selection)
- Smart contract (`Oracle of Fate`) uses the verified numbers to pick winners  
- Matches are automatically checked against all NFTs in that draw  

### 4️⃣ Distribute the Nebula Vault (Prize Payout)
- Prize pool auto-distributes HBAR to winning wallets  
- 100% on-chain, trustless & auditable  

---

## 📊 Metrics & Goals

| Metric | Target |
|-------|--------|
| **User Adoption** | 1M+ users within first 3 years |
| **Prize Payouts** | $100M+ distributed within first year |
| **Transaction Costs** | < $0.001 per operation (thanks to Hedera) |

![Growth Chart](media/02.png)

---



---

## 🤝 Contributing

We welcome community contributions!  

```bash
# Fork & Clone the repository
git clone https://github.com/DevTitos/AstralDraw.git

# Create a feature branch
git checkout -b feature/AmazingFeature

# Commit and push changes
git commit -m "Add AmazingFeature"
git push origin feature/AmazingFeature

1. Refined Governance Structure: The Astral Council
Your hierarchical structure is solid. Let's give it more definition and clarity.

a) The Celestial Board (Max 10 Members)

Role: Board NFT Holders (IDs 1-10). The "King/Queen" (ID #1) is a first-among-equals, not an absolute ruler.

Responsibilities:

Strategic Vision: Set long-term goals for the Astral Draw universe.

Proposal Curation: Formalize high-quality project and parameter proposals from the community and subordinates for a vote.

Treasury Management Oversight: Multi-signature control over the community treasury wallet for large project payouts (e.g., no single board member can move funds).

Emergency Powers: Ability to pause the lottery or make critical decisions in case of a security breach (subject to a post-event community vote for ratification).

b) The Stellar Assembly (Max 1,000 Members)

Role: Subordinate NFT Holders. The primary voting body.

Responsibilities:

Voting on Proposals: Cast binding votes on all proposals from the Celestial Board (Project, Lottery Frequency, Prize Distribution).

Proposal Initiation: Draft and submit new proposals to the Board for consideration and curation.

Community Advocacy: Represent the interests of the general player base in discussions.

c) The Cosmic Community (Unlimited Players)

Role: All ticket purchasers. The foundation of the ecosystem.

Rights & Abilities:

Idea Forum: Post ideas and suggestions in the "General" topic.

Transparent Viewing: Read-only access to all discussions in the Board and Assembly channels.

Sentiment Signaling: Use non-binding "temperature checks" or polls (like/love/idea) on proposals before they go to a formal vote. This gives the Assembly a clear signal of community will.

Beneficial Ownership: Their portion of the ticket price fuels the community project treasury, making them de facto shareholders.

2. Enhanced Topic & Proposal Workflow
Let's define a clear process for how ideas become funded projects.

a. Project Topic: "The Launchpad"

Step 1: Ideation (Cosmic Community): Anyone can post a project idea in the General forum. The community discusses and refines it using sentiment signaling.

Step 2: Formalization (Stellar Assembly): An Assembly member can sponsor a popular idea and draft a formal proposal (Executive Summary, Budget, Timeline, Expected ROI).

Step 3: Curate & Post (Celestial Board): The Board reviews the formal proposal. If it meets quality standards, they post it to the official "Project Proposal" channel for a vote.

Step 4: Vote (Stellar Assembly): The Assembly votes. A passing vote (e.g., 60% majority) approves the project for funding from the treasury.

b. Lottery Topic: "The Cosmic Clock"

Proposals Here Define:

Draw frequency (e.g., daily, weekly, bi-weekly).

Ticket price adjustments.

Introduction of special, high-stakes "Supernova Draws."

Process: Board proposes -> Assembly votes.

c. Prize Distribution: "The Nebula Split"

A Sample Proposal Structure (to be voted on):

50%: Jackpot for the immediate winner(s).

30%: Community Project Treasury (for funded projects).

10%: Astral Draw Operational Fund (hosting, marketing, development).

10%: NFT Holder Rewards (Distributed pro-rata to Board and Assembly as an incentive for governance participation).

d. General: "The Galactic Forum"

This is the open, unrestricted space for all players. It's for brainstorming, community building, and sharing feedback on all aspects of the game.

3. The "Win-Win" Economic Model: How Everyone Benefits
This is the core of your vision.

If you WIN the Jackpot: You get a life-changing sum of money immediately.

If you DON'T WIN:

You become an Investor: The portion of your ticket price that went to the Community Treasury is now invested into a portfolio of community-vetted projects (e.g., a new DeFi protocol, an NFT game, a real-world asset tokenization).

You earn Dividends: As these projects generate profit (e.g., from fees, revenue), a percentage is returned to the Astral Draw treasury.

Treasury Distribution: The profits from the project portfolio are distributed in two ways:

Buyback & Burn: A portion is used to buy back and burn the Astral Draw token (if you have one), increasing its scarcity and value for all holders.

Community Airdrop: Another portion is airdropped to all players from the last X number of draws, proportional to the number of tickets they bought. This means even losers get a "consolation" income stream over time.

4. Technical Implementation on Hedera
Hedera is a perfect fit for this due to its low, predictable fees and high throughput.

Smart Contracts (HTS/HSC):

Lottery Contract: Handles ticket purchases, random number drawing (using a proven VRF), and prize distribution.

Governance Contract: Manages the voting power of the Stellar Assembly NFTs, tallies votes, and executes passed proposals.

Treasury Contract: A multi-sig wallet controlled by the Celestial Board for secure fund management.

Tokens (HTS):

Board & Assembly NFTs: These represent governance rights. They can be earned through contests, purchased, or awarded to early contributors.

Astral Draw Token (Optional): A fungible token used for ticket purchases, receiving airdrops, and participating in the ecosystem.

Consensus Service (HCS):

Used to create a transparent, immutable, and publicly verifiable log of all governance discussions, proposals, and vote outcomes. This is the "public ledger" for your community debates.
=======
🌌 Astral Draw – The Cosmic NFT Lottery on Hedera

Astral Draw is a next-generation, blockchain-powered lottery platform built on Hedera Hashgraph, reimagining the traditional lottery experience through an immersive cosmic narrative and NFT-gated participation.

Players do not just buy lottery tickets – they forge Star Keys, enter Astral Convergences, and compete for a share of the Nebula Vault (prize pool).
Every draw is transparent, verifiable, and provably fair thanks to Hedera’s Verifiable Random Function (VRF) service.

🚀 Vision

The global lottery industry is worth over $300 billion, but is plagued by trust issues, lack of transparency, and static experiences.
Astral Draw fixes this by:

🌐 Leveraging Hedera’s speed & fairness – near-instant transactions, low gas fees.

🔒 NFT-based ticketing – every ticket is a verifiable digital asset.

🎲 On-chain randomness – powered by Hedera’s PRNG service, ensuring draws are fair.

🎮 Immersive gamification – players feel like they are on a cosmic quest, not just buying tickets.

💸 Global access – payments via crypto & fiat onramps, making it inclusive.

Astral Draw aims to become the most trusted, most exciting lottery platform globally — with a vision to reach $100B+ in lifetime payouts.

✨ Core Features
Feature	Description
🛠 Star Key NFTs	Each ticket is minted as an NFT, unique & tradeable.
🎲 Provably Fair Draws	Draw results are generated using Hedera’s getPrng() randomness service.
💰 Nebula Vault	Prize pool is automatically distributed to winners via smart contracts.
🔗 On-chain Transparency	All ticket sales, draws, and payouts are logged on Hedera and verifiable.
📱 Modern UI/UX	Clean, cosmic-themed dashboard with real-time draw updates.
🌐 Multi-Payment Support	Pay with HBAR, stablecoins, or fiat via onramps for mass adoption.
🛠 Technology Stack
Layer	Technology
DLT	Hedera Hashgraph
Randomness	Hedera PRNG/HCS (Verifiable Randomness)
Smart Contracts	Hedera Smart Contract Service
NFT Ticketing	Hedera Token Service (HTS)
Backend	Python (FastAPI/Django)
Frontend	htmx + Tailwind + Framer Motion + bootstrap
Database	PostgreSQL
Payments	HBAR, Stablecoins (USDC), Fiat (via onramp)
🧩 How It Works

Player Buys Ticket

User purchases a Star Key (NFT) using HBAR, stablecoin, or fiat.

NFT metadata contains ticket number & draw details.

Draw Initiation

When the draw closes, a Hedera PRNG transaction generates 6 random numbers (0–9).

Numbers are stored on-chain for public verification.

Winner Selection

Matching tickets are checked on-chain.

Smart contract automatically triggers payouts to winners’ wallets.

Transparency

Anyone can verify ticket minting, draw randomness, and payouts using Hedera explorer.
