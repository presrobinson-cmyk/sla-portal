"""
Shared data loader for SLA Portal — Hybrid MrP + Raw fallback.

Priority: MrP-adjusted numbers from mrp_question_summary when available.
Fallback: Runtime scoring of l2_responses for surveys not yet in MrP.

All portal pages should import from here instead of querying Supabase directly.
"""

import streamlit as st
import requests
from collections import defaultdict

from theme import (
    get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE,
)

try:
    from content_scoring import SKIPPED_QIDS, get_construct, score_content, FAVORABLE_DIRECTION
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════
# PAGINATION HELPER
# ══════════════════════════════════════════════════════════════════

def _paginate(url_base, headers, limit=1000, max_rows=200000):
    """Paginate a Supabase REST query."""
    all_rows = []
    offset = 0
    while offset < max_rows:
        sep = "&" if "?" in url_base else "?"
        url = f"{url_base}{sep}offset={offset}&limit={limit}"
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        rows = resp.json()
        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit
    return all_rows


# ══════════════════════════════════════════════════════════════════
# MrP QUESTION SUMMARY LOADER
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading MrP estimates...")
def load_mrp_question_summary(survey_ids=None):
    """
    Load mrp_question_summary rows from Supabase.
    Returns dict keyed by (survey_id, question_id) with all fields.
    Also returns set of survey_ids that have MrP data.
    """
    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    rows = _paginate(
        f"{url}/rest/v1/mrp_question_summary"
        f"?select=survey_id,question_id,question_text,response_label,"
        f"raw_pct,mrp_pct,correction,n_respondents,state,domain",
        headers,
    )

    mrp_data = {}
    mrp_surveys = set()
    for r in rows:
        sid = r.get("survey_id")
        qid = r.get("question_id")
        if sid and qid:
            mrp_data[(sid, qid)] = r
            mrp_surveys.add(sid)

    return mrp_data, mrp_surveys


# ══════════════════════════════════════════════════════════════════
# RAW L2 FALLBACK LOADER (for surveys not yet in MrP)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading raw survey data (fallback)...")
def load_raw_l2_for_surveys(survey_ids):
    """
    Load and score raw l2_responses for the given survey_ids.
    Returns dict keyed by question_id with support stats.
    Used only for surveys NOT in mrp_question_summary.
    """
    if not survey_ids or not SCORING_AVAILABLE:
        return {}

    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    all_l2 = []
    for sid in survey_ids:
        rows = _paginate(
            f"{url}/rest/v1/l2_responses"
            f"?select=respondent_id,survey_id,question_id,question_text,response"
            f"&survey_id=eq.{sid}",
            headers,
        )
        all_l2.extend(rows)

    # Score and tally
    q_stats = defaultdict(lambda: {"f": 0, "n": 0, "construct": None, "text": "", "survey_id": None})
    for r in all_l2:
        qid = r.get("question_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        fav, intensity, has_int = score_content(qid, r["response"], r.get("survey_id"))
        if fav is None:
            continue
        is_fav = 1 if fav == 1 else 0
        q_stats[qid]["f"] += is_fav
        q_stats[qid]["n"] += 1
        q_stats[qid]["construct"] = construct
        if r.get("question_text"):
            q_stats[qid]["text"] = r["question_text"]
        q_stats[qid]["survey_id"] = r.get("survey_id")

    result = {}
    for qid, s in q_stats.items():
        if s["n"] < 20:
            continue
        result[qid] = {
            "raw_pct": s["f"] / s["n"] * 100,
            "mrp_pct": None,  # No MrP available
            "n_respondents": s["n"],
            "question_text": s["text"],
            "construct": s["construct"],
            "survey_id": s["survey_id"],
            "source": "raw",
        }
    return result


# ══════════════════════════════════════════════════════════════════
# PARTY-SPLIT LOADER (for scatter plot skeptic axis)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading party breakdowns...")
def load_party_splits(survey_ids=None):
    """
    Load Republican/Democrat split from l1+l2 for given surveys.
    Returns dict keyed by question_id with r_pct, d_pct.
    Party splits always come from raw data (MrP cells are race|age|edu|sex, not party).
    """
    if survey_ids is None:
        survey_ids = CJ_SURVEYS
    if not SCORING_AVAILABLE:
        return {}

    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    # Pull L1 party
    all_l1 = []
    for sid in survey_ids:
        rows = _paginate(
            f"{url}/rest/v1/l1_respondents"
            f"?select=respondent_id,party_id"
            f"&survey_id=eq.{sid}",
            headers,
        )
        all_l1.extend(rows)
    party_lookup = {d["respondent_id"]: d.get("party_id", "") for d in all_l1}

    # Pull L2 and score by party
    all_l2 = []
    for sid in survey_ids:
        rows = _paginate(
            f"{url}/rest/v1/l2_responses"
            f"?select=respondent_id,question_id,response,survey_id"
            f"&survey_id=eq.{sid}",
            headers,
        )
        all_l2.extend(rows)

    q_party = defaultdict(lambda: {"r_f": 0, "r_n": 0, "d_f": 0, "d_n": 0})
    for r in all_l2:
        qid = r.get("question_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        fav, intensity, has_int = score_content(qid, r["response"], r.get("survey_id"))
        if fav is None:
            continue
        is_fav = 1 if fav == 1 else 0
        party = party_lookup.get(r["respondent_id"], "")
        if party and "republican" in party.lower():
            q_party[qid]["r_f"] += is_fav
            q_party[qid]["r_n"] += 1
        elif party and "democrat" in party.lower():
            q_party[qid]["d_f"] += is_fav
            q_party[qid]["d_n"] += 1

    result = {}
    for qid, s in q_party.items():
        result[qid] = {
            "r_pct": (s["r_f"] / s["r_n"] * 100) if s["r_n"] >= 10 else None,
            "d_pct": (s["d_f"] / s["d_n"] * 100) if s["d_n"] >= 10 else None,
        }
    return result


# ══════════════════════════════════════════════════════════════════
# UNIFIED QUESTION DATA (MrP primary, raw fallback)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading question data...")
def load_question_data_hybrid(survey_ids=None):
    """
    Load question-level support data using MrP as primary source,
    falling back to raw scoring for surveys not yet in MrP.

    Returns:
        question_data: dict keyed by qid with:
            - mrp_pct: MrP-adjusted support % (None if not available)
            - raw_pct: Raw survey support %
            - display_pct: The number to show (mrp_pct if available, else raw_pct)
            - source: "mrp" or "raw"
            - construct, question_text, n_respondents
        mrp_coverage: dict with coverage stats
    """
    if survey_ids is None:
        survey_ids = CJ_SURVEYS

    # Step 1: Load MrP summaries
    mrp_data, mrp_surveys = load_mrp_question_summary()

    # Step 2: Identify CJ surveys that need raw fallback
    target_surveys = set(survey_ids)
    mrp_covered = target_surveys & mrp_surveys
    needs_raw = target_surveys - mrp_surveys

    # Step 3: Build question data from MrP source
    question_data = {}
    for (sid, qid), row in mrp_data.items():
        if sid not in target_surveys:
            continue
        # Skip non-CJ domain items unless explicitly requested
        construct = get_construct(qid) if SCORING_AVAILABLE else None
        if not construct:
            continue
        if qid in SKIPPED_QIDS:
            continue

        # If we already have this qid from a different survey, merge
        if qid in question_data:
            existing = question_data[qid]
            # Weighted average by respondent count
            old_n = existing["n_respondents"]
            new_n = row.get("n_respondents", 0)
            total_n = old_n + new_n
            if total_n > 0:
                existing["mrp_pct"] = (existing["mrp_pct"] * old_n + row["mrp_pct"] * new_n) / total_n
                existing["raw_pct"] = (existing["raw_pct"] * old_n + row["raw_pct"] * new_n) / total_n
                existing["n_respondents"] = total_n
                existing["display_pct"] = existing["mrp_pct"]
        else:
            question_data[qid] = {
                "mrp_pct": row.get("mrp_pct"),
                "raw_pct": row.get("raw_pct"),
                "display_pct": row.get("mrp_pct"),
                "source": "mrp",
                "construct": construct,
                "question_text": row.get("question_text", ""),
                "n_respondents": row.get("n_respondents", 0),
            }

    # Step 4: Load raw fallback for uncovered surveys
    if needs_raw:
        raw_data = load_raw_l2_for_surveys(list(needs_raw))
        for qid, rd in raw_data.items():
            if qid in question_data:
                # Merge raw into existing MrP entry (weighted)
                existing = question_data[qid]
                old_n = existing["n_respondents"]
                new_n = rd["n_respondents"]
                total_n = old_n + new_n
                if total_n > 0:
                    # MrP stays as is for MrP-covered portion; raw adds to overall
                    # For display, weighted blend
                    existing["raw_pct"] = (existing["raw_pct"] * old_n + rd["raw_pct"] * new_n) / total_n
                    # display_pct stays MrP-weighted where available
                    if existing["mrp_pct"] is not None:
                        existing["display_pct"] = (existing["mrp_pct"] * old_n + rd["raw_pct"] * new_n) / total_n
                    existing["n_respondents"] = total_n
                    existing["source"] = "mixed"
            else:
                question_data[qid] = {
                    "mrp_pct": None,
                    "raw_pct": rd["raw_pct"],
                    "display_pct": rd["raw_pct"],
                    "source": "raw",
                    "construct": rd["construct"],
                    "question_text": rd["question_text"],
                    "n_respondents": rd["n_respondents"],
                }

    # Coverage stats
    mrp_coverage = {
        "mrp_surveys": sorted(mrp_covered),
        "raw_surveys": sorted(needs_raw),
        "mrp_count": len(mrp_covered),
        "raw_count": len(needs_raw),
        "total": len(target_surveys),
        "pct_mrp": len(mrp_covered) / max(len(target_surveys), 1) * 100,
    }

    return question_data, mrp_coverage


# ══════════════════════════════════════════════════════════════════
# STATE-LEVEL QUESTION DATA (for Cross-State and State Report)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading state-level data...")
def load_state_question_data(survey_ids, state_name=None):
    """
    Load question data for specific surveys, preserving per-survey granularity.
    Returns dict keyed by qid with per-survey and aggregate stats.
    """
    mrp_data, mrp_surveys = load_mrp_question_summary()
    target_surveys = set(survey_ids)

    mrp_covered = target_surveys & mrp_surveys
    needs_raw = target_surveys - mrp_surveys

    question_data = {}

    # MrP-covered surveys
    for (sid, qid), row in mrp_data.items():
        if sid not in target_surveys:
            continue
        construct = get_construct(qid) if SCORING_AVAILABLE else None
        if not construct or qid in SKIPPED_QIDS:
            continue
        if qid not in question_data:
            question_data[qid] = {
                "mrp_pct": row.get("mrp_pct"),
                "raw_pct": row.get("raw_pct"),
                "display_pct": row.get("mrp_pct"),
                "source": "mrp",
                "construct": construct,
                "question_text": row.get("question_text", ""),
                "n_respondents": row.get("n_respondents", 0),
                "state": row.get("state", state_name),
            }

    # Raw fallback
    if needs_raw:
        raw_data = load_raw_l2_for_surveys(list(needs_raw))
        for qid, rd in raw_data.items():
            if qid not in question_data:
                question_data[qid] = {
                    "mrp_pct": None,
                    "raw_pct": rd["raw_pct"],
                    "display_pct": rd["raw_pct"],
                    "source": "raw",
                    "construct": rd["construct"],
                    "question_text": rd["question_text"],
                    "n_respondents": rd["n_respondents"],
                    "state": state_name,
                }

    return question_data, bool(mrp_covered), bool(needs_raw)
