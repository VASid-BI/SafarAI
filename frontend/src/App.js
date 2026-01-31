import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import Marquee from "react-fast-marquee";
import createGlobe from "cobe";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Play, Database, FileText, Activity, Terminal, 
  Plus, CheckCircle2, XCircle, AlertTriangle, Loader2,
  ExternalLink, Trash2, Clock, Zap, ChevronDown,
  TrendingUp, Mail, BarChart3, Shield, Globe as GlobeIcon,
  ArrowRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Toaster, toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ========================
// LUNAR UI COMPONENTS
// ========================

// Interactive Globe Component (COBE) - Lunar UI Style
const InteractiveGlobe = () => {
  const canvasRef = useRef(null);
  const pointerInteracting = useRef(null);
  const pointerInteractionMovement = useRef(0);
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    let phi = 0;
    let width = 0;
    
    const onResize = () => {
      if (canvasRef.current) {
        width = canvasRef.current.offsetWidth;
      }
    };
    window.addEventListener('resize', onResize);
    onResize();
    
    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: 800 * 2,
      height: 800 * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 3,
      mapSamples: 24000,
      mapBrightness: 1.8,
      baseColor: [0.4, 0.4, 0.4],
      markerColor: [1, 1, 1],
      glowColor: [0.1, 0.1, 0.1],
      markers: [
        // Major tourism hubs
        { location: [40.7128, -74.0060], size: 0.06 },  // NYC
        { location: [51.5074, -0.1278], size: 0.06 },   // London
        { location: [35.6762, 139.6503], size: 0.06 }, // Tokyo
        { location: [48.8566, 2.3522], size: 0.05 },    // Paris
        { location: [25.2048, 55.2708], size: 0.07 },   // Dubai
        { location: [-33.8688, 151.2093], size: 0.05 }, // Sydney
        { location: [1.3521, 103.8198], size: 0.05 },   // Singapore
        { location: [55.7558, 37.6173], size: 0.04 },   // Moscow
        { location: [-22.9068, -43.1729], size: 0.04 }, // Rio
        { location: [19.4326, -99.1332], size: 0.04 },  // Mexico City
        { location: [22.3193, 114.1694], size: 0.05 },  // Hong Kong
        { location: [13.7563, 100.5018], size: 0.05 },  // Bangkok
      ],
      onRender: (state) => {
        if (!pointerInteracting.current) {
          phi += 0.002;
        }
        state.phi = phi + rotation;
        state.width = width * 2;
        state.height = width * 2;
      }
    });
    
    return () => {
      globe.destroy();
      window.removeEventListener('resize', onResize);
    };
  }, [rotation]);

  return (
    <div className="relative w-full aspect-square max-w-[450px] mx-auto">
      {/* Glow effect behind globe */}
      <div className="absolute inset-0 rounded-full bg-white/[0.02] blur-3xl" />
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing relative z-10"
        style={{ contain: 'layout paint size' }}
        onPointerDown={(e) => {
          pointerInteracting.current = e.clientX - pointerInteractionMovement.current;
        }}
        onPointerUp={() => {
          pointerInteracting.current = null;
        }}
        onPointerOut={() => {
          pointerInteracting.current = null;
        }}
        onMouseMove={(e) => {
          if (pointerInteracting.current !== null) {
            const delta = e.clientX - pointerInteracting.current;
            pointerInteractionMovement.current = delta;
            setRotation(delta / 200);
          }
        }}
        onTouchMove={(e) => {
          if (pointerInteracting.current !== null && e.touches[0]) {
            const delta = e.touches[0].clientX - pointerInteracting.current;
            pointerInteractionMovement.current = delta;
            setRotation(delta / 100);
          }
        }}
      />
      {/* Gradient overlay at bottom */}
      <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-black to-transparent pointer-events-none z-20" />
    </div>
  );
};

// Marquee Component
const IntelMarquee = ({ items }) => (
  <div className="marquee-container py-6 border-y border-white/5">
    <Marquee speed={40} gradient={false} pauseOnHover>
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-8 mx-8">
          <span className="text-white/30 text-sm uppercase tracking-widest">{item}</span>
          <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
        </div>
      ))}
    </Marquee>
  </div>
);

// Text Reveal Component
const TextReveal = ({ children, className = "", delay = 0 }) => {
  const words = children.split(' ');
  
  return (
    <span className={className}>
      {words.map((word, i) => (
        <span
          key={i}
          className="inline-block overflow-hidden"
        >
          <motion.span
            className="inline-block"
            initial={{ y: '100%', opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{
              duration: 0.5,
              delay: delay + i * 0.1,
              ease: [0.4, 0, 0.2, 1]
            }}
          >
            {word}&nbsp;
          </motion.span>
        </span>
      ))}
    </span>
  );
};

// Scroll Reveal Component
const ScrollReveal = ({ children, className = "" }) => {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 40 }}
      animate={isVisible ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
};

// Details/Accordion Component
const Details = ({ items }) => {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <div className="space-y-0">
      {items.map((item, i) => (
        <div key={i} className="details-item">
          <button
            onClick={() => setOpenIndex(openIndex === i ? -1 : i)}
            className="details-trigger w-full text-left"
          >
            <span className="text-lg font-medium text-white/80">{item.title}</span>
            <ChevronDown
              size={20}
              className={`text-white/40 transition-transform duration-300 ${openIndex === i ? 'rotate-180' : ''}`}
            />
          </button>
          <div className={`details-content ${openIndex === i ? 'open' : ''}`}>
            <p className="text-white/50 text-sm pb-4 leading-relaxed">{item.content}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Fluid Navigation Tab
const FluidTab = ({ to, icon: Icon, label, isActive }) => (
  <Link to={to} data-testid={`nav-${label.toLowerCase().replace(' ', '-')}`}>
    <div className={`fluid-tab ${isActive ? 'active' : ''}`}>
      <Icon size={18} />
      <span>{label}</span>
    </div>
  </Link>
);

// Spotlight Card
const SpotlightCard = ({ children, className = "" }) => {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className={`spotlight-card ${className}`}
    >
      {children}
    </div>
  );
};

// ========================
// SIDEBAR
// ========================
const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { path: "/", label: "Dashboard", icon: Activity },
    { path: "/sources", label: "Sources", icon: Database },
    { path: "/brief", label: "Intel Brief", icon: FileText },
    { path: "/runs", label: "Metrics", icon: BarChart3 },
    { path: "/logs", label: "Logs", icon: Terminal },
  ];
  
  return (
    <div className="hidden md:flex flex-col w-72 h-screen fixed left-0 top-0 glass-bw border-r border-white/5">
      <div className="p-8 border-b border-white/5">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center">
              <GlobeIcon size={24} className="text-black" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              SAFAR<span className="text-white/50">AI</span>
            </h1>
            <p className="text-[10px] text-white/30 uppercase tracking-[0.25em]">Intelligence</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-5">
        <div className="fluid-tabs">
          {navItems.map(({ path, label, icon }) => (
            <FluidTab
              key={path}
              to={path}
              icon={icon}
              label={label}
              isActive={location.pathname === path}
            />
          ))}
        </div>
      </nav>
      
      <div className="p-5 border-t border-white/5">
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
          <div className="flex items-center gap-3">
            <div className="status-indicator online" />
            <div>
              <p className="text-xs font-medium text-white/80">System Online</p>
              <p className="text-[10px] text-white/40">All services operational</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ========================
// DASHBOARD
// ========================
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
      setIsRunning(response.data.latest_run?.status === "running");
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [fetchStats]);
  
  const triggerRun = async () => {
    try {
      setIsRunning(true);
      const response = await axios.post(`${API}/run`);
      toast.success("Pipeline initiated", { description: `Run ID: ${response.data.run_id.slice(0, 8)}...` });
    } catch (e) {
      toast.error("Failed to start pipeline");
      setIsRunning(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }
  
  const latestRun = stats?.latest_run;
  const marqueeItems = [
    "Marriott International", "Hilton Worldwide", "Hyatt Hotels", "IHG",
    "Skift News", "PhocusWire", "US Travel Association", "Reuters Business", "TravelZoo"
  ];
  
  const detailsItems = [
    { title: "What does SafarAI monitor?", content: "SafarAI continuously monitors tourism and hospitality news sources, extracting partnerships, funding rounds, campaigns, and deal intelligence using AI-powered analysis." },
    { title: "How often is data updated?", content: "The pipeline can be triggered manually or scheduled. Each run crawls all active sources, detects new or updated content, and generates executive briefings." },
    { title: "What types of events are tracked?", content: "We track partnerships, funding & investments, campaign deals, acquisitions, executive hiring, and pricing changes across the tourism industry." },
  ];
  
  return (
    <div className="space-y-8 noise-bg" data-testid="dashboard-page">
      {/* Hero Section with Globe */}
      <ScrollReveal>
        <div className="grid md:grid-cols-2 gap-8 items-center min-h-[500px]">
          <div className="space-y-8">
            <div>
              <span className="badge-bw badge-outline mb-6 inline-block">
                <Zap size={12} /> Intelligence Platform
              </span>
              <h1 className="text-5xl md:text-6xl font-bold leading-[1.1] tracking-tight">
                <TextReveal>Competitive Intelligence</TextReveal>
                <br />
                <span className="text-white/40">
                  <TextReveal delay={0.3}>for Tourism</TextReveal>
                </span>
              </h1>
            </div>
            <p className="text-white/50 text-lg leading-relaxed max-w-lg">
              Monitor competitors, extract partnerships, track funding rounds, and discover deals automatically with AI-powered analysis.
            </p>
            <div className="flex gap-4">
              <button
                onClick={triggerRun}
                disabled={isRunning}
                className="btn-premium-bw flex items-center gap-2"
                data-testid="run-pipeline-btn"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Execute Pipeline
                  </>
                )}
              </button>
              <Link to="/brief">
                <button className="btn-outline-bw flex items-center gap-2">
                  View Brief <ArrowRight size={14} />
                </button>
              </Link>
            </div>
          </div>
          <div className="hidden md:block">
            <InteractiveGlobe />
          </div>
        </div>
      </ScrollReveal>
      
      {/* Marquee */}
      <IntelMarquee items={marqueeItems} />
      
      {/* Stats Grid */}
      <ScrollReveal>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Active Sources", value: stats?.active_sources || 0, icon: Database },
            { label: "Total Runs", value: stats?.total_runs || 0, icon: Activity },
            { label: "Events Extracted", value: stats?.total_events || 0, icon: TrendingUp },
            { label: "Items Indexed", value: stats?.total_items || 0, icon: FileText },
          ].map((stat, i) => (
            <SpotlightCard key={i} className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                  <stat.icon size={18} className="text-white/60" />
                </div>
              </div>
              <p className="stat-number">{stat.value}</p>
              <p className="text-xs text-white/40 uppercase tracking-wider mt-2">{stat.label}</p>
            </SpotlightCard>
          ))}
        </div>
      </ScrollReveal>
      
      {/* Latest Run */}
      {latestRun && (
        <ScrollReveal>
          <SpotlightCard className="p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                  <BarChart3 size={22} className="text-white/60" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold">Latest Run</h3>
                  <p className="text-xs text-white/40 font-mono">{latestRun.id?.slice(0, 12)}...</p>
                </div>
              </div>
              <span className={`badge-bw ${latestRun.status === 'success' ? 'badge-success-bw' : 'badge-warning-bw'}`}>
                {latestRun.status === 'success' ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                {latestRun.status}
              </span>
            </div>
            
            <div className="grid grid-cols-5 gap-4">
              {[
                { label: "Sources", value: `${latestRun.sources_ok}/${latestRun.sources_total}` },
                { label: "New", value: latestRun.items_new },
                { label: "Updated", value: latestRun.items_updated },
                { label: "Events", value: latestRun.events_created },
                { label: "Emails", value: latestRun.emails_sent },
              ].map((item, i) => (
                <div key={i} className="text-center p-4 rounded-xl bg-white/[0.02] border border-white/5">
                  <p className="text-2xl font-bold text-white">{item.value}</p>
                  <p className="text-[10px] text-white/40 uppercase tracking-wider mt-1">{item.label}</p>
                </div>
              ))}
            </div>
          </SpotlightCard>
        </ScrollReveal>
      )}
      
      {/* Details Section */}
      <ScrollReveal>
        <SpotlightCard className="p-8">
          <h3 className="text-xl font-semibold mb-6">How It Works</h3>
          <Details items={detailsItems} />
        </SpotlightCard>
      </ScrollReveal>
    </div>
  );
};

// ========================
// SOURCES PAGE
// ========================
const Sources = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newSource, setNewSource] = useState({ name: "", url: "", category: "general" });
  
  const fetchSources = async () => {
    try {
      const response = await axios.get(`${API}/sources`);
      setSources(response.data.sources || []);
    } catch (e) {
      toast.error("Failed to fetch sources");
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => { fetchSources(); }, []);
  
  const toggleSource = async (sourceId, currentActive) => {
    try {
      await axios.patch(`${API}/sources/${sourceId}`, { active: !currentActive });
      setSources(sources.map(s => s.id === sourceId ? { ...s, active: !currentActive } : s));
      toast.success(`Source ${!currentActive ? "enabled" : "disabled"}`);
    } catch (e) {
      toast.error("Failed to update source");
    }
  };
  
  const deleteSource = async (sourceId) => {
    try {
      await axios.delete(`${API}/sources/${sourceId}`);
      setSources(sources.filter(s => s.id !== sourceId));
      toast.success("Source deleted");
    } catch (e) {
      toast.error("Failed to delete source");
    }
  };
  
  const addSource = async () => {
    if (!newSource.name || !newSource.url) {
      toast.error("Name and URL are required");
      return;
    }
    try {
      const response = await axios.post(`${API}/sources`, newSource);
      setSources([...sources, response.data]);
      setNewSource({ name: "", url: "", category: "general" });
      setAddDialogOpen(false);
      toast.success("Source added");
    } catch (e) {
      toast.error("Failed to add source");
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }
  
  return (
    <div className="space-y-8 noise-bg" data-testid="sources-page">
      <ScrollReveal>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              <TextReveal>Data Sources</TextReveal>
            </h1>
            <p className="text-white/40 mt-2">Manage monitored websites and feeds</p>
          </div>
          
          <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
            <DialogTrigger asChild>
              <button className="btn-premium-bw flex items-center gap-2" data-testid="add-source-btn">
                <Plus size={16} />
                Add Source
              </button>
            </DialogTrigger>
            <DialogContent className="glass-bw border-white/10 max-w-md">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold">Add New Source</DialogTitle>
                <DialogDescription className="text-white/40">
                  Add a website to monitor for competitive intelligence.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <label className="text-xs uppercase tracking-wider text-white/40 mb-2 block">Name</label>
                  <Input
                    value={newSource.name}
                    onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                    placeholder="e.g., Marriott News"
                    className="input-bw"
                    data-testid="source-name-input"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-wider text-white/40 mb-2 block">URL</label>
                  <Input
                    value={newSource.url}
                    onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                    placeholder="https://news.example.com"
                    className="input-bw"
                    data-testid="source-url-input"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-wider text-white/40 mb-2 block">Category</label>
                  <Select value={newSource.category} onValueChange={(v) => setNewSource({ ...newSource, category: v })}>
                    <SelectTrigger className="input-bw" data-testid="source-category-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="glass-bw border-white/10">
                      <SelectItem value="hotel">Hotel</SelectItem>
                      <SelectItem value="accommodation">Accommodation</SelectItem>
                      <SelectItem value="airline">Airline</SelectItem>
                      <SelectItem value="deals">Deals</SelectItem>
                      <SelectItem value="news">News</SelectItem>
                      <SelectItem value="association">Association</SelectItem>
                      <SelectItem value="general">General</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <button onClick={addSource} className="btn-premium-bw w-full" data-testid="submit-source-btn">
                  Add Source
                </button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </ScrollReveal>
      
      <div className="space-y-3">
        {sources.map((source, i) => (
          <ScrollReveal key={source.id}>
            <SpotlightCard className="p-5" data-testid={`source-card-${source.id}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`status-indicator ${source.active ? 'online' : ''}`} />
                  <div>
                    <h3 className="font-medium text-white">{source.name}</h3>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-xs text-white/40 hover:text-white/60 flex items-center gap-1 mt-1">
                      {source.url} <ExternalLink size={10} />
                    </a>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="badge-bw badge-outline">{source.category}</span>
                  <Switch
                    checked={source.active}
                    onCheckedChange={() => toggleSource(source.id, source.active)}
                    data-testid={`toggle-source-${source.id}`}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteSource(source.id)}
                    className="text-white/40 hover:text-white hover:bg-white/5"
                    data-testid={`delete-source-${source.id}`}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
            </SpotlightCard>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
};

// ========================
// BRIEF PAGE
// ========================
const Brief = () => {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchBrief = async () => {
      try {
        const response = await axios.get(`${API}/brief/latest`);
        setBrief(response.data);
      } catch (e) {
        console.error("Failed to fetch brief:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchBrief();
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }
  
  if (!brief || !brief.events || brief.events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center" data-testid="brief-page">
        <FileText className="mb-6 text-white/20" size={64} />
        <h2 className="text-2xl font-bold mb-2">No Brief Available</h2>
        <p className="text-white/40 mb-8">Run the pipeline to generate intelligence</p>
        <Link to="/">
          <button className="btn-premium-bw flex items-center gap-2">
            <Play size={16} /> Go to Dashboard
          </button>
        </Link>
      </div>
    );
  }
  
  const events = brief.events || [];
  const topMovers = events.filter(e => e.materiality_score >= 70);
  const partnerships = events.filter(e => e.event_type === "partnership");
  const funding = events.filter(e => e.event_type === "funding");
  const campaigns = events.filter(e => e.event_type === "campaign_deal");
  
  const EventCard = ({ event }) => (
    <div className="event-card-bw">
      <div className="mb-4">
        <span className="badge-bw badge-white">
          {event.event_type?.replace("_", " ")}
        </span>
      </div>
      <h3 className="text-lg font-semibold mb-2">{event.title}</h3>
      <p className="text-sm text-white/60 mb-2">{event.company}</p>
      <p className="text-sm text-white/40 mb-4 leading-relaxed">{event.summary}</p>
      <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 mb-4">
        <p className="text-xs text-white/60">
          <span className="text-white/80 font-medium">Why it matters:</span> {event.why_it_matters}
        </p>
      </div>
      {event.evidence_quotes?.length > 0 && (
        <div className="space-y-2 mb-4">
          {event.evidence_quotes.slice(0, 2).map((quote, i) => (
            <p key={i} className="text-xs text-white/30 italic border-l-2 border-white/10 pl-3">"{quote}"</p>
          ))}
        </div>
      )}
      <a href={event.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-white/50 hover:text-white flex items-center gap-1">
        View Source <ExternalLink size={12} />
      </a>
    </div>
  );
  
  const Section = ({ title, events }) => {
    if (!events || events.length === 0) return null;
    return (
      <ScrollReveal className="mb-10">
        <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
          {title}
          <span className="text-sm font-normal text-white/30">({events.length})</span>
        </h3>
        <div className="space-y-4">
          {events.slice(0, 5).map((event, i) => (
            <EventCard key={event.id || i} event={event} />
          ))}
        </div>
      </ScrollReveal>
    );
  };
  
  return (
    <div className="space-y-8 noise-bg" data-testid="brief-page">
      <ScrollReveal>
        <div>
          <span className="badge-bw badge-white mb-4 inline-block">Latest Brief</span>
          <h1 className="text-4xl font-bold tracking-tight">
            <TextReveal>Executive Intelligence Brief</TextReveal>
          </h1>
          <p className="text-white/40 mt-2">
            Generated: {brief.created_at ? new Date(brief.created_at).toLocaleString() : "Unknown"}
          </p>
        </div>
      </ScrollReveal>
      
      <Section title="Top Movers" events={topMovers} />
      <Section title="Partnerships" events={partnerships} />
      <Section title="Funding" events={funding} />
      <Section title="Campaigns & Deals" events={campaigns} />
    </div>
  );
};

// ========================
// RUNS PAGE
// ========================
const Runs = () => {
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchRun = async () => {
      try {
        const response = await axios.get(`${API}/runs/latest`);
        setRun(response.data);
      } catch (e) {
        console.error("Failed to fetch run:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchRun();
    const interval = setInterval(fetchRun, 3000);
    return () => clearInterval(interval);
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }
  
  if (!run || run.message) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center" data-testid="runs-page">
        <BarChart3 className="mb-6 text-white/20" size={64} />
        <h2 className="text-2xl font-bold mb-2">No Runs Yet</h2>
        <p className="text-white/40">Execute the pipeline to see metrics</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-8 noise-bg" data-testid="runs-page">
      <ScrollReveal>
        <h1 className="text-4xl font-bold tracking-tight">
          <TextReveal>Run Metrics</TextReveal>
        </h1>
        <p className="text-white/40 mt-2">Latest pipeline execution details</p>
      </ScrollReveal>
      
      <ScrollReveal>
        <SpotlightCard className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center">
                {run.status === 'success' ? (
                  <CheckCircle2 size={28} className="text-black" />
                ) : run.status === 'running' ? (
                  <Loader2 size={28} className="text-black animate-spin" />
                ) : (
                  <AlertTriangle size={28} className="text-black" />
                )}
              </div>
              <div>
                <h3 className="text-2xl font-bold uppercase">{run.status?.replace("_", " ")}</h3>
                <p className="text-xs text-white/40 font-mono">ID: {run.id}</p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Sources", value: run.sources_total },
              { label: "Sources OK", value: run.sources_ok },
              { label: "Sources Failed", value: run.sources_failed },
              { label: "Events Created", value: run.events_created },
            ].map((stat, i) => (
              <div key={i} className="text-center p-6 rounded-xl bg-white/[0.02] border border-white/5">
                <p className="stat-number text-3xl">{stat.value}</p>
                <p className="text-[10px] text-white/40 uppercase tracking-wider mt-2">{stat.label}</p>
              </div>
            ))}
          </div>
          
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Items Total", value: run.items_total },
              { label: "New Items", value: run.items_new },
              { label: "Updated", value: run.items_updated },
              { label: "Emails Sent", value: run.emails_sent },
            ].map((stat, i) => (
              <div key={i} className="text-center p-6 rounded-xl bg-white/[0.02] border border-white/5">
                <p className="stat-number text-3xl">{stat.value}</p>
                <p className="text-[10px] text-white/40 uppercase tracking-wider mt-2">{stat.label}</p>
              </div>
            ))}
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/5 flex justify-between text-xs text-white/40">
            <span className="flex items-center gap-2">
              <Clock size={14} />
              Started: {run.started_at ? new Date(run.started_at).toLocaleString() : "N/A"}
            </span>
            <span>Finished: {run.finished_at ? new Date(run.finished_at).toLocaleString() : "In progress..."}</span>
          </div>
        </SpotlightCard>
      </ScrollReveal>
    </div>
  );
};

// ========================
// LOGS PAGE
// ========================
const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [runId, setRunId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get(`${API}/logs/latest`);
        setLogs(response.data.logs || []);
        setRunId(response.data.run_id);
      } catch (e) {
        console.error("Failed to fetch logs:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);
  
  const filteredLogs = filter === "all" ? logs : logs.filter(l => l.level === filter);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }
  
  return (
    <div className="space-y-8 noise-bg" data-testid="logs-page">
      <ScrollReveal>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              <TextReveal>Pipeline Logs</TextReveal>
            </h1>
            <p className="text-white/40 mt-2 font-mono text-sm">Run: {runId || "N/A"}</p>
          </div>
          
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-32 input-bw" data-testid="log-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass-bw border-white/10">
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="warn">Warnings</SelectItem>
              <SelectItem value="error">Errors</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </ScrollReveal>
      
      <SpotlightCard className="overflow-hidden">
        <ScrollArea className="h-[600px]">
          {filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64">
              <Terminal className="mb-4 text-white/20" size={48} />
              <p className="text-white/40">No logs available</p>
            </div>
          ) : (
            <div className="p-4 space-y-1">
              {filteredLogs.map((log, i) => (
                <div key={log.id || i} className={`log-entry-bw ${log.level}`} data-testid={`log-entry-${i}`}>
                  <div className="flex items-start gap-4">
                    <span className={`shrink-0 text-[10px] uppercase font-bold px-2 py-1 rounded ${
                      log.level === "error" ? "bg-red-500/10 text-red-400" :
                      log.level === "warn" ? "bg-yellow-500/10 text-yellow-400" :
                      "bg-white/5 text-white/50"
                    }`}>
                      {log.level}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/70">{log.message}</p>
                      {log.meta && Object.keys(log.meta).length > 0 && (
                        <pre className="text-xs text-white/30 mt-2 overflow-x-auto bg-black/20 p-2 rounded">
                          {JSON.stringify(log.meta, null, 2)}
                        </pre>
                      )}
                    </div>
                    <span className="text-[10px] text-white/30 shrink-0">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </SpotlightCard>
    </div>
  );
};

// ========================
// MAIN APP
// ========================
function App() {
  return (
    <div className="min-h-screen bg-black">
      <Toaster 
        theme="dark" 
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(20, 20, 20, 0.9)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#fff'
          }
        }}
      />
      <BrowserRouter>
        <div className="flex">
          <Sidebar />
          <main className="flex-1 md:ml-72 p-8 min-h-screen">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/brief" element={<Brief />} />
              <Route path="/runs" element={<Runs />} />
              <Route path="/logs" element={<Logs />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
