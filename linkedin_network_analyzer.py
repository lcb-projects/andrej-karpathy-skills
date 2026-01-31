#!/usr/bin/env python3
"""
LinkedIn Network Intelligence Analyzer

Analyzes LinkedIn data exports to surface insights the platform never shows you.
Implements six core analyses that break the informational asymmetry between
you and the platform.

Usage:
    python linkedin_network_analyzer.py /path/to/linkedin/export [--target-company "Company Name"]

LinkedIn data export: Settings > Data Privacy > Get a copy of your data
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def find_csv(directory, candidates):
    """Find the first matching CSV file from a list of candidate names."""
    for name in candidates:
        path = Path(directory) / name
        if path.exists():
            return path
    return None


def load_csv(filepath):
    """Load a CSV file, handling common LinkedIn export quirks."""
    if filepath is None or not Path(filepath).exists():
        return []
    rows = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k.strip(): v.strip() if v else "" for k, v in row.items()}
            rows.append(cleaned)
    return rows


def parse_date(date_str):
    """Parse dates in common LinkedIn export formats."""
    if not date_str:
        return None
    for fmt in ("%d %b %Y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def days_ago(dt):
    """Return the number of days between a datetime and now."""
    if dt is None:
        return 9999
    return (datetime.now() - dt).days


# ---------------------------------------------------------------------------
# Data loaders for each LinkedIn export file
# ---------------------------------------------------------------------------

def load_connections(directory):
    """Load Connections.csv."""
    path = find_csv(directory, ["Connections.csv", "connections.csv"])
    rows = load_csv(path)
    connections = []
    for r in rows:
        name = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
        if not name or name == " ":
            continue
        connections.append({
            "name": name,
            "company": r.get("Company", ""),
            "position": r.get("Position", ""),
            "connected_on": parse_date(r.get("Connected On", "")),
            "email": r.get("Email Address", ""),
        })
    return connections


def load_messages(directory):
    """Load Messages.csv and group by conversation."""
    path = find_csv(directory, ["Messages.csv", "messages.csv"])
    rows = load_csv(path)
    conversations = defaultdict(list)
    for r in rows:
        conv_id = r.get("CONVERSATION ID", r.get("Conversation ID", ""))
        sender = r.get("FROM", r.get("From", ""))
        date = parse_date(r.get("DATE", r.get("Date", "")))
        content = r.get("CONTENT", r.get("Content", ""))
        if conv_id:
            conversations[conv_id].append({
                "from": sender,
                "date": date,
                "content": content,
            })
    # Sort each conversation by date
    for conv_id in conversations:
        conversations[conv_id].sort(key=lambda m: m["date"] or datetime.min)
    return conversations


def load_endorsements_received(directory):
    """Load endorsements received."""
    path = find_csv(directory, [
        "Endorsement_Received_Info.csv",
        "endorsement_received_info.csv",
        "Endorsements_Received.csv",
    ])
    rows = load_csv(path)
    endorsements = defaultdict(int)
    for r in rows:
        name = r.get("Endorser First Name", r.get("First Name", ""))
        last = r.get("Endorser Last Name", r.get("Last Name", ""))
        full = f"{name} {last}".strip()
        if full:
            endorsements[full] += 1
    return endorsements


def load_endorsements_given(directory):
    """Load endorsements given (if available)."""
    path = find_csv(directory, [
        "Endorsement_Given_Info.csv",
        "endorsement_given_info.csv",
        "Endorsements_Given.csv",
    ])
    rows = load_csv(path)
    endorsements = defaultdict(int)
    for r in rows:
        name = r.get("First Name", r.get("Endorsee First Name", ""))
        last = r.get("Last Name", r.get("Endorsee Last Name", ""))
        full = f"{name} {last}".strip()
        if full:
            endorsements[full] += 1
    return endorsements


def load_recommendations_received(directory):
    """Load recommendations received."""
    path = find_csv(directory, [
        "Recommendations_Received.csv",
        "recommendations_received.csv",
    ])
    rows = load_csv(path)
    recs = {}
    for r in rows:
        name = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
        if name:
            recs[name] = r.get("Recommendation Text", r.get("Text", ""))
    return recs


def load_recommendations_given(directory):
    """Load recommendations given."""
    path = find_csv(directory, [
        "Recommendations_Given.csv",
        "recommendations_given.csv",
    ])
    rows = load_csv(path)
    recs = {}
    for r in rows:
        name = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
        if name:
            recs[name] = r.get("Recommendation Text", r.get("Text", ""))
    return recs


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def message_depth_score(content):
    """
    Score a message's depth: 0 (shallow) to 1.0 (substantive).

    Shallow: short congratulatory messages, single emojis, "thanks".
    Deep: longer messages with questions, substance, specifics.
    """
    if not content:
        return 0.0
    words = content.split()
    word_count = len(words)
    if word_count <= 3:
        return 0.1
    shallow_patterns = [
        r"^congrat", r"^thanks?$", r"^happy birthday",
        r"^welcome$", r"^nice$", r"^great$", r"^good luck",
    ]
    lower = content.lower().strip()
    for pat in shallow_patterns:
        if re.match(pat, lower):
            return 0.15
    # Longer messages with questions score higher
    has_question = "?" in content
    score = min(1.0, word_count / 100)
    if has_question:
        score = min(1.0, score + 0.2)
    return round(score, 2)


def build_message_profile(conversations, your_name_hint=""):
    """
    Build a per-contact message profile from conversation data.

    Returns dict: name -> {
        message_count, last_message_date, avg_depth,
        they_initiated, you_initiated, total_words, messages
    }
    """
    profiles = defaultdict(lambda: {
        "message_count": 0,
        "last_message_date": None,
        "depths": [],
        "they_initiated": 0,
        "you_initiated": 0,
        "total_words": 0,
        "messages": [],
    })
    your_name_lower = your_name_hint.lower()

    for conv_id, msgs in conversations.items():
        # Identify the other party (not you)
        participants = set()
        for m in msgs:
            if m["from"]:
                participants.add(m["from"])
        other = None
        for p in participants:
            if your_name_lower and your_name_lower in p.lower():
                continue
            other = p
        if not other:
            # Fallback: use the first participant that isn't likely "you"
            if len(participants) >= 2:
                other = sorted(participants)[0]
            else:
                continue

        for i, m in enumerate(msgs):
            prof = profiles[other]
            prof["message_count"] += 1
            if m["date"] and (prof["last_message_date"] is None or m["date"] > prof["last_message_date"]):
                prof["last_message_date"] = m["date"]
            depth = message_depth_score(m.get("content", ""))
            prof["depths"].append(depth)
            prof["total_words"] += len((m.get("content", "") or "").split())
            prof["messages"].append(m)
            # Track initiation (first message in conversation)
            if i == 0:
                is_you = your_name_lower and your_name_lower in (m["from"] or "").lower()
                if is_you:
                    prof["you_initiated"] += 1
                else:
                    prof["they_initiated"] += 1

    # Compute averages
    result = {}
    for name, prof in profiles.items():
        avg_depth = sum(prof["depths"]) / len(prof["depths"]) if prof["depths"] else 0
        result[name] = {
            "message_count": prof["message_count"],
            "last_message_date": prof["last_message_date"],
            "avg_depth": round(avg_depth, 2),
            "they_initiated": prof["they_initiated"],
            "you_initiated": prof["you_initiated"],
            "total_words": prof["total_words"],
            "messages": prof["messages"],
        }
    return result


# ---------------------------------------------------------------------------
# The six core analyses
# ---------------------------------------------------------------------------

def analysis_relationship_halflife(connections, msg_profiles, half_life_days=180):
    """
    Analysis 1: Relationship Half-Life Model

    Relationships lose half their strength every `half_life_days` without
    interaction. Interaction resets the clock. Deep messages and institutional
    bonds slow decay.
    """
    results = []
    decay_constant = math.log(2) / half_life_days

    for conn in connections:
        name = conn["name"]
        profile = msg_profiles.get(name, {})
        last_msg = profile.get("last_message_date")
        avg_depth = profile.get("avg_depth", 0)
        msg_count = profile.get("message_count", 0)

        # Base: time since last interaction (message or connection date)
        last_interaction = last_msg or conn["connected_on"]
        days_since = days_ago(last_interaction)

        # Depth modifier: deep conversations decay 30% slower
        depth_modifier = 1.0 - (avg_depth * 0.3)
        effective_decay = decay_constant * depth_modifier

        # Frequency modifier: more messages = slower decay (up to 20%)
        freq_modifier = max(0.8, 1.0 - (min(msg_count, 50) / 250))
        effective_decay *= freq_modifier

        # Calculate current strength (0 to 1)
        strength = math.exp(-effective_decay * days_since)

        # Effective half-life for display
        effective_half_life = math.log(2) / effective_decay if effective_decay > 0 else 9999

        results.append({
            "name": name,
            "company": conn["company"],
            "position": conn["position"],
            "strength": round(strength, 3),
            "days_since_interaction": days_since,
            "effective_half_life_days": round(effective_half_life),
            "message_count": msg_count,
            "avg_depth": avg_depth,
        })

    results.sort(key=lambda r: r["strength"], reverse=True)
    return results


def analysis_reciprocity_ledger(connections, endorsements_received, endorsements_given,
                                recs_received, recs_given, msg_profiles):
    """
    Analysis 2: Reciprocity Debt Ledger

    Track social capital flows per relationship.
    Recommendations = 5 points, Endorsements = 2 points, Message initiation = 1 point.
    """
    REC_WEIGHT = 5
    ENDORSE_WEIGHT = 2
    INITIATE_WEIGHT = 1

    ledger = []
    all_names = set(c["name"] for c in connections)

    for name in all_names:
        given_score = 0
        received_score = 0

        # Recommendations
        if name in recs_given:
            given_score += REC_WEIGHT
        if name in recs_received:
            received_score += REC_WEIGHT

        # Endorsements
        given_score += endorsements_given.get(name, 0) * ENDORSE_WEIGHT
        received_score += endorsements_received.get(name, 0) * ENDORSE_WEIGHT

        # Message initiation
        profile = msg_profiles.get(name, {})
        given_score += profile.get("you_initiated", 0) * INITIATE_WEIGHT
        received_score += profile.get("they_initiated", 0) * INITIATE_WEIGHT

        net = received_score - given_score
        if given_score == 0 and received_score == 0:
            continue

        ledger.append({
            "name": name,
            "you_invested": given_score,
            "they_invested": received_score,
            "net_balance": net,
            "status": "they owe you" if net < 0 else "you owe them" if net > 0 else "balanced",
        })

    ledger.sort(key=lambda r: r["net_balance"])
    return ledger


def analysis_vouch_scores(connections, msg_profiles, endorsements_received,
                          recs_received):
    """
    Analysis 3: Vouch Scores

    Predict who would advocate for you. Score 0-100 combining:
    - Message depth and recency (40%)
    - Recommendations received (25%)
    - Endorsement count (15%)
    - Interaction frequency (20%)
    """
    results = []
    for conn in connections:
        name = conn["name"]
        profile = msg_profiles.get(name, {})
        score = 0.0

        # Message depth & recency (40 points max)
        avg_depth = profile.get("avg_depth", 0)
        last_msg = profile.get("last_message_date")
        recency = max(0, 1.0 - days_ago(last_msg) / 730) if last_msg else 0
        score += (avg_depth * 20) + (recency * 20)

        # Recommendation received (25 points)
        if name in recs_received:
            score += 25

        # Endorsements (15 points max, diminishing)
        endorse_count = endorsements_received.get(name, 0)
        score += min(15, endorse_count * 5)

        # Interaction frequency (20 points max)
        msg_count = profile.get("message_count", 0)
        score += min(20, msg_count * 2)

        score = min(100, round(score))
        results.append({
            "name": name,
            "company": conn["company"],
            "vouch_score": score,
            "has_recommendation": name in recs_received,
            "endorsement_count": endorsements_received.get(name, 0),
            "message_count": profile.get("message_count", 0),
            "avg_depth": avg_depth,
        })

    results.sort(key=lambda r: r["vouch_score"], reverse=True)
    return results


def analysis_conversation_resurrection(msg_profiles, min_dormant_days=60):
    """
    Analysis 4: Conversation Resurrection

    Find dormant threads with natural re-engagement hooks:
    - Promises to catch up
    - Unanswered help requests
    - Shared interests mentioned
    """
    resurrection_patterns = [
        (r"let'?s (catch up|grab coffee|connect|chat|meet)", "catch-up promise"),
        (r"we should (talk|meet|connect|catch up)", "catch-up promise"),
        (r"would love to (hear|learn|chat|connect|catch up)", "interest expressed"),
        (r"can you help|could you|would you mind|any advice", "help request"),
        (r"i('?d| would) love your (input|thoughts|advice|feedback)", "advice request"),
        (r"congratulations|congrats|amazing|exciting", "celebration"),
        (r"new (role|position|job|company)", "career transition"),
        (r"check.?(out|in)|follow.?up", "follow-up intent"),
    ]

    results = []
    for name, profile in msg_profiles.items():
        last_date = profile.get("last_message_date")
        if not last_date:
            continue
        dormant_days = days_ago(last_date)
        if dormant_days < min_dormant_days:
            continue

        # Scan last few messages for hooks
        recent_msgs = profile["messages"][-5:] if profile.get("messages") else []
        hooks = []
        for msg in recent_msgs:
            content = (msg.get("content") or "").lower()
            for pattern, label in resurrection_patterns:
                if re.search(pattern, content):
                    hooks.append({
                        "type": label,
                        "snippet": (msg.get("content") or "")[:120],
                        "date": msg["date"].strftime("%Y-%m-%d") if msg["date"] else "unknown",
                    })
                    break

        if hooks:
            results.append({
                "name": name,
                "dormant_days": dormant_days,
                "hooks": hooks,
                "message_count": profile["message_count"],
                "avg_depth": profile["avg_depth"],
            })

    results.sort(key=lambda r: len(r["hooks"]), reverse=True)
    return results


def analysis_network_archetype(connections, msg_profiles):
    """
    Analysis 5: Network Archetype Classification

    Analyze connection fingerprint to determine networking style:
    - Thought Leader: high inbound, broad reach
    - Connector: bridges many different companies/industries
    - Specialist: deep in one domain
    - Explorer: spread across many organizations
    """
    total = len(connections)
    if total == 0:
        return {"archetype": "Unknown", "scores": {}, "strategy": ""}

    # Company diversity
    companies = [c["company"] for c in connections if c["company"]]
    unique_companies = len(set(companies))
    company_diversity = unique_companies / max(1, len(companies))

    # Top company concentration
    company_counts = defaultdict(int)
    for c in companies:
        company_counts[c] += 1
    top_company_pct = max(company_counts.values()) / max(1, total) if company_counts else 0

    # Message engagement rate
    messaged = sum(1 for c in connections if c["name"] in msg_profiles)
    engagement_rate = messaged / max(1, total)

    # Inbound vs outbound initiation
    total_they_init = sum(p.get("they_initiated", 0) for p in msg_profiles.values())
    total_you_init = sum(p.get("you_initiated", 0) for p in msg_profiles.values())
    inbound_ratio = total_they_init / max(1, total_they_init + total_you_init)

    # Depth of engagement
    avg_depths = [p["avg_depth"] for p in msg_profiles.values() if p["avg_depth"] > 0]
    overall_depth = sum(avg_depths) / len(avg_depths) if avg_depths else 0

    # Score each archetype
    scores = {
        "Thought Leader": round((inbound_ratio * 40) + (engagement_rate * 30) + (overall_depth * 30), 1),
        "Connector": round((company_diversity * 50) + (engagement_rate * 30) + ((1 - top_company_pct) * 20), 1),
        "Specialist": round((top_company_pct * 40) + ((1 - company_diversity) * 30) + (overall_depth * 30), 1),
        "Explorer": round((company_diversity * 40) + (unique_companies / max(1, total) * 30) + ((1 - overall_depth) * 30), 1),
    }

    archetype = max(scores, key=scores.get)

    strategies = {
        "Thought Leader": (
            "Your network comes to you. Leverage this by sharing insights publicly, "
            "responding thoughtfully to inbound messages, and being selective about "
            "outreach. Focus on deepening your highest-value relationships rather than "
            "expanding breadth."
        ),
        "Connector": (
            "Your strength is bridging different worlds. Actively introduce people "
            "across your diverse network. Your value increases when you facilitate "
            "connections between people who wouldn't otherwise meet. Maintain breadth "
            "but invest in key bridge relationships."
        ),
        "Specialist": (
            "You have deep roots in your domain. Double down on depth — become the "
            "go-to person in your area. Your referrals carry weight because of domain "
            "credibility. Consider expanding to adjacent domains to avoid single-point "
            "network risk."
        ),
        "Explorer": (
            "You cast a wide net across many organizations. Convert exploration into "
            "depth by identifying 3-5 key clusters to invest in. Your broad awareness "
            "is an asset for opportunity spotting, but depth is what converts "
            "opportunities into outcomes."
        ),
    }

    return {
        "archetype": archetype,
        "scores": scores,
        "strategy": strategies[archetype],
        "stats": {
            "total_connections": total,
            "unique_companies": unique_companies,
            "company_diversity": round(company_diversity, 2),
            "top_company_concentration": round(top_company_pct, 2),
            "engagement_rate": round(engagement_rate, 2),
            "inbound_ratio": round(inbound_ratio, 2),
            "avg_conversation_depth": round(overall_depth, 2),
        },
    }


def analysis_warm_path(connections, msg_profiles, halflife_results, target_company):
    """
    Analysis 6: Warm Path Discovery

    Find the best path to a target company by combining relationship warmth
    with relevance to the target.
    """
    if not target_company:
        return []

    target_lower = target_company.lower()

    # Build company -> connections map
    company_map = defaultdict(list)
    for conn in connections:
        if conn["company"]:
            company_map[conn["company"].lower()].append(conn)

    # Build a strength lookup from halflife results
    strength_lookup = {r["name"]: r["strength"] for r in halflife_results}

    results = []
    for conn in connections:
        name = conn["name"]
        company = (conn["company"] or "").lower()
        warmth = strength_lookup.get(name, 0)

        # Direct match: connection is at the target company
        if target_lower in company:
            results.append({
                "name": name,
                "company": conn["company"],
                "position": conn["position"],
                "path_type": "direct",
                "warmth": warmth,
                "relevance": 1.0,
                "combined_score": round(warmth * 0.5 + 1.0 * 0.5, 3),
                "message_count": msg_profiles.get(name, {}).get("message_count", 0),
            })
            continue

        # Industry adjacency: rough heuristic based on company name similarity
        # and shared words between target and connection's company
        if company:
            target_words = set(target_lower.split())
            company_words = set(company.split())
            common = target_words & company_words - {"inc", "ltd", "llc", "the", "and", "of", "co"}
            if common:
                relevance = len(common) / max(len(target_words), 1)
                results.append({
                    "name": name,
                    "company": conn["company"],
                    "position": conn["position"],
                    "path_type": "adjacent",
                    "warmth": warmth,
                    "relevance": round(relevance, 2),
                    "combined_score": round(warmth * 0.5 + relevance * 0.5, 3),
                    "message_count": msg_profiles.get(name, {}).get("message_count", 0),
                })

    results.sort(key=lambda r: r["combined_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_section(title, description):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"  {description}")
    print(f"{'=' * 70}")


def print_report(halflife, reciprocity, vouch, resurrection, archetype, warm_path,
                 target_company, top_n=15):
    """Print the full Network Intelligence Dashboard."""
    print("\n" + "=" * 70)
    print("  LINKEDIN NETWORK INTELLIGENCE DASHBOARD")
    print("  Breaking the platform asymmetry — your data, your questions")
    print("=" * 70)

    # 1. Relationship Half-Life
    format_section(
        "1. RELATIONSHIP HALF-LIFE",
        "Connections ranked by current relationship strength"
    )
    print(f"\n  {'Name':<30} {'Company':<25} {'Strength':>8} {'Days':>6} {'Half-Life':>10} {'Msgs':>5}")
    print(f"  {'-'*30} {'-'*25} {'-'*8} {'-'*6} {'-'*10} {'-'*5}")
    for r in halflife[:top_n]:
        strength_bar = "#" * int(r["strength"] * 10)
        print(f"  {r['name']:<30} {r['company'][:25]:<25} {r['strength']:>7.1%} {r['days_since_interaction']:>5}d "
              f"{r['effective_half_life_days']:>8}d {r['message_count']:>5}")
    if len(halflife) > top_n:
        print(f"\n  ... and {len(halflife) - top_n} more connections")

    decaying = [r for r in halflife if 0.1 < r["strength"] < 0.4 and r["message_count"] > 2]
    if decaying:
        print(f"\n  ** {len(decaying)} relationships are cooling but salvageable (10-40% strength)")

    # 2. Reciprocity Ledger
    format_section(
        "2. RECIPROCITY DEBT LEDGER",
        "Social capital balance per relationship"
    )
    # Show who owes you the most
    they_owe = [r for r in reciprocity if r["net_balance"] < 0][:top_n // 2]
    you_owe = [r for r in reciprocity if r["net_balance"] > 0][-top_n // 2:]

    if they_owe:
        print(f"\n  People who owe you (you invested more):")
        print(f"  {'Name':<30} {'You Gave':>10} {'They Gave':>10} {'Balance':>10}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
        for r in they_owe:
            print(f"  {r['name']:<30} {r['you_invested']:>10} {r['they_invested']:>10} {r['net_balance']:>+10}")

    if you_owe:
        print(f"\n  People you owe (they invested more):")
        print(f"  {'Name':<30} {'You Gave':>10} {'They Gave':>10} {'Balance':>10}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
        for r in you_owe:
            print(f"  {r['name']:<30} {r['you_invested']:>10} {r['they_invested']:>10} {r['net_balance']:>+10}")

    # 3. Vouch Scores
    format_section(
        "3. VOUCH SCORES",
        "Who would actually advocate for you if asked (0-100)"
    )
    print(f"\n  {'Name':<30} {'Company':<20} {'Score':>6} {'Rec?':>5} {'Endorse':>8} {'Msgs':>5} {'Depth':>6}")
    print(f"  {'-'*30} {'-'*20} {'-'*6} {'-'*5} {'-'*8} {'-'*5} {'-'*6}")
    for r in vouch[:top_n]:
        rec = "Yes" if r["has_recommendation"] else ""
        print(f"  {r['name']:<30} {r['company'][:20]:<20} {r['vouch_score']:>5} "
              f"{rec:>5} {r['endorsement_count']:>8} {r['message_count']:>5} {r['avg_depth']:>5.2f}")

    strong_vouchers = sum(1 for r in vouch if r["vouch_score"] >= 80)
    weak_vouchers = sum(1 for r in vouch if r["vouch_score"] < 30)
    print(f"\n  {strong_vouchers} strong advocates (80+) | {weak_vouchers} unlikely to vouch (<30)")

    # 4. Conversation Resurrection
    format_section(
        "4. CONVERSATION RESURRECTION",
        "Dormant threads with natural re-engagement hooks"
    )
    if resurrection:
        for r in resurrection[:top_n]:
            print(f"\n  {r['name']} — dormant {r['dormant_days']} days ({r['message_count']} total messages)")
            for hook in r["hooks"]:
                print(f"    [{hook['type']}] {hook['date']}: \"{hook['snippet']}\"")
    else:
        print("\n  No dormant conversations with clear re-engagement hooks found.")

    # 5. Network Archetype
    format_section(
        "5. NETWORK ARCHETYPE",
        "Your networking style and recommended strategy"
    )
    print(f"\n  Your archetype: {archetype['archetype']}")
    print(f"\n  Archetype scores:")
    for arch, score in sorted(archetype["scores"].items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(score)
        marker = " <-- YOU" if arch == archetype["archetype"] else ""
        print(f"    {arch:<16} {score:>5.1f}  {bar}{marker}")
    print(f"\n  Network stats:")
    for key, val in archetype["stats"].items():
        label = key.replace("_", " ").title()
        print(f"    {label:<30} {val}")
    print(f"\n  Strategy: {archetype['strategy']}")

    # 6. Warm Path
    if target_company:
        format_section(
            f"6. WARM PATH TO: {target_company.upper()}",
            "Connections ranked by combined warmth and relevance"
        )
        if warm_path:
            print(f"\n  {'Name':<28} {'Company':<22} {'Type':<9} {'Warmth':>7} {'Relev':>6} {'Score':>6} {'Msgs':>5}")
            print(f"  {'-'*28} {'-'*22} {'-'*9} {'-'*7} {'-'*6} {'-'*6} {'-'*5}")
            for r in warm_path[:top_n]:
                print(f"  {r['name']:<28} {r['company'][:22]:<22} {r['path_type']:<9} "
                      f"{r['warmth']:>6.1%} {r['relevance']:>5.0%} {r['combined_score']:>5.1%} {r['message_count']:>5}")

            direct = [r for r in warm_path if r["path_type"] == "direct"]
            if direct:
                print(f"\n  {len(direct)} direct connection(s) at {target_company}")
                warmest = max(direct, key=lambda r: r["warmth"])
                print(f"  Warmest direct path: {warmest['name']} ({warmest['warmth']:.0%} strength)")
        else:
            print(f"\n  No connections found with path to {target_company}.")
            print("  Try a broader company name or check spelling.")

    # Summary
    print(f"\n{'=' * 70}")
    print("  ANALYSIS SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n  Total connections analyzed: {len(halflife)}")
    print(f"  Connections with messages:  {sum(1 for r in halflife if r['message_count'] > 0)}")
    print(f"  Strong relationships (>50%): {sum(1 for r in halflife if r['strength'] > 0.5)}")
    print(f"  Decaying relationships:      {sum(1 for r in halflife if 0.1 < r['strength'] < 0.4)}")
    print(f"  Strong advocates (vouch 80+): {strong_vouchers}")
    print(f"  Resurrection candidates:      {len(resurrection)}")
    print(f"  Network archetype:            {archetype['archetype']}")
    if target_company and warm_path:
        print(f"  Paths to {target_company}: {len(warm_path)}")
    print()


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def export_json(halflife, reciprocity, vouch, resurrection, archetype, warm_path,
                target_company, output_path):
    """Export all analyses to a JSON file."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "relationship_halflife": halflife[:50],
        "reciprocity_ledger": reciprocity,
        "vouch_scores": vouch[:50],
        "conversation_resurrection": resurrection,
        "network_archetype": archetype,
    }
    if target_company:
        data["warm_path"] = {"target": target_company, "paths": warm_path[:30]}

    # Convert datetimes for JSON serialization
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=default_serializer)
    print(f"\n  Full results exported to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Network Intelligence Analyzer — break the platform asymmetry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python linkedin_network_analyzer.py ~/Downloads/linkedin-export/
    python linkedin_network_analyzer.py ./data --target-company "Google"
    python linkedin_network_analyzer.py ./data --your-name "Jane Doe" --json report.json
        """,
    )
    parser.add_argument("directory", help="Path to LinkedIn data export directory")
    parser.add_argument("--target-company", help="Target company for warm path analysis")
    parser.add_argument("--your-name", default="", help="Your name (for message direction analysis)")
    parser.add_argument("--half-life", type=int, default=180, help="Base half-life in days (default: 180)")
    parser.add_argument("--dormant-days", type=int, default=60, help="Min dormant days for resurrection (default: 60)")
    parser.add_argument("--json", metavar="FILE", help="Export results to JSON file")
    parser.add_argument("--top", type=int, default=15, help="Number of results to show per section (default: 15)")
    args = parser.parse_args()

    directory = args.directory
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Load data
    print("Loading LinkedIn data export...")
    connections = load_connections(directory)
    conversations = load_messages(directory)
    endorsements_received = load_endorsements_received(directory)
    endorsements_given = load_endorsements_given(directory)
    recs_received = load_recommendations_received(directory)
    recs_given = load_recommendations_given(directory)

    if not connections:
        print("Error: No connections found. Check that Connections.csv exists in the export directory.",
              file=sys.stderr)
        sys.exit(1)

    print(f"  Loaded {len(connections)} connections")
    print(f"  Loaded {len(conversations)} conversations")
    print(f"  Loaded {sum(endorsements_received.values())} endorsements received")
    print(f"  Loaded {sum(endorsements_given.values())} endorsements given")
    print(f"  Loaded {len(recs_received)} recommendations received")
    print(f"  Loaded {len(recs_given)} recommendations given")

    # Build message profiles
    print("Building message profiles...")
    msg_profiles = build_message_profile(conversations, args.your_name)
    print(f"  Profiled {len(msg_profiles)} contacts from messages")

    # Run analyses
    print("Running analyses...")

    halflife = analysis_relationship_halflife(connections, msg_profiles, args.half_life)
    reciprocity = analysis_reciprocity_ledger(
        connections, endorsements_received, endorsements_given,
        recs_received, recs_given, msg_profiles
    )
    vouch = analysis_vouch_scores(connections, msg_profiles, endorsements_received, recs_received)
    resurrection = analysis_conversation_resurrection(msg_profiles, args.dormant_days)
    archetype = analysis_network_archetype(connections, msg_profiles)
    warm_path = analysis_warm_path(connections, msg_profiles, halflife, args.target_company)

    # Output
    print_report(halflife, reciprocity, vouch, resurrection, archetype, warm_path,
                 args.target_company, args.top)

    if args.json:
        export_json(halflife, reciprocity, vouch, resurrection, archetype, warm_path,
                    args.target_company, args.json)


if __name__ == "__main__":
    main()
