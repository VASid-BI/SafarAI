from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import resend
from firecrawl import FirecrawlApp

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize APIs
resend.api_key = os.environ.get('RESEND_API_KEY', '')
firecrawl = FirecrawlApp(api_key=os.environ.get('FIRECRAWL_API_KEY', ''))

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
        score = event.get('materiality_score', 0)
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
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                <span style="background:#fff;color:#000;padding:6px 16px;border-radius:100px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">
                    {event_type}
                </span>
                <span style="color:#fff;font-size:24px;font-weight:700;font-family:monospace;">
                    {score}
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
                    <span style="font-size:28px;line-height:64px;">🌍</span>
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
        
        try:
            # Crawl with Firecrawl
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
            
            # Filter and limit links
            filtered_links = [l for l in links if filter_link(l)][:8]
            
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
            
        except Exception as e:
            run_data['sources_failed'] += 1
            await log_run(run_id, "error", f"Failed to process source: {source_name}", {"error": str(e)})
    
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

# Startup: Seed default sources
@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.items.create_index("url", unique=True)
    await db.sources.create_index("active")
    await db.runs.create_index([("started_at", -1)])
    
    # Seed default sources if none exist
    source_count = await db.sources.count_documents({})
    if source_count == 0:
        logger.info("Seeding default sources...")
        for src in DEFAULT_SOURCES:
            source = Source(**src)
            doc = source.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.sources.insert_one(doc)
        logger.info(f"Seeded {len(DEFAULT_SOURCES)} default sources")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
