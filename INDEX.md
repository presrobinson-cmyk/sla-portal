# SLA Portal — File Index

**Complete multi-page Streamlit application for Second Look Alliance criminal justice reform data platform.**

## Core Files

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | 280 | Home dashboard with KPI cards, nav, data overview |
| `auth.py` | 161 | Authentication module (existing, do not edit) |
| `requirements.txt` | 5 | Python dependencies (streamlit, plotly, pandas, numpy, requests) |

## Pages (6 main sections)

| Page | Lines | Purpose |
|------|-------|---------|
| `pages/1_Survey_Results.py` | 445 | State dashboards, durability matrix, heatmaps, cross-state comparison, voter pathways, message deploy |
| `pages/2_VIP_Scores.py` | 480 | 6 voter archetypes, distributions, demographic profiles, persuasion pathways |
| `pages/3_MrP_Estimates.py` | 410 | MrP models, state estimates, demographic subgroups, trends, rankings, map placeholder |
| `pages/4_Media_Portal.py` | 400 | Campaign builder, active campaigns, spend tracker with demo data |
| `pages/5_Survey_Writer.py` | 420 | Question generation, rewriting, question bank browser, best practices guide |
| `pages/6_AI_Search.py` | 235 | Chat-style query interface with suggested queries and demo responses |

**Total: ~3,100 lines of Python**

## Documentation

| File | Purpose |
|------|---------|
| `GUIDE.md` | Comprehensive guide: setup, page descriptions, design, architecture, Phase 2 roadmap |
| `INDEX.md` | This file — quick file inventory |

## Getting Started

```bash
cd /sessions/intelligent-practical-johnson/mnt/Actionable\ Intel/sla_portal_site/
pip install -r requirements.txt
streamlit run app.py
```

Open browser to `http://localhost:8501`

**Demo Login:**
- Username: `admin` or `preston`
- Password: `actionable2026` or `intel2026`

## Key Features

✅ **Multi-page navigation** with 6 main sections (home + 6 pages)
✅ **Dark theme throughout** (bg: #0f1117, cards: #1a1d29, accent: #22c55e green)
✅ **Authentication gate** with logout button
✅ **Realistic demo data** (12.5K respondents, 6 states, 11 constructs, 6 archetypes, 3 axes)
✅ **Interactive visualizations** (Plotly charts: scatter, bar, heatmap, line, area, pie)
✅ **Forms & inputs** (selectors, multiselect, sliders, text areas, number inputs)
✅ **Responsive layout** (columns, tabs, dividers, styled cards)
✅ **Data tables** (sortable, filterable, exportable)
✅ **Message history** (AI search chat interface)
✅ **Status badges** (active/paused/completed)
✅ **Progress indicators** (metric cards, progress bars)
✅ **Best practices sidebar** (survey design guidelines)
✅ **Comprehensive documentation** (GUIDE.md with 400+ lines)

## Page Summary

### Home (`app.py`)
- Welcome banner
- 4 KPI metric cards
- 6 navigation cards
- Data overview table (state coverage, constructs)

### Survey Results (`1_Survey_Results.py`)
- State Dashboard: respondents, golden zone %, support bars, durability
- Durability Matrix: support vs durability scatter (all constructs, all states)
- Coalition Heatmap: demographic group support by construct
- Cross-State Comparison: side-by-side bar charts
- Voter Pathways: 3-axis decision tree with messaging strategy
- Message Deploy: quadrant assignment (Golden Zone, Primary Fuel, General Arsenal, Dead Weight)

### VIP Scores (`2_VIP_Scores.py`)
- Archetype Explorer: 6 archetypes with descriptions, traits, construct profiles
- State Distribution: stacked bar chart across all states
- Demographic Profiles: pie chart (party), bar charts (age, education, area)
- Persuasion Pathways: messaging that moves each archetype

### MrP Estimates (`3_MrP_Estimates.py`)
- State Estimates: point estimate, 95% CI, margin of error
- Demographic Subgroups: estimates by demographic group with error bars
- Trend Analysis: 6-month trend with CI band and direction indicator
- State Rankings: ranked list with progress bars, heatmap of all constructs
- Map Explorer: placeholder + summary cards

### Media Portal (`4_Media_Portal.py`)
- Campaign Builder: form to create campaigns (name, objective, state, channels, budget, audience targeting, creative)
- Active Campaigns: 5 demo campaigns with status, impressions, clicks, spend, CPM, CTR
- Spend Tracker: budget overview, daily spend trend, channel breakdown, commission table

### Survey Writer (`5_Survey_Writer.py`)
- Write New Questions: topic input, question type, axis, difficulty, Likert options → generates 3 demo questions
- Rewrite Questions: paste question, select improvements → shows issues found + 3 suggested rewrites
- Question Bank: browse 5+ questions, filter by construct/axis/type, export CSV/JSON
- Best Practices: 4-column guide + MrP principles + design checklist

### AI Search (`6_AI_Search.py`)
- Chat interface with message history
- 8 suggested query chips (click to populate input)
- Demo responses for common patterns (state queries, comparisons, durability, messaging, archetypes)
- Formatting: bot responses as styled cards with stats

## Design

### Colors
- **Background**: #0f1117 (dark navy)
- **Cards**: #1a1d29 (slightly lighter)
- **Borders**: #2a2d3a (dark gray)
- **Text**: #e8e8ed (off-white)
- **Muted**: #8b8fa3 (medium gray)
- **Primary accent**: #22c55e (green, SLA branding)
- **Secondary**: #3b82f6 (blue), #f59e0b (amber), #818cf8 (purple)

### Quadrant Colors
- Golden Zone: #22c55e (green)
- Primary Fuel: #3b82f6 (blue)
- General Arsenal: #f59e0b (amber)
- Dead Weight: #6b7280 (gray)

### Typography
- **Font**: DM Sans (Google Fonts, imported in CSS)
- **Monospace**: JetBrains Mono (for code)
- **Headings**: 700 weight, off-white
- **Labels**: 500 weight, medium gray, uppercase + letter-spacing

## Demo Data

All pages generate **deterministic pseudo-random data** based on hashing:
- 6 states (OK, LA, NC, VA, MA, NJ)
- 11 constructs (Procedural Fairness, Proportionality, Constitutional Rights, etc.)
- 6 archetypes (System Defenders 22%, Cautious Reformers 26%, etc.)
- 3 belief axes (System Reliability, Capacity for Change, Change-Punishment Relationship)
- Support estimates: 40-85%
- Durability scores: 30-95
- Respondent counts: 1,800-2,400 per state
- Confidence intervals: ±3-8 percentage points

No external APIs required for MVP.

## Authentication

All pages protected by `require_auth()` imported from `auth.py`:

```python
from auth import require_auth
username = require_auth("Second Look Alliance", accent_color="#22c55e")
```

**Demo Credentials:**
- admin / actionable2026
- preston / intel2026

**Production**: Configure Streamlit secrets with username→password hash mapping.

## Deployment

### Streamlit Community Cloud (Recommended)
1. Push repo to GitHub
2. Connect via Streamlit Cloud dashboard
3. Automatic deploys on push

### Railway (Fallback)
1. Configure via `railway.json`
2. Deploy: `railway up`
3. Set environment variables for secrets

## Next Steps (Phase 2)

- **Data Integration**: Live Supabase queries replacing demo data
- **AI Backend**: GPT-4 for question generation + LLM for AI search
- **Media APIs**: StackAdapt, Meta, X integrations
- **Map Visualization**: Choropleth for state estimates
- **Export Tools**: PDF briefings, Excel workbooks
- **Performance**: Caching, pagination, lazy loading

---

**Created**: 2026-04-09
**Status**: MVP complete, demo data functional, Phase 2 roadmap defined
**Lines of Code**: 3,100+ Python
**Dependencies**: streamlit, plotly, pandas, numpy, requests
