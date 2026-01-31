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
  - Reducto: PDF parsing (configured, ready for PDF-heavy sources)
  - Resend: Email delivery for executive briefings
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

### What's Been Implemented (Jan 31, 2026)
- [x] Dashboard with Run Now button and stats
- [x] Sources management (6 default tourism sources seeded)
- [x] Pipeline execution with Firecrawl integration
- [x] LLM classification with Emergent GPT-5.2
- [x] Executive brief generation with materiality scoring
- [x] Run metrics and logs viewer
- [x] Resend email integration (requires domain verification for production)
- [x] Dark professional UI theme ("Midnight Ops")

### API Endpoints
- `POST /api/run` - Trigger pipeline execution
- `GET /api/brief/latest` - Get latest executive brief
- `GET /api/sources` - List all sources
- `POST /api/sources` - Add new source
- `PATCH /api/sources/{id}` - Update source
- `DELETE /api/sources/{id}` - Delete source
- `GET /api/runs/latest` - Get latest run metrics
- `GET /api/logs/latest` - Get latest run logs
- `GET /api/stats` - Get platform statistics

### Prioritized Backlog
**P0 (Critical)**
- [ ] Domain verification for Resend to enable email delivery
- [ ] Add retry logic for LLM budget exceeded errors

**P1 (Important)**
- [ ] PDF parsing with Reducto for investor relations pages
- [ ] Scheduled pipeline runs (cron-based)
- [ ] Email brief template customization

**P2 (Nice to have)**
- [ ] Historical brief archive
- [ ] Source health monitoring
- [ ] Custom event type filters
- [ ] Export briefs to PDF

### Next Tasks
1. Verify Resend domain to enable multi-recipient emails
2. Add more tourism/hospitality sources
3. Implement scheduled pipeline runs
4. Add PDF parsing for investor relations content
