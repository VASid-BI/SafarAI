from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import asyncio
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import resend
from firecrawl import FirecrawlApp
from reducto import Reducto

# Import agentic modules
from agentic_models import (
    TeamMember, TeamMemberCreate, ActionItem, ActionItemUpdate,
    Approval, TrendForecast, AgenticInsight
)
from agentic_engine import generate_agentic_insights

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize APIs
resend.api_key = os.environ.get('RESEND_API_KEY', '')
firecrawl = FirecrawlApp(api_key=os.environ.get('FIRECRAWL_API_KEY', ''))
reducto_client = Reducto(api_key=os.environ.get('REDUCTO_API_KEY', ''))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="SafarAI Intelligence Platform")
api_router = APIRouter(prefix="/api")

# ========================
# PYDANTIC MODELS
# ========================

class Source(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    category: str = "general"
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SourceCreate(BaseModel):
    name: str
    url: str
    category: str = "general"
    active: bool = True

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    active: Optional[bool] = None

class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    url: str
    title: str
    content_text: str
    content_type: str = "html"
    content_hash: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    item_id: str
    company: str
    event_type: str
    title: str
    summary: str
    why_it_matters: str
    materiality_score: int = 0
    confidence: float = 0.0
    key_entities: Dict[str, Any] = {}
    evidence_quotes: List[str] = []
    source_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Run(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    status: str = "running"
    sources_total: int = 0
    sources_ok: int = 0
    sources_failed: int = 0
    items_total: int = 0
    items_new: int = 0
    items_updated: int = 0
    items_unchanged: int = 0
    events_created: int = 0
    emails_sent: int = 0

class RunLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    level: str = "info"
    message: str
    meta: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScheduledRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cron_expression: str  # e.g., "0 9 * * *" (9 AM daily)
    name: str = "Daily Run"
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScheduledRunCreate(BaseModel):
    cron_expression: str
    name: str = "Daily Run"
    enabled: bool = True

class SourceHealth(BaseModel):
    source_id: str
    source_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_error: Optional[str] = None

# ========================
# DEFAULT SOURCES
# ========================

DEFAULT_SOURCES = [
    {"name": "Marriott News", "url": "https://news.marriott.com/", "category": "hotel"},
    {"name": "Hilton Stories", "url": "https://stories.hilton.com/", "category": "hotel"},
    {"name": "Airbnb News", "url": "https://news.airbnb.com/", "category": "accommodation"},
    {"name": "Reuters Business", "url": "https://www.reuters.com/business/", "category": "news"},
    {"name": "US Travel Association", "url": "https://www.ustravel.org/", "category": "association"},
    {"name": "TravelZoo", "url": "https://www.travelzoo.com/", "category": "deals"},
]

# Keywords for link filtering
KEYWORDS = [
    "press", "news", "blog", "partnership", "partner", "alliance", "collaboration",
    "funding", "investment", "acquisition", "campaign", "deal", "package", "offer",
    "discount", "promotion", "vacation", "resort", "special offer", "announcement"
]

# Blocked domains (social media, etc.)
BLOCKED_DOMAINS = [
    "facebook.com", "twitter.com", "instagram.com", "linkedin.com", 
    "youtube.com", "tiktok.com", "pinterest.com", "x.com"
]

# ========================
# UTILITY FUNCTIONS
# ========================

def compute_hash(content: str) -> str:
    return hashlib.sha256(content[:12000].encode()).hexdigest()

def filter_link(url: str) -> bool:
    url_lower = url.lower()
    # Block social media domains
    if any(domain in url_lower for domain in BLOCKED_DOMAINS):
        return False
    return any(kw in url_lower for kw in KEYWORDS)

async def log_run(run_id: str, level: str, message: str, meta: dict = None):
    log = RunLog(run_id=run_id, level=level, message=message, meta=meta or {})
    doc = log.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.run_logs.insert_one(doc)
    if level == "error":
        logger.error(f"[{run_id}] {message}")
    else:
        logger.info(f"[{run_id}] {message}")

# ========================
# LLM CLASSIFICATION
# ========================

async def classify_content(content: str, url: str, title: str) -> Optional[Dict]:
    """Use Emergent LLM to classify content into structured intelligence."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        system_prompt = """You are a competitive intelligence analyst for the tourism and hospitality industry.
Analyze the provided content and extract structured intelligence.
You MUST return ONLY valid JSON with NO markdown formatting, NO code blocks, NO explanation.

Return this exact JSON structure:
{
  "company": "string - company name mentioned",
  "event_type": "one of: partnership | funding | campaign_deal | pricing_change | acquisition | hiring_exec | other",
  "title": "string - brief title of the event",
  "summary": "1-2 sentences summarizing the key information",
  "why_it_matters": "1-2 sentences explaining relevance to tourism executives",
  "materiality_score": 0-100 integer indicating business impact,
  "confidence": 0-1 float indicating extraction confidence,
  "key_entities": {
    "partners": [],
    "campaigns": [],
    "packages": [],
    "discounts": [],
    "locations": [],
    "amounts": [],
    "dates": []
  },
  "evidence_quotes": ["2-3 short snippets from the content"],
  "source_url": "the source url"
}

If content is not relevant to tourism/hospitality intelligence, return null."""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"classify-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"URL: {url}\nTitle: {title}\n\nContent:\n{content[:8000]}"
        )
        
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.lower() == "null" or not response_text:
            return None
        
        # Clean up response if it has markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip() if end > start else response_text
        elif response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        # Find JSON object in response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        result = json.loads(response_text)
        result["source_url"] = url
        return result
        
    except Exception as e:
        logger.error(f"LLM classification error: {e}")
        return None

# ========================
# EMAIL BRIEF GENERATION
# ========================

def generate_html_brief(events: List[Dict], run: Dict) -> str:
    """Generate stunning black & white HTML executive briefing email."""
    
    top_movers = [e for e in events if e.get('materiality_score', 0) >= 70]
    partnerships = [e for e in events if e.get('event_type') == 'partnership']
    funding = [e for e in events if e.get('event_type') == 'funding']
    campaigns = [e for e in events if e.get('event_type') == 'campaign_deal']
    
    def event_card(event: Dict) -> str:
        event_type = event.get('event_type', 'other').replace('_', ' ').upper()
        
        quotes_html = ""
        for quote in event.get('evidence_quotes', [])[:2]:
            quotes_html += f'''
            <div style="border-left:2px solid #333;padding-left:16px;margin:16px 0;">
                <p style="font-style:italic;color:#888;font-size:13px;margin:0;line-height:1.6;">"{quote[:150]}..."</p>
            </div>
            '''
        
        return f'''
        <div style="background:#0a0a0a;border-radius:12px;padding:28px;margin-bottom:16px;border:1px solid #1a1a1a;border-left:3px solid #fff;">
            <div style="margin-bottom:20px;">
                <span style="background:#fff;color:#000;padding:6px 16px;border-radius:100px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">
                    {event_type}
                </span>
            </div>
            <h3 style="color:#fff;margin:0 0 12px 0;font-size:22px;font-weight:600;line-height:1.3;">{event.get('title', 'N/A')}</h3>
            <p style="color:#666;font-size:14px;margin:0 0 16px 0;text-transform:uppercase;letter-spacing:0.5px;">{event.get('company', 'Unknown Company')}</p>
            <p style="color:#aaa;font-size:15px;margin:0 0 20px 0;line-height:1.7;">{event.get('summary', '')}</p>
            
            <div style="background:#111;border-radius:8px;padding:20px;margin:20px 0;border:1px solid #222;">
                <p style="color:#fff;font-size:11px;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:1px;opacity:0.5;">Why It Matters</p>
                <p style="color:#ccc;font-size:14px;margin:0;line-height:1.6;">{event.get('why_it_matters', '')}</p>
            </div>
            
            {quotes_html}
            
            <div style="margin-top:20px;padding-top:20px;border-top:1px solid #222;">
                <a href="{event.get('source_url', '#')}" style="color:#fff;font-size:12px;text-decoration:none;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">
                    View Source →
                </a>
            </div>
        </div>
        '''
    
    def section(title: str, items: List[Dict]) -> str:
        if not items:
            return ""
        cards = "".join(event_card(e) for e in items[:5])
        return f'''
        <div style="margin-bottom:48px;">
            <div style="margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #222;">
                <h2 style="color:#fff;font-size:14px;margin:0;font-weight:600;text-transform:uppercase;letter-spacing:2px;">{title}</h2>
                <p style="color:#555;font-size:12px;margin:8px 0 0 0;">{len(items)} item{'s' if len(items) != 1 else ''}</p>
            </div>
            {cards}
        </div>
        '''
    
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    time_now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    total_events = len(events)
    high_priority = len([e for e in events if e.get('materiality_score', 0) >= 70])
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body style="font-family:'Space Grotesk',-apple-system,sans-serif;background:#000;margin:0;padding:0;color:#fff;">
        <div style="max-width:680px;margin:0 auto;">
            
            <!-- Header -->
            <div style="padding:60px 40px;text-align:center;border-bottom:1px solid #1a1a1a;">
                <div style="width:64px;height:64px;border-radius:16px;background:#fff;margin:0 auto 24px;display:flex;align-items:center;justify-content:center;">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="2" y1="12" x2="22" y2="12"></line>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                    </svg>
                </div>
                <h1 style="color:#fff;font-size:32px;margin:0 0 8px 0;font-weight:700;letter-spacing:-1px;">
                    SAFAR<span style="opacity:0.4;">AI</span>
                </h1>
                <p style="color:#555;font-size:11px;margin:0 0 32px 0;text-transform:uppercase;letter-spacing:4px;">
                    Intelligence Brief
                </p>
                <div style="display:inline-block;background:#0a0a0a;padding:12px 28px;border-radius:100px;border:1px solid #1a1a1a;">
                    <p style="color:#888;font-size:13px;margin:0;">{today} · {time_now}</p>
                </div>
            </div>
            
            <!-- Stats Bar -->
            <div style="display:flex;border-bottom:1px solid #1a1a1a;">
                <div style="flex:1;padding:32px;text-align:center;border-right:1px solid #1a1a1a;">
                    <p style="color:#fff;font-size:36px;font-weight:700;margin:0;font-family:monospace;">{total_events}</p>
                    <p style="color:#555;font-size:10px;margin:8px 0 0 0;text-transform:uppercase;letter-spacing:1px;">Events</p>
                </div>
                <div style="flex:1;padding:32px;text-align:center;border-right:1px solid #1a1a1a;">
                    <p style="color:#fff;font-size:36px;font-weight:700;margin:0;font-family:monospace;">{high_priority}</p>
                    <p style="color:#555;font-size:10px;margin:8px 0 0 0;text-transform:uppercase;letter-spacing:1px;">High Priority</p>
                </div>
                <div style="flex:1;padding:32px;text-align:center;">
                    <p style="color:#fff;font-size:36px;font-weight:700;margin:0;font-family:monospace;">{run.get('sources_ok', 0)}/{run.get('sources_total', 0)}</p>
                    <p style="color:#555;font-size:10px;margin:8px 0 0 0;text-transform:uppercase;letter-spacing:1px;">Sources</p>
                </div>
            </div>
            
            <!-- Main Content -->
            <div style="padding:48px 40px;">
                {section("Top Movers", top_movers)}
                {section("Partnerships", partnerships)}
                {section("Funding", funding)}
                {section("Campaigns & Deals", campaigns)}
            </div>
            
            <!-- Pipeline Health -->
            <div style="padding:40px;background:#0a0a0a;border-top:1px solid #1a1a1a;">
                <p style="color:#555;font-size:10px;margin:0 0 20px 0;text-transform:uppercase;letter-spacing:2px;">Pipeline Health</p>
                <div style="display:flex;gap:16px;">
                    <div style="flex:1;background:#111;padding:20px;border-radius:8px;border:1px solid #1a1a1a;">
                        <p style="color:#555;font-size:10px;margin:0 0 8px 0;text-transform:uppercase;">Status</p>
                        <p style="color:{'#fff' if run.get('status') == 'success' else '#888'};font-size:14px;margin:0;font-weight:600;">
                            {run.get('status', 'unknown').upper()}
                        </p>
                    </div>
                    <div style="flex:1;background:#111;padding:20px;border-radius:8px;border:1px solid #1a1a1a;">
                        <p style="color:#555;font-size:10px;margin:0 0 8px 0;text-transform:uppercase;">New</p>
                        <p style="color:#fff;font-size:14px;margin:0;font-weight:600;">{run.get('items_new', 0)}</p>
                    </div>
                    <div style="flex:1;background:#111;padding:20px;border-radius:8px;border:1px solid #1a1a1a;">
                        <p style="color:#555;font-size:10px;margin:0 0 8px 0;text-transform:uppercase;">Updated</p>
                        <p style="color:#fff;font-size:14px;margin:0;font-weight:600;">{run.get('items_updated', 0)}</p>
                    </div>
                    <div style="flex:1;background:#111;padding:20px;border-radius:8px;border:1px solid #1a1a1a;">
                        <p style="color:#555;font-size:10px;margin:0 0 8px 0;text-transform:uppercase;">Events</p>
                        <p style="color:#fff;font-size:14px;margin:0;font-weight:600;">{run.get('events_created', 0)}</p>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="padding:40px;text-align:center;border-top:1px solid #1a1a1a;">
                <p style="color:#444;font-size:12px;margin:0;">
                    Powered by <strong style="color:#888;">SafarAI</strong>
                </p>
                <p style="color:#333;font-size:10px;margin:8px 0 0 0;text-transform:uppercase;letter-spacing:1px;">
                    Tourism & Hospitality Intelligence
                </p>
            </div>
            
        </div>
    </body>
    </html>
    '''
    
    return html

async def send_brief_email(html_content: str, run: Dict) -> bool:
    """Send executive briefing via Resend."""
    try:
        recipients = os.environ.get('SAFARAI_RECIPIENTS', '').split(',')
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if not recipients:
            logger.warning("No recipients configured for email")
            return False
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        params = {
            "from": os.environ.get('SAFARAI_FROM_EMAIL', 'onboarding@resend.dev'),
            "to": recipients,
            "subject": f"Daily Competitive Intel Brief — {today}",
            "html": html_content
        }
        
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent successfully: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# ========================
# PIPELINE EXECUTION
# ========================

async def run_pipeline(run_id: str):
    """Execute the full intelligence pipeline."""
    
    await log_run(run_id, "info", "Starting pipeline execution")
    
    # Get active sources
    sources = await db.sources.find({"active": True}, {"_id": 0}).to_list(100)
    
    run_data = {
        "sources_total": len(sources),
        "sources_ok": 0,
        "sources_failed": 0,
        "items_total": 0,
        "items_new": 0,
        "items_updated": 0,
        "items_unchanged": 0,
        "events_created": 0
    }
    
    all_events = []
    
    for source in sources:
        source_id = source['id']
        source_url = source['url']
        source_name = source['name']
        
        await log_run(run_id, "info", f"Processing source: {source_name}", {"url": source_url})
        
        start_time = datetime.now(timezone.utc)
        source_success = False
        source_error = None
        
        try:
            # Check if URL is a PDF
            is_pdf = source_url.lower().endswith('.pdf')
            
            if is_pdf:
                # Use Reducto for PDF parsing
                await log_run(run_id, "info", f"Processing PDF with Reducto: {source_name}")
                try:
                    pdf_result = await asyncio.to_thread(
                        reducto_client.parse,
                        document_url=source_url
                    )
                    markdown = pdf_result.to_markdown() if hasattr(pdf_result, 'to_markdown') else str(pdf_result)
                    title = source_name
                    links = []
                except Exception as pdf_error:
                    await log_run(run_id, "warn", f"PDF parsing failed, trying Firecrawl: {pdf_error}")
                    # Fallback to Firecrawl for PDFs
                    crawl_result = await asyncio.to_thread(
                        firecrawl.scrape,
                        source_url,
                        formats=['markdown']
                    )
                    markdown = crawl_result.markdown if hasattr(crawl_result, 'markdown') else crawl_result.get('markdown', '')
                    title = source_name
                    links = []
            else:
                # Crawl with Firecrawl for HTML pages
                crawl_result = await asyncio.to_thread(
                    firecrawl.scrape,
                    source_url,
                    formats=['markdown', 'links']
                )
                
                if not crawl_result:
                    raise Exception("Empty crawl result")
                
                # Handle Firecrawl Document object
                if hasattr(crawl_result, 'markdown'):
                    markdown = crawl_result.markdown or ''
                    title = getattr(crawl_result.metadata, 'title', source_name) if hasattr(crawl_result, 'metadata') and crawl_result.metadata else source_name
                    links = getattr(crawl_result, 'links', []) or []
                else:
                    # Fallback for dict response
                    markdown = crawl_result.get('markdown', '')
                    title = crawl_result.get('metadata', {}).get('title', source_name)
                    links = crawl_result.get('links', [])
            
            # Filter links for PDFs and relevant content
            filtered_links = []
            for link in links:
                if filter_link(link):
                    filtered_links.append(link)
                elif link.lower().endswith('.pdf'):
                    filtered_links.append(link)
            filtered_links = filtered_links[:8]
            
            await log_run(run_id, "info", f"Found {len(filtered_links)} relevant links from {source_name}")
            
            # Process main page
            content_hash = compute_hash(markdown)
            
            existing = await db.items.find_one({"url": source_url}, {"_id": 0})
            
            is_new = existing is None
            is_updated = existing and existing.get('content_hash') != content_hash
            
            if is_new or is_updated:
                item = Item(
                    source_id=source_id,
                    url=source_url,
                    title=title,
                    content_text=markdown[:50000],
                    content_type="html",
                    content_hash=content_hash
                )
                
                item_doc = item.model_dump()
                item_doc['fetched_at'] = item_doc['fetched_at'].isoformat()
                item_doc['last_seen_at'] = item_doc['last_seen_at'].isoformat()
                
                if is_new:
                    await db.items.insert_one(item_doc)
                    run_data['items_new'] += 1
                else:
                    await db.items.update_one(
                        {"url": source_url},
                        {"$set": item_doc}
                    )
                    run_data['items_updated'] += 1
                
                # Classify content with LLM
                classification = await classify_content(markdown, source_url, title)
                
                if classification:
                    event = Event(
                        run_id=run_id,
                        item_id=item.id,
                        **classification
                    )
                    event_doc = event.model_dump()
                    event_doc['created_at'] = event_doc['created_at'].isoformat()
                    await db.events.insert_one(event_doc)
                    all_events.append(event_doc)
                    run_data['events_created'] += 1
            else:
                run_data['items_unchanged'] += 1
                await db.items.update_one(
                    {"url": source_url},
                    {"$set": {"last_seen_at": datetime.now(timezone.utc).isoformat()}}
                )
            
            run_data['items_total'] += 1
            
            # Process child links (limit to 3 per source to stay within limits)
            for link_url in filtered_links[:3]:
                try:
                    link_result = await asyncio.to_thread(
                        firecrawl.scrape,
                        link_url,
                        formats=['markdown']
                    )
                    
                    if link_result:
                        # Handle Firecrawl Document object
                        if hasattr(link_result, 'markdown'):
                            link_markdown = link_result.markdown or ''
                            link_title = getattr(link_result.metadata, 'title', link_url) if hasattr(link_result, 'metadata') and link_result.metadata else link_url
                        else:
                            # Fallback for dict response
                            link_markdown = link_result.get('markdown', '')
                            link_title = link_result.get('metadata', {}).get('title', link_url)
                        link_hash = compute_hash(link_markdown)
                        
                        link_existing = await db.items.find_one({"url": link_url}, {"_id": 0})
                        link_is_new = link_existing is None
                        link_is_updated = link_existing and link_existing.get('content_hash') != link_hash
                        
                        if link_is_new or link_is_updated:
                            link_item = Item(
                                source_id=source_id,
                                url=link_url,
                                title=link_title,
                                content_text=link_markdown[:50000],
                                content_type="html",
                                content_hash=link_hash
                            )
                            
                            link_doc = link_item.model_dump()
                            link_doc['fetched_at'] = link_doc['fetched_at'].isoformat()
                            link_doc['last_seen_at'] = link_doc['last_seen_at'].isoformat()
                            
                            if link_is_new:
                                await db.items.insert_one(link_doc)
                                run_data['items_new'] += 1
                            else:
                                await db.items.update_one({"url": link_url}, {"$set": link_doc})
                                run_data['items_updated'] += 1
                            
                            # Classify link content
                            link_classification = await classify_content(link_markdown, link_url, link_title)
                            
                            if link_classification:
                                link_event = Event(
                                    run_id=run_id,
                                    item_id=link_item.id,
                                    **link_classification
                                )
                                link_event_doc = link_event.model_dump()
                                link_event_doc['created_at'] = link_event_doc['created_at'].isoformat()
                                await db.events.insert_one(link_event_doc)
                                all_events.append(link_event_doc)
                                run_data['events_created'] += 1
                        else:
                            run_data['items_unchanged'] += 1
                        
                        run_data['items_total'] += 1
                        
                except Exception as link_error:
                    await log_run(run_id, "warn", f"Failed to process link: {link_url}", {"error": str(link_error)})
            
            run_data['sources_ok'] += 1
            source_success = True
            
        except Exception as e:
            run_data['sources_failed'] += 1
            source_error = str(e)
            await log_run(run_id, "error", f"Failed to process source: {source_name}", {"error": str(e)})
        
        # Log source health
        end_time = datetime.now(timezone.utc)
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        health_doc = {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "source_name": source_name,
            "run_id": run_id,
            "success": source_success,
            "error": source_error,
            "response_time_ms": response_time_ms,
            "checked_at": end_time.isoformat()
        }
        await db.source_health.insert_one(health_doc)
    
    # Determine final status
    if run_data['sources_failed'] == 0:
        status = "success"
    elif run_data['sources_ok'] > 0:
        status = "partial_failure"
    else:
        status = "failure"
    
    # Generate and send brief
    emails_sent = 0
    if all_events:
        run_data_for_brief = {**run_data, "status": status}
        html_brief = generate_html_brief(all_events, run_data_for_brief)
        
        # Clean events for brief (remove MongoDB _id)
        clean_events = [{k: v for k, v in e.items() if k != '_id'} for e in all_events]
        
        # Store brief
        brief_doc = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "html": html_brief,
            "events": clean_events,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.briefs.insert_one(brief_doc)
        
        # Send email
        if await send_brief_email(html_brief, run_data_for_brief):
            emails_sent = 1
    else:
        # If no new events, send the latest available brief
        await log_run(run_id, "info", "No new events detected, sending latest available brief")
        latest_brief = await db.briefs.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
        if latest_brief:
            # Send the latest brief with current run stats
            run_data_for_brief = {**run_data, "status": status}
            if await send_brief_email(latest_brief['html'], run_data_for_brief):
                emails_sent = 1
                await log_run(run_id, "info", f"Sent latest brief from {latest_brief['created_at']}")
    
    # Update run record
    await db.runs.update_one(
        {"id": run_id},
        {"$set": {
            **run_data,
            "status": status,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "emails_sent": emails_sent
        }}
    )
    
    # Generate agentic insights if events were created
    if all_events and len(all_events) > 0:
        await log_run(run_id, "info", f"Generating agentic insights for {len(all_events)} events")
        try:
            team_members = await db.team_members.find({}, {"_id": 0}).to_list(100)
            insight_id = await generate_agentic_insights(
                run_id=run_id,
                events=all_events,
                run_data=run_data,
                team_members=team_members,
                db=db
            )
            if insight_id:
                await log_run(run_id, "info", f"Agentic insights generated: {insight_id}")
            else:
                await log_run(run_id, "warn", "Failed to generate agentic insights")
        except Exception as e:
            await log_run(run_id, "error", f"Agentic insights error: {str(e)}")
    
    await log_run(run_id, "info", f"Pipeline completed with status: {status}", run_data)

# ========================
# API ENDPOINTS
# ========================

@api_router.get("/")
async def root():
    return {"message": "SafarAI Intelligence Platform API"}

@api_router.post("/run")
async def trigger_run(background_tasks: BackgroundTasks):
    """Trigger a new intelligence pipeline run."""
    run = Run()
    run_doc = run.model_dump()
    run_doc['started_at'] = run_doc['started_at'].isoformat()
    await db.runs.insert_one(run_doc)
    
    background_tasks.add_task(run_pipeline, run.id)
    
    return {"run_id": run.id, "status": "started", "message": "Pipeline execution started"}

@api_router.get("/brief/latest")
async def get_latest_brief():
    """Get the most recent executive briefing."""
    brief = await db.briefs.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not brief:
        return {"message": "No briefs available yet", "brief": None}
    return brief

@api_router.get("/sources")
async def list_sources():
    """List all configured sources."""
    sources = await db.sources.find({}, {"_id": 0}).to_list(100)
    return {"sources": sources}

@api_router.post("/sources")
async def create_source(source_data: SourceCreate):
    """Add a new source to monitor."""
    source = Source(**source_data.model_dump())
    doc = source.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.sources.insert_one(doc)
    return source

@api_router.patch("/sources/{source_id}")
async def update_source(source_id: str, update_data: SourceUpdate):
    """Update source configuration."""
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.sources.update_one({"id": source_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    
    updated = await db.sources.find_one({"id": source_id}, {"_id": 0})
    return updated

@api_router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a source."""
    result = await db.sources.delete_one({"id": source_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"message": "Source deleted"}

@api_router.get("/runs/latest")
async def get_latest_run():
    """Get the most recent run details."""
    run = await db.runs.find_one({}, {"_id": 0}, sort=[("started_at", -1)])
    if not run:
        return {"message": "No runs yet", "run": None}
    return run

@api_router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get a specific run by ID."""
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@api_router.get("/logs/latest")
async def get_latest_logs():
    """Get logs from the most recent run."""
    latest_run = await db.runs.find_one({}, {"_id": 0}, sort=[("started_at", -1)])
    if not latest_run:
        return {"logs": [], "message": "No runs yet"}
    
    logs = await db.run_logs.find(
        {"run_id": latest_run['id']},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return {"run_id": latest_run['id'], "logs": logs}

@api_router.get("/logs/{run_id}")
async def get_run_logs(run_id: str):
    """Get logs for a specific run."""
    logs = await db.run_logs.find(
        {"run_id": run_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return {"run_id": run_id, "logs": logs}

@api_router.get("/stats")
async def get_stats():
    """Get overall platform statistics."""
    total_sources = await db.sources.count_documents({})
    active_sources = await db.sources.count_documents({"active": True})
    total_runs = await db.runs.count_documents({})
    total_events = await db.events.count_documents({})
    total_items = await db.items.count_documents({})
    
    latest_run = await db.runs.find_one({}, {"_id": 0}, sort=[("started_at", -1)])
    
    return {
        "total_sources": total_sources,
        "active_sources": active_sources,
        "total_runs": total_runs,
        "total_events": total_events,
        "total_items": total_items,
        "latest_run": latest_run
    }

# ========================
# AGENTIC AI ENDPOINTS
# ========================

# Team Management
@api_router.get("/team")
async def get_team():
    """Get all team members"""
    members = await db.team_members.find({}, {"_id": 0}).to_list(100)
    return {"team_members": members}

@api_router.post("/team")
async def add_team_member(member_data: TeamMemberCreate):
    """Add a new team member"""
    member = TeamMember(**member_data.model_dump())
    doc = member.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.team_members.insert_one(doc)
    return member

# Action Items
@api_router.get("/action-items")
async def get_action_items(status: Optional[str] = None, run_id: Optional[str] = None):
    """Get action items with optional filtering"""
    query = {}
    if status:
        query["status"] = status
    if run_id:
        query["run_id"] = run_id
    
    items = await db.action_items.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"action_items": items}

@api_router.post("/action-items/{item_id}/complete")
async def complete_action_item(item_id: str, update_data: ActionItemUpdate):
    """Mark action item as complete or update status"""
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict.get("status") == "completed":
        update_dict["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.action_items.update_one({"id": item_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    updated = await db.action_items.find_one({"id": item_id}, {"_id": 0})
    return updated

# Approvals
@api_router.get("/approvals")
async def get_approvals(status: Optional[str] = "pending"):
    """Get approval requests"""
    query = {"status": status} if status else {}
    approvals = await db.approvals.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"approvals": approvals}

@api_router.post("/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, background_tasks: BackgroundTasks):
    """Approve and execute an action"""
    approval = await db.approvals.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")
    
    # Update approval status
    await db.approvals.update_one(
        {"id": approval_id},
        {"$set": {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Execute action in background
    action_type = approval["action_type"]
    parameters = approval["parameters"]
    
    # Add execution logic based on action type
    if action_type == "send_email":
        # Queue email sending
        logger.info(f"Executing send_email action: {parameters}")
    elif action_type == "add_source":
        # Add source to monitoring
        source_data = parameters
        source = Source(**source_data)
        doc = source.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.sources.insert_one(doc)
    elif action_type == "export_csv":
        # Export data to CSV
        logger.info(f"Executing export_csv action: {parameters}")
    
    # Mark as executed
    await db.approvals.update_one(
        {"id": approval_id},
        {"$set": {
            "status": "executed",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Action approved and executed", "action_type": action_type}

@api_router.post("/approvals/{approval_id}/reject")
async def reject_action(approval_id: str):
    """Reject an approval request"""
    result = await db.approvals.update_one(
        {"id": approval_id, "status": "pending"},
        {"$set": {
            "status": "rejected",
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pending approval not found")
    
    return {"message": "Action rejected"}

# Insights
@api_router.get("/agentic/insights/latest")
async def get_latest_insights():
    """Get latest agentic insights"""
    insight = await db.agentic_insights.find_one({}, {"_id": 0}, sort=[("generated_at", -1)])
    if not insight:
        return {"message": "No insights available yet", "insight": None}
    return insight

@api_router.get("/agentic/insights/{run_id}")
async def get_insights_by_run(run_id: str):
    """Get insights for a specific run"""
    insight = await db.agentic_insights.find_one({"run_id": run_id}, {"_id": 0})
    if not insight:
        raise HTTPException(status_code=404, detail="Insights not found for this run")
    return insight

@api_router.post("/agentic/generate")
async def generate_insights_endpoint(background_tasks: BackgroundTasks):
    """Generate agentic insights for the latest run"""
    # Get latest run
    latest_run = await db.runs.find_one({}, {"_id": 0}, sort=[("started_at", -1)])
    if not latest_run:
        raise HTTPException(status_code=404, detail="No runs found")
    
    # Get events for this run (or from latest brief if no events in run)
    events = await db.events.find({"run_id": latest_run['id']}, {"_id": 0}).to_list(1000)
    
    # If no events for latest run, use all available events
    if not events:
        logger.warning(f"No events for run {latest_run['id']}, using all available events")
        events = await db.events.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    
    if not events:
        raise HTTPException(status_code=400, detail="No events available in database")
    
    # Get team members
    team_members = await db.team_members.find({}, {"_id": 0}).to_list(100)
    
    # Generate insights
    insight_id = await generate_agentic_insights(
        run_id=latest_run['id'],
        events=events,
        run_data=latest_run,
        team_members=team_members,
        db=db
    )
    
    if not insight_id:
        raise HTTPException(status_code=500, detail="Failed to generate insights")
    
    return {
        "message": "Agentic insights generated successfully",
        "insight_id": insight_id,
        "run_id": latest_run['id'],
        "events_analyzed": len(events)
    }

# Trends
@api_router.get("/trends")
async def get_trends(run_id: Optional[str] = None):
    """Get trend forecasts"""
    query = {"run_id": run_id} if run_id else {}
    trends = await db.trend_forecasts.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"trends": trends}

# ========================
# BRIEFS ARCHIVE ENDPOINTS
# ========================

@api_router.get("/briefs")
async def list_briefs(limit: int = 50):
    """Get all historical briefs"""
    briefs = await db.briefs.find({}, {"_id": 0, "html": 0}).sort("created_at", -1).to_list(limit)
    return {"briefs": briefs}

@api_router.get("/brief/{brief_id}")
async def get_brief_by_id(brief_id: str):
    """Get a specific brief by ID"""
    brief = await db.briefs.find_one({"id": brief_id}, {"_id": 0})
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief

@api_router.get("/brief/{brief_id}/pdf")
async def export_brief_to_pdf(brief_id: str):
    """Export brief to PDF"""
    try:
        # Get brief
        brief = await db.briefs.find_one({"id": brief_id}, {"_id": 0})
        if not brief:
            raise HTTPException(status_code=404, detail="Brief not found")
        
        # Use weasyprint or return HTML for client-side PDF
        # For now, return HTML that can be printed/saved as PDF
        html_content = brief.get('html', '')
        
        # Create a downloadable PDF using reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Heading1']
        story.append(Paragraph("SafarAI Intelligence Brief", title_style))
        story.append(Spacer(1, 12))
        
        # Date
        date_str = brief.get('created_at', 'Unknown')
        story.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        story.append(Spacer(1, 24))
        
        # Events
        events = brief.get('events', [])
        for event in events[:20]:
            event_type = event.get('event_type', 'other').replace('_', ' ').upper()
            story.append(Paragraph(f"<b>[{event_type}]</b> {event.get('title', 'N/A')}", styles['Heading3']))
            story.append(Paragraph(f"Company: {event.get('company', 'Unknown')}", styles['Normal']))
            story.append(Paragraph(f"{event.get('summary', '')}", styles['Normal']))
            story.append(Paragraph(f"<i>Why it matters:</i> {event.get('why_it_matters', '')}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=intel-brief-{brief_id[:8]}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

# ========================
# SCHEDULED RUNS ENDPOINTS
# ========================

# Global scheduler state
scheduler_running = False
scheduler_task = None

async def check_scheduled_runs():
    """Background task to check and execute scheduled runs"""
    global scheduler_running
    while scheduler_running:
        try:
            now = datetime.now(timezone.utc)
            schedules = await db.scheduled_runs.find({"enabled": True}, {"_id": 0}).to_list(100)
            
            for schedule in schedules:
                next_run = schedule.get('next_run_at')
                if next_run:
                    next_run_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00')) if isinstance(next_run, str) else next_run
                    if now >= next_run_dt:
                        # Execute run
                        run = Run()
                        run_doc = run.model_dump()
                        run_doc['started_at'] = run_doc['started_at'].isoformat()
                        run_doc['scheduled_run_id'] = schedule['id']
                        await db.runs.insert_one(run_doc)
                        
                        # Run pipeline in background
                        asyncio.create_task(run_pipeline(run.id))
                        
                        # Calculate next run time
                        from croniter import croniter
                        cron = croniter(schedule['cron_expression'], now)
                        next_time = cron.get_next(datetime)
                        
                        await db.scheduled_runs.update_one(
                            {"id": schedule['id']},
                            {"$set": {
                                "last_run_at": now.isoformat(),
                                "next_run_at": next_time.isoformat()
                            }}
                        )
                        logger.info(f"Scheduled run executed: {schedule['name']}")
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)

@api_router.get("/schedules")
async def list_schedules():
    """Get all scheduled runs"""
    schedules = await db.scheduled_runs.find({}, {"_id": 0}).to_list(100)
    return {"schedules": schedules}

@api_router.post("/schedules")
async def create_schedule(schedule_data: ScheduledRunCreate):
    """Create a new scheduled run"""
    try:
        from croniter import croniter
        
        # Validate cron expression
        now = datetime.now(timezone.utc)
        cron = croniter(schedule_data.cron_expression, now)
        next_run = cron.get_next(datetime)
        
        schedule = ScheduledRun(
            cron_expression=schedule_data.cron_expression,
            name=schedule_data.name,
            enabled=schedule_data.enabled,
            next_run_at=next_run
        )
        
        doc = schedule.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['next_run_at'] = doc['next_run_at'].isoformat() if doc['next_run_at'] else None
        
        await db.scheduled_runs.insert_one(doc)
        
        return {"message": "Schedule created", "schedule": doc}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")

@api_router.patch("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, enabled: bool):
    """Enable or disable a scheduled run"""
    result = await db.scheduled_runs.update_one(
        {"id": schedule_id},
        {"$set": {"enabled": enabled}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": f"Schedule {'enabled' if enabled else 'disabled'}"}

@api_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a scheduled run"""
    result = await db.scheduled_runs.delete_one({"id": schedule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted"}

# ========================
# SOURCE HEALTH MONITORING
# ========================

@api_router.get("/sources/health")
async def get_sources_health():
    """Get health metrics for all sources"""
    sources = await db.sources.find({}, {"_id": 0}).to_list(100)
    health_data = []
    
    for source in sources:
        # Get source run history
        source_logs = await db.source_health.find(
            {"source_id": source['id']},
            {"_id": 0}
        ).sort("checked_at", -1).to_list(100)
        
        total = len(source_logs)
        successes = len([l for l in source_logs if l.get('success')])
        failures = total - successes
        
        last_success = next((l for l in source_logs if l.get('success')), None)
        last_failure = next((l for l in source_logs if not l.get('success')), None)
        
        avg_response_time = 0
        if source_logs:
            response_times = [l.get('response_time_ms', 0) for l in source_logs if l.get('response_time_ms')]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        health_data.append(SourceHealth(
            source_id=source['id'],
            source_name=source['name'],
            total_runs=total,
            successful_runs=successes,
            failed_runs=failures,
            success_rate=(successes / total * 100) if total > 0 else 0,
            avg_response_time_ms=avg_response_time,
            last_success_at=last_success.get('checked_at') if last_success else None,
            last_failure_at=last_failure.get('checked_at') if last_failure else None,
            last_error=last_failure.get('error') if last_failure else None
        ).model_dump())
    
    return {"health": health_data}

# ========================
# EMAIL CONFIGURATION
# ========================

@api_router.get("/email/config")
async def get_email_config():
    """Get current email configuration"""
    from_email = os.environ.get('SAFARAI_FROM_EMAIL', 'onboarding@resend.dev')
    recipients = os.environ.get('SAFARAI_RECIPIENTS', '').split(',')
    recipients = [r.strip() for r in recipients if r.strip()]
    
    return {
        "from_email": from_email,
        "recipients": recipients,
        "domain_verified": "kirikomal.com" in from_email
    }

@api_router.post("/email/test")
async def send_test_email():
    """Send a test email to verify configuration"""
    try:
        recipients = os.environ.get('SAFARAI_RECIPIENTS', '').split(',')
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if not recipients:
            raise HTTPException(status_code=400, detail="No recipients configured")
        
        params = {
            "from": os.environ.get('SAFARAI_FROM_EMAIL', 'onboarding@resend.dev'),
            "to": recipients,
            "subject": "SafarAI Test Email",
            "html": """
            <div style="font-family: sans-serif; padding: 20px;">
                <h1>SafarAI Email Test</h1>
                <p>This is a test email from your SafarAI Intelligence Platform.</p>
                <p>If you received this, your email configuration is working correctly.</p>
            </div>
            """
        }
        
        email = await asyncio.to_thread(resend.Emails.send, params)
        return {"message": "Test email sent", "email_id": email.get('id')}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
