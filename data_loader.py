"""
Shared data loader for SLA Portal — Hybrid MrP + Raw fallback.

Priority: MrP-adjusted numbers from mrp_question_summary when available.
Fallback: Runtime scoring of l2_responses for surveys not yet in MrP.

All portal pages should import from here instead of querying Supabase directly.
"""

import streamlit as st
import requests
from collections import defaultdict
from datetime import datetime, timezone

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
# MrP / RAW TOGGLE HELPERS
# ══════════════════════════════════════════════════════════════════

def render_data_source_toggle():
    """Render a sidebar toggle for MrP vs Raw data display.
    Returns the current selection: "mrp" or "raw".
    Persists in session_state so it stays consistent across pages.
    """
    if "data_source_mode" not in st.session_state:
        st.session_state["data_source_mode"] = "mrp"

    # Record when data was first loaded this session
    if "_data_loaded_at" not in st.session_state:
        st.session_state["_data_loaded_at"] = datetime.now(timezone.utc)

    with st.sidebar:
        st.markdown("### Data Source")
        choice = st.radio(
            "Display numbers as:",
            ["MrP-Adjusted", "Raw Survey"],
            index=0 if st.session_state["data_source_mode"] == "mrp" else 1,
            key="_data_source_radio",
            help=(
                "**MrP-Adjusted**: Population-weighted estimates using multilevel "
                "regression with poststratification. More accurate for state-level "
                "inference.\n\n"
                "**Raw Survey**: Direct response tallies without modeling adjustment."
            ),
        )
        mode = "mrp" if choice == "MrP-Adjusted" else "raw"
        st.session_state["data_source_mode"] = mode

        # Cache freshness info + manual refresh
        loaded_at = st.session_state.get("_data_loaded_at")
        if loaded_at:
            age = datetime.now(timezone.utc) - loaded_at
            hours = int(age.total_seconds() // 3600)
            mins  = int((age.total_seconds() % 3600) // 60)
            age_str = f"{hours}h {mins}m ago" if hours else f"{mins}m ago"
            st.caption(f"Data cached · loaded {age_str} · refreshes weekly")
        if st.button("↻ Refresh data", key="_refresh_data_btn", use_container_width=True):
            st.cache_data.clear()
            st.session_state["_data_loaded_at"] = datetime.now(timezone.utc)
            st.rerun()

        st.divider()

    return mode


def get_display_pct(qd, mode="mrp"):
    """Pick the right percentage to display given the toggle mode.
    qd: a question_data dict with mrp_pct and raw_pct keys.
    mode: "mrp" or "raw".
    """
    if mode == "raw":
        return qd.get("raw_pct") if qd.get("raw_pct") is not None else qd.get("mrp_pct")
    else:
        return qd.get("mrp_pct") if qd.get("mrp_pct") is not None else qd.get("raw_pct")


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

@st.cache_data(ttl=604800, show_spinner="Loading MrP estimates...")  # 1-week cache — data only changes on DB upload
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

@st.cache_data(ttl=604800, show_spinner="Loading raw survey data (fallback)...")  # 1-week cache
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

@st.cache_data(ttl=604800, show_spinner="Loading party breakdowns...")  # 1-week cache
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
# DEMOGRAPHIC SUBGROUP SPLITS (for scatter plot X axis)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=604800, show_spinner="Loading demographic breakdowns...")
def load_demo_splits(survey_ids=None):
    """
    Load support rates split by key demographic subgroups.
    Returns dict keyed by question_id:
      {qid: {
          "r": r_pct,          "d": d_pct,
          "hs_or_less": pct,   "some_college": pct,  "college_plus": pct,
          "m18_34": pct,       "m35_54": pct,        "m55plus": pct,
          "male": pct,         "female": pct,
       }}
    Any group with < 10 respondents gets None.
    """
    if survey_ids is None:
        survey_ids = CJ_SURVEYS
    if not SCORING_AVAILABLE:
        return {}

    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    # Pull all L1 demographic columns at once
    all_l1 = []
    for sid in survey_ids:
        rows = _paginate(
            f"{url}/rest/v1/l1_respondents"
            f"?select=respondent_id,party_id,education,age,gender"
            f"&survey_id=eq.{sid}",
            headers,
        )
        all_l1.extend(rows)

    # Build respondent → group membership lookup
    demo_lookup = {}
    for d in all_l1:
        rid = d["respondent_id"]
        party = (d.get("party_id") or "").lower()
        edu   = (d.get("education") or "").lower()
        age   = (d.get("age") or "").lower()
        gender = (d.get("gender") or "").lower()

        groups = []
        # Party
        if "republican" in party:
            groups.append("r")
        elif "democrat" in party:
            groups.append("d")
        # Education — map common Alchemer / L2 labels
        if any(x in edu for x in ["less than high", "no high", "grade", "elementary", "middle"]):
            groups.append("hs_or_less")
        elif "high school" in edu or "hs" == edu or "diploma" in edu or "ged" in edu:
            groups.append("hs_or_less")
        elif "some college" in edu or "associate" in edu or "vocational" in edu or "trade" in edu:
            groups.append("some_college")
        elif "bachelor" in edu or "college" in edu or "4-year" in edu or "university" in edu:
            groups.append("college_plus")
        elif "graduate" in edu or "master" in edu or "doctoral" in edu or "phd" in edu or "professional" in edu:
            groups.append("college_plus")
        # Age
        if any(x in age for x in ["18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34"]):
            groups.append("m18_34")
        elif "18-34" in age or "18 to 34" in age:
            groups.append("m18_34")
        elif any(x in age for x in ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54"]):
            groups.append("m35_54")
        elif "35-54" in age or "35 to 54" in age:
            groups.append("m35_54")
        elif any(x in age for x in ["55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "75", "80", "85", "older", "65+"]):
            groups.append("m55plus")
        elif "55+" in age or "55 and" in age or "55 or" in age:
            groups.append("m55plus")
        # Gender
        if "male" in gender and "fe" not in gender:
            groups.append("male")
        elif "female" in gender or "woman" in gender:
            groups.append("female")
        demo_lookup[rid] = groups

    # Pull L2 and score by demographic group
    all_l2 = []
    for sid in survey_ids:
        rows = _paginate(
            f"{url}/rest/v1/l2_responses"
            f"?select=respondent_id,question_id,response,survey_id"
            f"&survey_id=eq.{sid}",
            headers,
        )
        all_l2.extend(rows)

    GROUP_KEYS = ["r", "d", "hs_or_less", "some_college", "college_plus",
                  "m18_34", "m35_54", "m55plus", "male", "female"]
    q_demo = defaultdict(lambda: {k: {"f": 0, "n": 0} for k in GROUP_KEYS})

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
        for grp in demo_lookup.get(r["respondent_id"], []):
            q_demo[qid][grp]["f"] += is_fav
            q_demo[qid][grp]["n"] += 1

    result = {}
    for qid, groups in q_demo.items():
        result[qid] = {
            grp: (groups[grp]["f"] / groups[grp]["n"] * 100) if groups[grp]["n"] >= 10 else None
            for grp in GROUP_KEYS
        }
    return result


# ══════════════════════════════════════════════════════════════════
# UNIFIED QUESTION DATA (MrP primary, raw fallback)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=604800, show_spinner="Loading question data...")  # 1-week cache
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

@st.cache_data(ttl=604800, show_spinner="Loading state-level data...")  # 1-week cache
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
