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

### What's Been Implemented (Feb 1, 2026)

#### Core Features
- [x] Dashboard with Run Now button and stats
- [x] Sources management (6 default tourism sources seeded)
- [x] Pipeline execution with Firecrawl integration
- [x] LLM classification with Emergent GPT-5.2
- [x] Executive brief generation
- [x] Run metrics and logs viewer
- [x] Resend email integration with verified domain (kirikomal.com)
- [x] New branded logo (blue-purple gradient with layers icon)

#### Agentic AI Module
- [x] AI-powered Insights page with expandable impact scenarios
- [x] Trend Forecasting page with expandable trend cards
- [x] Read More/Collapse functionality for dense content
- ~~Tasks/Action Items page~~ (Removed)
- ~~Approvals page~~ (Removed)
- ~~Brief Archive page~~ (Removed)

#### Reducto PDF Integration
- [x] Reducto API integrated for PDF processing
- [x] `POST /api/process-pdf` endpoint for on-demand PDF processing
- [x] `GET /api/reducto/status` endpoint to check configuration
- [x] Pipeline auto-detects PDF URLs and processes with Reducto

#### Other Features
- [x] Multi-recipient emails (domain kirikomal.com verified)
- [x] Scheduled Pipeline Runs (cron-based)
- [x] Source Health Monitoring
- [x] Export Briefs to PDF

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

#### Reducto PDF Endpoints
- `POST /api/process-pdf` - Process a PDF with Reducto
- `GET /api/reducto/status` - Check Reducto configuration

#### Scheduling Endpoints
- `GET /api/schedules` - List scheduled runs
- `POST /api/schedules` - Create scheduled run
- `PATCH /api/schedules/{id}` - Enable/disable schedule
- `DELETE /api/schedules/{id}` - Delete schedule

#### Health & Email Endpoints
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

**P0 (Critical)** - ✅ All Complete
- [x] Domain verification for Resend
- [x] PDF parsing with Reducto
- [x] Scheduled pipeline runs
- [x] Source health monitoring
- [x] Export briefs to PDF

**P1 (Important)**
- [ ] UI for scheduled runs management
- [ ] Email template customization UI
- [ ] Source health dashboard visualization

**P2 (Nice to have)**
- [ ] Real-time pipeline progress tracking
- [ ] Slack/Teams notifications
- [ ] Calendar integration for scheduled briefs
- [ ] Multi-language support

### Technical Notes
- Reducto SDK: Use `client.parse.run(input=url_string)` to parse PDFs
- Cron expressions validated with croniter library
- PDF export uses reportlab library
- All datetime values stored as ISO format strings
