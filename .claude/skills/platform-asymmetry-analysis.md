# Platform Asymmetry Analysis

Skill for analyzing your own data exports from digital platforms, breaking the informational asymmetry where platforms hold your data but only show you filtered views optimized for their engagement metrics.

## Core Concept

Digital platforms (LinkedIn, Spotify, banks, etc.) collect comprehensive data about your behavior but surface only what drives their business metrics. Legally mandated data exports + AI analysis = asking your own questions against your own data.

## LinkedIn Network Intelligence

The highest-impact application: analyzing LinkedIn data exports to understand your professional network in ways the platform never surfaces.

### Required Data Exports

Request these from LinkedIn Settings > Data Privacy > Get a copy of your data:

- **Connections.csv** — your full connection list with dates, companies, positions
- **Messages.csv** — complete message history with timestamps and content
- **Endorsement_Received_Info.csv** — endorsements others gave you
- **Endorsement_Given_Info.csv** — endorsements you gave others (if available)
- **Recommendations_Received.csv** — recommendations written for you
- **Recommendations_Given.csv** — recommendations you wrote
- **Profile.csv** — your profile metadata
- **Positions.csv** — employment history

### Six Core Analyses

#### 1. Relationship Half-Life Model

Relationships lose strength over time without interaction. Default decay: half strength every 180 days. Adjust based on:

- **Institutional bonds** (shared employer history) — decay more slowly
- **Message frequency** — frequent interaction resets the clock
- **Message depth** — deep substantive messages vs shallow "congratulations" carry different weight

Output: ranked list of connections by current relationship strength, highlighting those decaying toward irrelevance.

#### 2. Reciprocity Debt Ledger

Track social capital balance per relationship:

- Recommendations written vs received (high value)
- Endorsements given vs received (moderate value)
- Message initiation patterns (who reaches out first)

Output: net balance per connection — who you owe, who owes you, where relationships are balanced.

#### 3. Vouch Scores

Predict who would actually advocate for you if asked. Combine:

- Message depth and recency
- Recommendations received from them
- Endorsement patterns
- Shared institutional history
- Interaction frequency

Score 0-100. Above 80 = would write a reference tomorrow. Below 30 = might not remember you clearly.

#### 4. Conversation Resurrection

Scan message history for dormant threads with natural re-engagement hooks:

- Promises to catch up that never happened
- Help requests that went unanswered
- Shared interests mentioned but never followed up on
- Career transitions that warrant congratulations

Output: prioritized list of conversations worth reviving, with suggested re-engagement angles.

#### 5. Network Archetype Classification

Analyze your connection fingerprint to identify your networking style:

- **Thought Leader** — high inbound connections, content engagement
- **Connector** — bridges between disparate groups
- **Specialist** — deep connections within one industry/domain
- **Explorer** — widespread across many organizations

Output: your archetype with a tailored networking strategy.

#### 6. Warm Path Discovery

Given a target company, rank connections by combined relevance and warmth to find a bridge:

- Identify connections at or adjacent to the target company
- Score by relationship warmth (from half-life model)
- Score by relevance (industry overlap, role similarity)
- Map second-degree paths through warm intermediaries

Output: ranked list of people to contact to reach any target company.

## General Platform Analysis Pattern

The same approach works for any platform with data exports:

1. **Export** your data (usually in Settings > Privacy)
2. **Inventory** the files — understand what data you have
3. **Ask questions the platform never lets you ask** — the ones that might reveal you don't need premium, or that recommendations aren't helping
4. **Synthesize across files** — the real insights come from combining data the platform keeps in separate silos

## Usage Notes

- Point the analyzer at your LinkedIn data export directory
- All analysis runs locally on your data — nothing is sent to LinkedIn
- Names can be anonymized in output for sharing
- The analyzer handles messy real-world data (missing fields, inconsistent formats)
- Results are actionable: each analysis produces specific next steps
