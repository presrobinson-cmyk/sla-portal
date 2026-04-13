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
    """Render a compact top-of-page control bar: MrP/Raw toggle + cache age + refresh button.
    Moved out of the sidebar so it's visible above the fold, not buried below nav links.
    Returns the current selection: "mrp" or "raw".
    Persists in session_state so it stays consistent across pages.
    """
    if "data_source_mode" not in st.session_state:
        st.session_state["data_source_mode"] = "mrp"

    # Record when data was first loaded this session
    if "_data_loaded_at" not in st.session_state:
        st.session_state["_data_loaded_at"] = datetime.now(timezone.utc)

    col_toggle, col_age, col_btn = st.columns([4, 3, 1])

    with col_toggle:
        choice = st.radio(
            "Data source",
            ["MrP-Adjusted", "Raw Survey"],
            index=0 if st.session_state["data_source_mode"] == "mrp" else 1,
            key="_data_source_radio",
            horizontal=True,
            help=(
                "**MrP-Adjusted**: Population-weighted estimates using multilevel "
                "regression with poststratification. More accurate for state-level "
                "inference.\n\n"
                "**Raw Survey**: Direct response tallies without modeling adjustment."
            ),
        )

    mode = "mrp" if choice == "MrP-Adjusted" else "raw"
    st.session_state["data_source_mode"] = mode

    with col_age:
        loaded_at = st.session_state.get("_data_loaded_at")
        if loaded_at:
            age = datetime.now(timezone.utc) - loaded_at
            hours = int(age.total_seconds() // 3600)
            mins  = int((age.total_seconds() % 3600) // 60)
            age_str = f"{hours}h {mins}m ago" if hours else f"{mins}m ago"
            st.caption(f"Cached · loaded {age_str} · refreshes weekly")

    with col_btn:
        if st.button("↻ Refresh", key="_refresh_data_btn", use_container_width=True):
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
# CANONICAL SUPPORT-RATE HELPER
# ══════════════════════════════════════════════════════════════════

def tally_responses(rows, qid_col="question_id", response_col="response",
                    survey_col="survey_id", group_fn=None):
    """
    Canonical support-rate computation. SINGLE SOURCE OF TRUTH for all callers.

    Correct denominator rule:
        support_rate = n_favorable / n_total
        n_total = ALL responses, including neutral ("not sure") ones.
        score_content() returns (None, ...) for neutrals — those rows count
        toward n but not toward n_favorable.

    Args:
        rows       : list of dicts, each with at least qid_col and response_col
        qid_col    : column name holding the question ID
        response_col: column name holding the response text
        survey_col : column name holding the survey ID (passed to score_content)
        group_fn   : optional callable(row) → list[str] of group keys
                     If provided, returns per-group tallies in addition to overall.

    Returns:
        dict keyed by qid:
            {
              "f": int,          # favorable count
              "n": int,          # total count (includes neutrals)
              "groups": {        # only present when group_fn is provided
                  group_key: {"f": int, "n": int}, ...
              }
            }

    Callers compute pct as:  (s["f"] / s["n"] * 100) if s["n"] > 0 else 0
    Do NOT divide f/n-where-n-excludes-neutrals.
    """
    if not SCORING_AVAILABLE:
        return {}

    tallies = defaultdict(lambda: {"f": 0, "n": 0, "groups": defaultdict(lambda: {"f": 0, "n": 0})})

    for r in rows:
        qid = r.get(qid_col)
        if not qid or qid in SKIPPED_QIDS:
            continue
        if not get_construct(qid):
            continue

        fav, _, _ = score_content(qid, r.get(response_col, ""), r.get(survey_col))

        # Always increment total — neutral (fav=None) rows belong in denominator
        tallies[qid]["n"] += 1
        if fav == 1:
            tallies[qid]["f"] += 1

        # Per-group tallies when caller provides a grouping function
        if group_fn is not None:
            for grp in (group_fn(r) or []):
                tallies[qid]["groups"][grp]["n"] += 1
                if fav == 1:
                    tallies[qid]["groups"][grp]["f"] += 1

    return dict(tallies)


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

    # Build text/construct/survey_id metadata lookup from raw rows
    meta = {}
    for r in all_l2:
        qid = r.get("question_id")
        if qid and qid not in meta:
            meta[qid] = {
                "text": r.get("question_text", ""),
                "construct": get_construct(qid) if SCORING_AVAILABLE else None,
                "survey_id": r.get("survey_id"),
            }

    # Canonical tally — correct denominator (neutrals included in n)
    tallies = tally_responses(all_l2)

    result = {}
    for qid, s in tallies.items():
        if s["n"] < 20:
            continue
        m = meta.get(qid, {})
        result[qid] = {
            "raw_pct": s["f"] / s["n"] * 100,
            "mrp_pct": None,  # No MrP available
            "n_respondents": s["n"],
            "question_text": m.get("text", ""),
            "construct": m.get("construct"),
            "survey_id": m.get("survey_id"),
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

    # Canonical tally with party grouping — correct denominator
    def party_group_fn(r):
        party = party_lookup.get(r.get("respondent_id", ""), "").lower()
        if "republican" in party:
            return ["r"]
        elif "democrat" in party:
            return ["d"]
        return []

    tallies = tally_responses(all_l2, group_fn=party_group_fn)

    result = {}
    for qid, s in tallies.items():
        grp = s["groups"]
        result[qid] = {
            "r_pct": (grp["r"]["f"] / grp["r"]["n"] * 100) if grp["r"]["n"] >= 10 else None,
            "d_pct": (grp["d"]["f"] / grp["d"]["n"] * 100) if grp["d"]["n"] >= 10 else None,
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
          # Party
          "r": pct, "d": pct, "ind": pct,
          # Ideology
          "very_conservative": pct, "conservative": pct, "moderate": pct,
          "liberal": pct, "very_liberal": pct,
          # Race/Ethnicity
          "white": pct, "black": pct, "hispanic": pct, "non_white": pct,
          # Education
          "hs_or_less": pct, "some_college": pct, "college_plus": pct,
          # Age (4 brackets)
          "m18_34": pct, "m35_54": pct, "m55_64": pct, "m65plus": pct,
          # Gender
          "male": pct, "female": pct,
          # Community type
          "urban": pct, "suburban": pct, "rural": pct,
       }}
    Any group with < 10 respondents gets None.
    """
    import re as _re

    if survey_ids is None:
        survey_ids = CJ_SURVEYS
    if not SCORING_AVAILABLE:
        return {}

    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    # Pull all L1 demographic columns at once (including new columns)
    all_l1 = []
    for sid in survey_ids:
        try:
            rows = _paginate(
                f"{url}/rest/v1/l1_respondents"
                f"?select=respondent_id,party_id,ideology,education,age_bracket,"
                f"race_ethnicity,gender,area_type"
                f"&survey_id=eq.{sid}",
                headers,
            )
            all_l1.extend(rows)
        except Exception:
            continue  # Skip this survey; partial data is better than a full crash

    # Build respondent → group membership lookup
    demo_lookup = {}
    for d in all_l1:
        rid = d["respondent_id"]
        party    = (d.get("party_id") or "").lower()
        ideology = (d.get("ideology") or "").strip().lower()
        edu      = (d.get("education") or "").lower()
        age      = (d.get("age_bracket") or "").lower()  # DB column is age_bracket, not age
        race     = (d.get("race_ethnicity") or "").lower()
        gender   = (d.get("gender") or "").lower()
        area     = (d.get("area_type") or "").lower()

        groups = []

        # ── Party ────────────────────────────────────────────────
        if "republican" in party:
            groups.append("r")
        elif "democrat" in party:
            groups.append("d")
        elif "no party" in party or "independent" in party or "none" in party:
            groups.append("ind")

        # ── Ideology ─────────────────────────────────────────────
        # Order matters: check "very" before bare "conservative"/"liberal"
        if "very conservative" in ideology:
            groups.append("very_conservative")
        elif "conservative" in ideology:
            groups.append("conservative")
        elif "very liberal" in ideology:
            groups.append("very_liberal")
        elif "liberal" in ideology:
            groups.append("liberal")
        elif "moderate" in ideology:
            groups.append("moderate")

        # ── Race / Ethnicity ─────────────────────────────────────
        is_white = "white" in race and "non" not in race and "not" not in race
        if is_white:
            groups.append("white")
        else:
            # Only add non_white if race is actually specified (not blank)
            if race:
                groups.append("non_white")
        if "black" in race or "african" in race:
            groups.append("black")
        if "hispanic" in race or "latino" in race or "latina" in race:
            groups.append("hispanic")

        # ── Education ────────────────────────────────────────────
        if any(x in edu for x in ["less than high", "no high", "grade", "elementary", "middle"]):
            groups.append("hs_or_less")
        elif "high school" in edu or edu == "hs" or "diploma" in edu or "ged" in edu or "hs / ged" in edu:
            groups.append("hs_or_less")
        elif "some college" in edu or "associate" in edu or "vocational" in edu or "trade" in edu:
            groups.append("some_college")
        elif "bachelor" in edu or "bachelor+" in edu or "4-year" in edu or "university" in edu:
            groups.append("college_plus")
        elif "graduate" in edu or "master" in edu or "doctoral" in edu or "phd" in edu or "professional" in edu or "post-graduate" in edu:
            groups.append("college_plus")

        # ── Age (4 brackets) ──────────────────────────────────────
        # Extract first number from bracket string ("18-24" → 18, "65+" → 65)
        age_nums = [int(x) for x in _re.findall(r'\d+', age)]
        if age_nums:
            min_age = age_nums[0]
            if min_age < 35:
                groups.append("m18_34")
            elif min_age < 55:
                groups.append("m35_54")
            elif min_age < 65:
                groups.append("m55_64")
            else:
                groups.append("m65plus")

        # ── Gender ───────────────────────────────────────────────
        if "male" in gender and "fe" not in gender:
            groups.append("male")
        elif "female" in gender or "woman" in gender:
            groups.append("female")

        # ── Community Type ───────────────────────────────────────
        if "suburban" in area:
            groups.append("suburban")
        elif "urban" in area:
            groups.append("urban")
        elif "rural" in area:
            groups.append("rural")

        demo_lookup[rid] = groups

    # Pull L2 and score by demographic group
    # Pull one survey at a time so a single failure doesn't wipe everything
    all_l2 = []
    for sid in survey_ids:
        try:
            rows = _paginate(
                f"{url}/rest/v1/l2_responses"
                f"?select=respondent_id,question_id,response,survey_id"
                f"&survey_id=eq.{sid}",
                headers,
            )
            all_l2.extend(rows)
        except Exception:
            continue  # Skip this survey; partial data is better than a full crash

    GROUP_KEYS = [
        # Party
        "r", "d", "ind",
        # Ideology
        "very_conservative", "conservative", "moderate", "liberal", "very_liberal",
        # Race
        "white", "black", "hispanic", "non_white",
        # Education
        "hs_or_less", "some_college", "college_plus",
        # Age
        "m18_34", "m35_54", "m55_64", "m65plus",
        # Gender
        "male", "female",
        # Community
        "urban", "suburban", "rural",
    ]

    # Canonical tally with demographic grouping — correct denominator
    def demo_group_fn(r):
        return demo_lookup.get(r.get("respondent_id", ""), [])

    tallies = tally_responses(all_l2, group_fn=demo_group_fn)

    result = {}
    for qid, s in tallies.items():
        grp = s["groups"]
        result[qid] = {
            k: (grp[k]["f"] / grp[k]["n"] * 100) if grp[k]["n"] >= 10 else None
            for k in GROUP_KEYS
        }
    return result


# ══════════════════════════════════════════════════════════════════
# RESPONDENT-LEVEL DATA (for multi-group intersection queries)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=604800, show_spinner="Loading respondent-level data...")
def load_respondent_level_data(survey_ids=None):
    """
    Return raw respondent→group membership and pre-scored responses.
    Used by the scatter view to compute intersection support for any
    combination of demographic groups (e.g. 'Republican Women').

    Returns:
        demo_lookup  : dict[respondent_id → frozenset(group_keys)]
        scored_responses : list[{respondent_id, qid, fav}]
            fav = 1 (favorable), 0 (unfavorable), None (neutral)
    """
    import re as _re

    if survey_ids is None:
        survey_ids = CJ_SURVEYS
    if not SCORING_AVAILABLE:
        return {}, []

    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    # ── Pull L1 demographics (same group logic as load_demo_splits) ──
    all_l1 = []
    for sid in survey_ids:
        try:
            rows = _paginate(
                f"{url}/rest/v1/l1_respondents"
                f"?select=respondent_id,party_id,ideology,education,age_bracket,"
                f"race_ethnicity,gender,area_type"
                f"&survey_id=eq.{sid}",
                headers,
            )
            all_l1.extend(rows)
        except Exception:
            continue

    demo_lookup = {}
    for d in all_l1:
        rid = d["respondent_id"]
        party    = (d.get("party_id") or "").lower()
        ideology = (d.get("ideology") or "").strip().lower()
        edu      = (d.get("education") or "").lower()
        age      = (d.get("age_bracket") or "").lower()
        race     = (d.get("race_ethnicity") or "").lower()
        gender   = (d.get("gender") or "").lower()
        area     = (d.get("area_type") or "").lower()

        groups = []

        # Party
        if "republican" in party:
            groups.append("r")
        elif "democrat" in party:
            groups.append("d")
        elif "no party" in party or "independent" in party or "none" in party:
            groups.append("ind")

        # Ideology
        if "very conservative" in ideology:
            groups.append("very_conservative")
        elif "conservative" in ideology:
            groups.append("conservative")
        elif "very liberal" in ideology:
            groups.append("very_liberal")
        elif "liberal" in ideology:
            groups.append("liberal")
        elif "moderate" in ideology:
            groups.append("moderate")

        # Race
        is_white = "white" in race and "non" not in race and "not" not in race
        if is_white:
            groups.append("white")
        elif race:
            groups.append("non_white")
        if "black" in race or "african" in race:
            groups.append("black")
        if "hispanic" in race or "latino" in race or "latina" in race:
            groups.append("hispanic")

        # Education
        if any(x in edu for x in ["less than high", "no high", "grade", "elementary", "middle"]):
            groups.append("hs_or_less")
        elif "high school" in edu or edu == "hs" or "diploma" in edu or "ged" in edu or "hs / ged" in edu:
            groups.append("hs_or_less")
        elif "some college" in edu or "associate" in edu or "vocational" in edu or "trade" in edu:
            groups.append("some_college")
        elif "bachelor" in edu or "bachelor+" in edu or "4-year" in edu or "university" in edu:
            groups.append("college_plus")
        elif "graduate" in edu or "master" in edu or "doctoral" in edu or "phd" in edu or "professional" in edu or "post-graduate" in edu:
            groups.append("college_plus")

        # Age
        age_nums = [int(x) for x in _re.findall(r'\d+', age)]
        if age_nums:
            min_age = age_nums[0]
            if min_age < 35:
                groups.append("m18_34")
            elif min_age < 55:
                groups.append("m35_54")
            elif min_age < 65:
                groups.append("m55_64")
            else:
                groups.append("m65plus")

        # Gender
        if "male" in gender and "fe" not in gender:
            groups.append("male")
        elif "female" in gender or "woman" in gender:
            groups.append("female")

        # Community type
        if "suburban" in area:
            groups.append("suburban")
        elif "urban" in area:
            groups.append("urban")
        elif "rural" in area:
            groups.append("rural")

        demo_lookup[rid] = frozenset(groups)

    # ── Pull and score L2 responses ──
    all_l2 = []
    for sid in survey_ids:
        try:
            rows = _paginate(
                f"{url}/rest/v1/l2_responses"
                f"?select=respondent_id,question_id,response,survey_id"
                f"&survey_id=eq.{sid}",
                headers,
            )
            all_l2.extend(rows)
        except Exception:
            continue

    scored = []
    for r in all_l2:
        qid = r.get("question_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        if not get_construct(qid):
            continue
        fav, _, _ = score_content(qid, r.get("response", ""), r.get("survey_id"))
        scored.append({
            "respondent_id": r["respondent_id"],
            "qid": qid,
            "fav": fav,  # 1, 0, or None (neutral — counts in denominator)
        })

    return demo_lookup, scored


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
            # None-safe weighted average by respondent count.
            # mrp_pct / raw_pct can be null in the DB; multiplying None * n raises TypeError.
            old_n = existing["n_respondents"]
            new_n = row.get("n_respondents", 0)
            total_n = old_n + new_n
            if total_n > 0:
                e_mrp, r_mrp = existing["mrp_pct"], row.get("mrp_pct")
                if e_mrp is not None and r_mrp is not None:
                    existing["mrp_pct"] = (e_mrp * old_n + r_mrp * new_n) / total_n
                elif r_mrp is not None:
                    existing["mrp_pct"] = r_mrp
                # else: keep existing mrp_pct (may be None — better than crashing)

                e_raw, r_raw = existing["raw_pct"], row.get("raw_pct")
                if e_raw is not None and r_raw is not None:
                    existing["raw_pct"] = (e_raw * old_n + r_raw * new_n) / total_n
                elif r_raw is not None:
                    existing["raw_pct"] = r_raw
                # else: keep existing raw_pct

                existing["n_respondents"] = total_n
                existing["display_pct"] = existing["mrp_pct"] if existing["mrp_pct"] is not None else existing["raw_pct"]
        else:
            question_data[qid] = {
                "mrp_pct": row.get("mrp_pct"),
                "raw_pct": row.get("raw_pct"),
                "display_pct": row.get("mrp_pct"),
                "source": "mrp",
                "construct": construct,
                "question_text": row.get("question_text", ""),
                "response_label": row.get("response_label", ""),  # Favorable response text
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
                    "response_label": "",  # Not available for raw-only fallback
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
