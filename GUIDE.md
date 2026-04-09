# SLA Portal — Multi-Page Streamlit App

**Second Look Alliance (SLA) Portal** — Criminal justice reform data dashboard for advocates, policymakers, and researchers.

## Quick Start

```bash
cd /sessions/intelligent-practical-johnson/mnt/Actionable\ Intel/sla_portal_site/
pip install -r requirements.txt
streamlit run app.py
```

**Demo credentials:**
- Username: `admin` or `preston`
- Password: `actionable2026` or `intel2026`

---

## Project Structure

```
sla_portal_site/
├── app.py                          # Main entry point / home dashboard
├── auth.py                         # Authentication module (DO NOT EDIT)
├── requirements.txt                # Python dependencies
├── pages/
│   ├── 1_Survey_Results.py         # State dashboards, durability matrices, heatmaps, comparisons
│   ├── 2_VIP_Scores.py             # Voter archetype profiles & persuasion pathways
│   ├── 3_MrP_Estimates.py          # Geographic models with confidence intervals
│   ├── 4_Media_Portal.py           # Campaign builder & spend tracker
│   ├── 5_Survey_Writer.py          # AI question writer/rewriter with best practices
│   └── 6_AI_Search.py              # Chat-style data query interface
├── .streamlit/
│   └── config.toml                 # Streamlit configuration (dark theme, fonts, etc.)
└── GUIDE.md                        # This file
```

---

## Page Descriptions

### `app.py` — Home Dashboard

Landing page with:
- **Welcome banner** with SLA branding and description
- **KPI cards**: States Covered (6), Total Respondents (~12.5K), Active Surveys (18), Reform Temperature (avg 62°)
- **Navigation cards** for all 6 main sections with icons and descriptions
- **Data overview**: State coverage table and construct list
- **Last update timestamp**

Dark theme throughout: bg `#0f1117`, cards `#1a1d29`, accent green `#22c55e`, text `#e8e8ed`.

---

### `pages/1_Survey_Results.py` — Survey Results

6 tabs covering core CJ reform survey analysis:

#### **Tab 1: State Dashboard**
- State selector dropdown
- KPI cards: respondents, golden zone %, top construct
- Support gauge bars for all 11 constructs
- Durability snapshot (bar chart of top durable constructs)

#### **Tab 2: Durability Matrix**
- Scatter plot: Support % (x-axis) vs Durability (y-axis)
- Each point = a construct in a state
- Colored by state
- Threshold lines at 60% support/durability

#### **Tab 3: Coalition Heatmap**
- Demographic group × construct support heatmap
- Selectors for construct and demographic type (Party, Ideology, Race, Age, Gender, Education, Area)
- Color scale: red (low) to green (high)

#### **Tab 4: Cross-State Comparison**
- Multi-select state and construct filters
- Grouped bar chart comparing support across selected states & constructs
- Show side-by-side state performance

#### **Tab 5: Voter Pathways**
- 3 Belief Axes decision tree explanation:
  1. **System Reliability**: Does CJ system work?
  2. **Capacity for Change**: Can people change?
  3. **Change-Punishment Relationship**: Does punishment enable change?
- Yes/No paths for each axis with messaging strategy

#### **Tab 6: Message Deploy**
- Quadrant assignment based on support × durability:
  - **🟢 Golden Zone** (high/high): Lead with these
  - **🔵 Primary Fuel** (high/low): Protect and reinforce
  - **🟡 General Arsenal** (low/high): Build foundation
  - **⚫ Dead Weight** (low/low): Avoid or pivot

---

### `pages/2_VIP_Scores.py` — VIP Archetypes

Voter archetype explorer with 4 tabs:

#### **Tab 1: Archetype Explorer**
- Interactive selector for each of the 6 archetypes:
  1. **System Defenders** (22%): Trust institutions, value order, fiscal conservative
  2. **Cautious Reformers** (26%): Evidence-focused, risk-averse, pragmatic
  3. **Compassionate Pragmatists** (24%): Empathetic, values-driven, hope-focused
  4. **Justice Skeptics** (16%): Skeptical of institutions, demand structural change
  5. **Rehabilitation Champions** (7%): Believe in human potential, transformative approach
  6. **Abolition-Leaning** (5%): Question system viability, advocate alternatives

- For selected archetype:
  - Full description with icon and population %
  - Key traits as badges
  - Construct support profile (bar chart)
  - Effective messaging vs. approaches to avoid

#### **Tab 2: State Distribution**
- Stacked bar chart of archetype % by state
- Cross-state comparison showing variation

#### **Tab 3: Demographic Profiles**
- Pie chart: Party affiliation breakdown
- Bar chart: Age distribution
- Bar chart: Education level
- Bar chart: Geographic area (Urban/Suburban/Rural)

#### **Tab 4: Persuasion Pathways**
- For each archetype:
  - **Most Effective Messaging**: 2 top messages
  - **Avoid These Approaches**: 2 strategies to skip
- Styled with green checkmark / red X visual hierarchy

---

### `pages/3_MrP_Estimates.py` — MrP Geographic Models

Multilevel regression with post-stratification estimates:

#### **Tab 1: State Estimates**
- State & construct selectors
- Point estimate, 95% CI, margin of error as metric cards
- All constructs for selected state with error bars (CI visualization)

#### **Tab 2: Demographic Subgroups**
- Construct & demographic type selectors
- Demographic groups dropdown (Party, Ideology, Race, Age, Gender, Education)
- Bar chart with error bars for each demographic group
- Detailed table with estimates and CIs

#### **Tab 3: Trend Analysis**
- Construct & state selectors
- Line chart showing estimate over 6 months with CI band shading
- Starting estimate, trend direction (increasing/decreasing/stable) with pp change

#### **Tab 4: State Rankings**
- Construct selector
- Ranked list of states (1-6) with estimates and CI bands
- Progress bar visualization for each state
- Heatmap across all constructs showing state rankings

#### **Tab 5: Map Explorer**
- Placeholder for future choropleth map
- State rankings summary (highest/lowest support)
- Link to State Rankings tab for drill-down

---

### `pages/4_Media_Portal.py` — Campaign Builder & Tracker

MVP media placement and campaign management interface:

#### **Tab 1: Campaign Builder**
- **Campaign Details**: Name, objective (Survey Fielding / Awareness / Persuasion), state, channels (Meta/X/Display/OTT)
- **Budget**: Daily budget input, duration selector (1-8 weeks), calculated total budget
- **Demographic Filters**: Party, age range, education level
- **Attitudinal Filters**: VIP archetypes, message constructs to emphasize
- **Creative**: Ad copy text area, creative asset upload placeholder
- Form submission → confirmation with campaign specs

#### **Tab 2: Active Campaigns**
- KPI cards: Total Budget, Amount Spent (with %), Impressions
- Status & state filter dropdowns
- Campaign cards showing:
  - Campaign name, state, objective, status badge (Active/Paused/Completed)
  - Impressions, clicks, date range
  - Budget utilization progress bar
  - CPM, CTR metrics

#### **Tab 3: Spend Tracker**
- Budget summary metrics (Total, Spent, Remaining, Utilization %)
- Line chart of daily spend over time
- Pie chart: spend by channel (Meta/X/Display/OTT)
- Commission breakdown table (Meta 5%, X 7%, Display 8%, Agency Fee 10%)

**Note:** MVP only — actual StackAdapt, Meta, X API integrations in Phase 2.

---

### `pages/5_Survey_Writer.py` — AI Question Writer

Question generation and improvement tool:

#### **Tab 1: Write New Questions**
- Inputs:
  - Topic/construct (free text)
  - Question type (Opinion/Support, Likelihood, Priority, Behavioral)
  - Related belief axes (multi-select)
  - Difficulty slider (Easy/Moderate/Hard)
  - Language level (Simple/Standard/Technical)
  - Likert scale length (4-7 options)
  - Target population
- Generates 3 demo questions with:
  - Question text
  - Type, construct, scale info
  - Quality assessment (✓ checks)
- Save/refine buttons

#### **Tab 2: Rewrite Questions**
- Paste/type existing question
- Multi-select improvement focus areas (leading language, clarity, Likert anchoring, jargon, behavioral, burden, specificity)
- Rewrite style selector (Conservative/Moderate/Aggressive)
- Issues found section: severity (High/Medium/Low), description, impact
- 3 suggested rewrites (v1: neutral phrasing, v2: behavioral anchor, v3: axes-aligned)
- Use buttons to select preferred version

#### **Tab 3: Question Bank**
- Filter dropdowns: Construct, Belief Axis, Question Type
- Browse saved questions with metadata badges
- Table showing: Text, Construct, Axis, Type, Scale
- Export buttons: CSV or JSON download

#### **Tab 4: Best Practices**
- Two-column layout:
  - **Question Writing**: Behavioral past-action, no knowledge tests, Likert scales, avoid jargon
  - **Bias & Clarity**: Remove leading language, avoid double-barrel, balance framing, test with population
- MrP measurement principles section
- CJ Reform checklist (8 items with checkboxes)

**Note:** UI mockup with demo outputs — full AI backend in Phase 2.

---

### `pages/6_AI_Search.py` — Chat Data Query Interface

Chat-style natural language search over survey data:

#### **Features**
- Message history display (user messages in green, bot in blue)
- Suggested query chips (8 example questions):
  - "What % of NC Republicans support sentencing reform?"
  - "Compare rehabilitation support across states"
  - "Which constructs have the highest durability in OK?"
  - "What messaging moves Cautious Reformers in LA?"
  - etc.
- Text input for custom queries
- Click suggestion chips to auto-populate
- Demo responses tied to common query patterns:
  - State × party queries → archetype breakdown
  - Cross-state comparisons → rankings with CI
  - Durability queries → Golden Zone + quadrant analysis
  - Messaging queries → persuasion impact + channel recommendations
  - Archetype queries → state distribution variations

**Note:** UI/response templates only — full AI backend with live SQL queries in Phase 2.

---

## Design & Styling

### Color Palette

| Purpose | Color | Usage |
|---------|-------|-------|
| Background | `#0f1117` | Page, sidebar bg |
| Card | `#1a1d29` | Metric cards, sections |
| Border | `#2a2d3a` | Dividers, card borders |
| Text | `#e8e8ed` | Primary text |
| Muted | `#8b8fa3` | Labels, captions |
| Accent (Primary) | `#22c55e` | SLA green, success, key metrics |
| Secondary | `#3b82f6` | Blue, secondary info |
| Tertiary | `#f59e0b` | Amber, warnings |
| Accent (Purple) | `#818cf8` | Purple, data viz |

### Quadrant Colors

- **Golden Zone**: `#22c55e` (green)
- **Primary Fuel**: `#3b82f6` (blue)
- **General Arsenal**: `#f59e0b` (amber)
- **Dead Weight**: `#6b7280` (gray)

### Typography

- **Font Family**: DM Sans (Google Fonts)
- **Monospace**: JetBrains Mono
- **Headings**: 700 weight, `#e8e8ed`
- **Labels**: 500 weight, `#8b8fa3`, uppercase with 0.05em letter-spacing

### Components

- **Cards**: `#1a1d29` background, `#2a2d3a` border, 12px border-radius
- **Progress Bars**: Green (`#22c55e`) fill on dark background
- **Status Badges**: Colored background with border, e.g., Active = green 10% bg + green border
- **Metric Cards**: Large value in accent color, label in muted text

---

## Demo Data

All pages use **deterministic pseudo-random generation** based on state/construct/archetype hashing to ensure:
- Consistent data across page reloads
- Realistic-looking (but synthetic) survey statistics
- No external API calls required

Key data structures:

### States
- Oklahoma, Louisiana, North Carolina, Virginia, Massachusetts, New Jersey
- Each: 1,800-2,400 respondents
- 3 surveys per state

### Constructs (11)
1. Procedural Fairness
2. Proportionality
3. Constitutional Rights
4. Juvenile Compassion
5. Rehabilitation
6. Dangerousness Distinction
7. Fiscal Efficiency
8. Fines & Fees
9. Compassion
10. Police Discretion
11. Promise of Redemption

### Belief Axes (3)
1. **System Reliability**: Does the CJ system generally get it right?
2. **Capacity for Change**: Can systems and people change?
3. **Change-Punishment Relationship**: Does punishment enable change?

### VIP Archetypes (6)
1. System Defenders (22%)
2. Cautious Reformers (26%)
3. Compassionate Pragmatists (24%)
4. Justice Skeptics (16%)
5. Rehabilitation Champions (7%)
6. Abolition-Leaning (5%)

---

## Authentication

Pages are gated behind `require_auth()` imported from `auth.py`:

```python
from auth import require_auth
username = require_auth("Second Look Alliance", accent_color="#22c55e")
```

**Demo accounts** (fallback if secrets not configured):
- `admin` / `actionable2026`
- `preston` / `intel2026`

**In production**, configure Streamlit secrets:

```yaml
# ~/.streamlit/secrets.toml
[users]
"your_username" = "hashed_password_here"
```

---

## Running the App

### Local Development

```bash
cd /sessions/intelligent-practical-johnson/mnt/Actionable\ Intel/sla_portal_site/
streamlit run app.py
```

Streamlit will start on `http://localhost:8501`

### Deployment Options (from project notes)

1. **Streamlit Community Cloud** (free tier, recommended for MVP):
   - Push repo to GitHub
   - Connect via Streamlit Community Cloud dashboard
   - Automatic deploys on push

2. **Railway** (fallback, low-cost):
   - Deploy via `railway up`
   - Environment variables for auth secrets

3. **DreamHost** (legacy, being phased out):
   - Discontinue in favor of Streamlit Cloud

---

## Phase 2 Enhancements

Planned additions (outside scope of this build):

### Data Integration
- Live Supabase connection replacing demo data
- Real MrP model queries with confidence intervals
- Temporal pooling with decay policies (CJ: 12mo full, 24mo half, 36mo 10%)

### AI Backend
- **Survey Writer**: GPT-4 integration for question generation/rewriting with validation
- **AI Search**: LLM-powered natural language → SQL with retrieval-augmented generation (RAG)

### Media Portal
- StackAdapt API for programmatic media buying
- Meta/X OAuth for campaign management
- Real spend tracking and performance metrics

### Visualization Enhancements
- Choropleth map for state estimates (Plotly Scattergeo or Folium)
- Interactive 3D scatter for construct × archetype × state analysis
- Temporal trend animations

### Export & Reporting
- Automated briefing PDFs (state-specific scorecards)
- Excel workbook export with charts and pivot tables
- CSV batch export for analysis

---

## Architecture Notes

### Page Structure
Streamlit multi-page apps organize pages as:
```
app.py (home)
pages/
  1_*.py (appears as first page in nav)
  2_*.py (appears as second page in nav)
  etc.
```

Numeric prefixes control nav order. The emoji in the filename becomes the page icon.

### Session State
Some pages use `st.session_state` to track:
- Selected state/construct filters
- Message history (AI Search)
- Form inputs (Media Portal)

Session state persists across page navigation within one session.

### No External APIs
All pages use **synthetic demo data**. In production, integrate:
- Supabase REST API for survey responses
- Database queries for MrP estimates
- LLM APIs for AI features
- Media platform APIs for campaign management

---

## Testing & Validation

To test each page:

1. **Home Dashboard**: Load `app.py` → Verify KPI cards, nav cards, data table
2. **Survey Results**: Click through 6 tabs, change filters, inspect charts
3. **VIP Scores**: Select archetypes, view distributions, check persuasion pathways
4. **MrP Estimates**: Select state/construct, verify CI ranges, check heatmap
5. **Media Portal**: Fill campaign form, view demo campaigns, check spend tracker
6. **Survey Writer**: Generate questions, paste & rewrite, browse question bank
7. **AI Search**: Type or click suggested queries, inspect response formatting

---

## Troubleshooting

### Streamlit Won't Start
```bash
# Clear cache
rm -rf ~/.streamlit/
streamlit run app.py
```

### Page Navigation Not Working
- Ensure page filenames start with `1_`, `2_`, etc.
- Restart Streamlit: `Ctrl+C` and `streamlit run app.py`

### Auth Issues
- Check `auth.py` exists in same directory as `app.py`
- Verify secrets are configured in `.streamlit/secrets.toml`
- Use fallback demo credentials for testing

### Charts Not Rendering
- Verify Plotly is installed: `pip install plotly`
- Check browser console for JS errors
- Try different plot type (px.bar vs px.line)

---

## File Sizes & Performance

Current app footprint:
- `app.py`: ~3.5 KB
- `pages/1_Survey_Results.py`: ~13 KB
- `pages/2_VIP_Scores.py`: ~15 KB
- `pages/3_MrP_Estimates.py`: ~11 KB
- `pages/4_Media_Portal.py`: ~16 KB
- `pages/5_Survey_Writer.py`: ~14 KB
- `pages/6_AI_Search.py`: ~7 KB

**Total**: ~80 KB Python + ~30 KB CSS → **~110 KB app code**

Page load times with demo data: **500-800ms** (Streamlit overhead mostly).

With live database queries (Phase 2), optimize with:
- Caching (`@st.cache_data`)
- Pagination for large result sets
- Lazy-loaded charts (show summary first)

---

## Questions?

Refer to:
- Streamlit docs: https://docs.streamlit.io
- Project memory: `/sessions/intelligent-practical-johnson/mnt/.auto-memory/MEMORY.md`
- VIP framework: `VIP Framework Architecture (Apr 2026)` in project memory
