# SafarAI - Competitive Intelligence Platform
## Product Requirements Document

### Original Problem Statement
SafarAI is an automated Competitive Intelligence and Deal Monitoring platform for the tourism and hospitality industry. It continuously monitors trusted tourism/travel websites, ingests HTML and PDFs, detects what is NEW or UPDATED since the last run, uses LLM reasoning to decide what matters, converts content into executive-grade intelligence, and delivers structured executive briefings via email.

### Architecture
- **Frontend**: React with Tailwind CSS, Shadcn/UI components
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (motor async driver)
- **Integrations**:
  - Firecrawl: Web crawling and content extraction
  - Reducto: PDF parsing for investor relations content
  - Resend: Email delivery for executive briefings (domain: kirikomal.com)
  - Emergent LLM (GPT-5.2): Content classification and intelligence extraction

### User Personas
1. **Tourism Executives** - Need daily competitive intelligence briefings
2. **Hospitality Analysts** - Monitor competitor partnerships and deals
3. **Destination Marketing Organizations** - Track industry funding and campaigns

### Core Requirements (Static)
1. Source management (add/remove/enable/disable)
2. Pipeline execution (crawl → classify → brief → email)
3. Change detection (NEW/UPDATED content only)
4. Executive brief generation (Top Movers, Partnerships, Funding, Campaigns)
5. Run health monitoring and logging
6. Email delivery of intelligence briefs

### What's Been Implemented (Feb 1, 2026)

#### Core Features
- [x] Dashboard with Run Now button and stats
- [x] Sources management (6 default tourism sources seeded)
- [x] Pipeline execution with Firecrawl integration
- [x] LLM classification with Emergent GPT-5.2
- [x] Executive brief generation with materiality scoring
- [x] Run metrics and logs viewer
- [x] Resend email integration with verified domain (kirikomal.com)
- [x] Dark professional UI theme ("Midnight Ops")

#### Agentic AI Module
- [x] AI-powered Insights page with:
  - Impact scenarios with probability/confidence scores
  - Key findings visualization
  - Risk alerts and opportunities detection
  - Dashboard recommendations
- [x] Trend Forecasting page with:
  - Category filtering (Partnerships, Funding, Pricing, Technology, Destinations)
  - Visual confidence gauges
  - Key indicators and recommended actions
- [x] Removed: Tasks/Action Items page
- [x] Removed: Approvals page

#### New Features (Feb 1, 2026)
- [x] **Multi-recipient emails**: Domain kirikomal.com verified, supports multiple recipients
- [x] **PDF Parsing with Reducto**: Automatically processes PDF links from sources
- [x] **Scheduled Pipeline Runs**: Cron-based scheduling (e.g., "0 9 * * *" for daily 9 AM)
- [x] **Historical Brief Archive**: Browse and view past intelligence briefs
- [x] **Source Health Monitoring**: Track success rates and response times per source
- [x] **Export Briefs to PDF**: Download any brief as a formatted PDF document

### API Endpoints

#### Core Endpoints
- `POST /api/run` - Trigger pipeline execution
- `GET /api/brief/latest` - Get latest executive brief
- `GET /api/sources` - List all sources
- `POST /api/sources` - Add new source
- `PATCH /api/sources/{id}` - Update source
- `DELETE /api/sources/{id}` - Delete source
- `GET /api/runs/latest` - Get latest run metrics
- `GET /api/logs/latest` - Get latest run logs
- `GET /api/stats` - Get platform statistics

#### Agentic AI Endpoints
- `GET /api/agentic/insights/latest` - Get latest AI insights
- `POST /api/agentic/generate` - Generate new insights
- `GET /api/trends` - Get trend forecasts
- `GET /api/team` - Get team members

#### New Endpoints (Feb 1, 2026)
- `GET /api/briefs` - List all historical briefs
- `GET /api/brief/{id}` - Get specific brief by ID
- `GET /api/brief/{id}/pdf` - Export brief to PDF
- `GET /api/schedules` - List scheduled runs
- `POST /api/schedules` - Create scheduled run
- `PATCH /api/schedules/{id}` - Enable/disable schedule
- `DELETE /api/schedules/{id}` - Delete schedule
- `GET /api/sources/health` - Get source health metrics
- `GET /api/email/config` - Get email configuration
- `POST /api/email/test` - Send test email

### Database Collections
- `sources` - Monitored websites
- `items` - Crawled content
- `events` - Classified intelligence events
- `runs` - Pipeline execution records
- `run_logs` - Detailed execution logs
- `briefs` - Generated executive briefs
- `team_members` - Team member profiles
- `agentic_insights` - AI-generated insights
- `trend_forecasts` - Predicted trends
- `scheduled_runs` - Cron schedule configurations
- `source_health` - Source performance metrics

### Prioritized Backlog

**P0 (Critical)**
- [x] Domain verification for Resend ✓ (kirikomal.com)
- [x] PDF parsing with Reducto ✓
- [x] Scheduled pipeline runs ✓
- [x] Historical brief archive ✓
- [x] Source health monitoring ✓
- [x] Export briefs to PDF ✓

**P1 (Important)**
- [ ] Email brief template customization UI
- [ ] Real-time pipeline progress tracking
- [ ] Add more tourism/hospitality sources

**P2 (Nice to have)**
- [ ] Custom event type filters
- [ ] Integration with Slack/Teams
- [ ] Calendar integration for scheduled briefs
- [ ] Multi-language support

### Next Tasks
1. Add UI for scheduled runs management
2. Add UI for source health dashboard
3. Email template editor

### Technical Notes
- Cron expressions use croniter library for validation
- PDF generation uses reportlab library
- Source health is logged after each pipeline run
- All datetime values stored as ISO format strings
