import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Brain, TrendingUp, Target, Zap, ChevronRight, Sparkles,
  Loader2, BarChart3, Activity, AlertTriangle,
  ArrowUpRight, ArrowDownRight, ChevronDown, ChevronUp
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ========================
// INSIGHTS PAGE - Clean with Read More
// ========================
export const InsightsPage = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedScenarios, setExpandedScenarios] = useState({});

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const response = await axios.get(`${API}/agentic/insights/latest`);
      setInsights(response.data);
    } catch (e) {
      console.error("Failed to fetch insights:", e);
    } finally {
      setLoading(false);
    }
  };

  const generateInsights = async () => {
    try {
      setGenerating(true);
      toast.info("Generating AI insights...", { description: "This may take 30-60 seconds" });
      const response = await axios.post(`${API}/agentic/generate`);
      toast.success("Insights generated!", { description: `Analyzed ${response.data.events_analyzed} events` });
      setTimeout(() => fetchInsights(), 2000);
    } catch (e) {
      toast.error("Failed to generate insights", { description: e.response?.data?.detail || "Unknown error" });
    } finally {
      setGenerating(false);
    }
  };

  const toggleScenario = (index) => {
    setExpandedScenarios(prev => ({ ...prev, [index]: !prev[index] }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  if (!insights || insights.message) {
    return (
      <div className="space-y-8 noise-bg" data-testid="insights-page">
        <div className="flex flex-col items-center justify-center h-[60vh] text-center">
          <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mb-6">
            <Brain className="text-white/60" size={40} />
          </div>
          <h2 className="text-3xl font-bold mb-3">No Insights Yet</h2>
          <p className="text-white/40 mb-8 max-w-md">Generate AI-powered insights to get impact analysis and recommendations</p>
          <button onClick={generateInsights} disabled={generating} className="btn-premium-bw flex items-center gap-2" data-testid="generate-insights-btn">
            {generating ? <><Loader2 className="animate-spin" size={16} />Generating...</> : <><Sparkles size={16} />Generate Insights</>}
          </button>
        </div>
      </div>
    );
  }

  const totalScenarios = insights.impact_scenarios?.length || 0;
  const criticalAlerts = insights.risk_alerts?.length || 0;
  const opportunities = insights.opportunities?.length || 0;

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="insights-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="badge-bw badge-outline mb-4 inline-block"><Brain size={12} /> AI Insights</span>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Intelligence Overview</h1>
          <p className="text-white/40 mt-2">Generated: {insights.generated_at ? new Date(insights.generated_at).toLocaleString() : "N/A"}</p>
        </div>
        <button onClick={generateInsights} disabled={generating} className="btn-outline-bw flex items-center gap-2" data-testid="regenerate-insights-btn">
          {generating ? <Loader2 className="animate-spin" size={14} /> : <Sparkles size={14} />}Regenerate
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-blue-500/10 flex items-center justify-center mb-3">
            <BarChart3 size={24} className="text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">{totalScenarios}</p>
          <p className="text-xs text-white/40 mt-1">Scenarios</p>
        </div>
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-red-500/10 flex items-center justify-center mb-3">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <p className="text-3xl font-bold text-white">{criticalAlerts}</p>
          <p className="text-xs text-white/40 mt-1">Risks</p>
        </div>
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-green-500/10 flex items-center justify-center mb-3">
            <Zap size={24} className="text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">{opportunities}</p>
          <p className="text-xs text-white/40 mt-1">Opportunities</p>
        </div>
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-purple-500/10 flex items-center justify-center mb-3">
            <Activity size={24} className="text-purple-400" />
          </div>
          <p className="text-3xl font-bold text-white">{insights.processing_time_seconds?.toFixed(0) || 0}s</p>
          <p className="text-xs text-white/40 mt-1">Analysis Time</p>
        </div>
      </div>

      {/* Key Findings */}
      {insights.key_findings && insights.key_findings.length > 0 && (
        <div className="spotlight-card p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Target size={18} className="text-white/60" /> Key Findings</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {insights.key_findings.map((finding, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                <span className="text-xs text-white/30 mb-2 block">#{i + 1}</span>
                <p className="text-sm text-white/70 leading-relaxed">{finding}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk & Opportunities Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.risk_alerts && insights.risk_alerts.length > 0 && (
          <div className="spotlight-card p-5">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-400" /> Risks
            </h3>
            <div className="space-y-2">
              {insights.risk_alerts.map((alert, i) => (
                <div key={i} className="flex items-start gap-2 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                  <ArrowDownRight size={14} className="text-red-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-red-300/80">{alert}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {insights.opportunities && insights.opportunities.length > 0 && (
          <div className="spotlight-card p-5">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Zap size={16} className="text-green-400" /> Opportunities
            </h3>
            <div className="space-y-2">
              {insights.opportunities.map((opp, i) => (
                <div key={i} className="flex items-start gap-2 p-3 rounded-lg bg-green-500/5 border border-green-500/10">
                  <ArrowUpRight size={14} className="text-green-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-green-300/80">{opp}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Impact Scenarios with Read More */}
      {insights.impact_scenarios && insights.impact_scenarios.length > 0 && (
        <div className="spotlight-card p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><BarChart3 size={18} className="text-white/60" /> Impact Scenarios</h2>
          <div className="space-y-3">
            {insights.impact_scenarios.map((scenario, i) => {
              const isExpanded = expandedScenarios[i];
              const impactColors = {
                critical: 'bg-red-500/10 text-red-400 border-red-500/20',
                high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
                medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
                low: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
              };
              const colorClass = impactColors[scenario.impact_level] || impactColors.low;
              
              return (
                <div key={i} className={`rounded-xl border ${colorClass.split(' ')[2]} bg-white/[0.01] overflow-hidden`}>
                  {/* Always visible header */}
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold ${colorClass}`}>
                        {scenario.impact_level}
                      </span>
                      <h3 className="font-medium text-white">{scenario.scenario_name}</h3>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right hidden sm:block">
                        <span className="text-xs text-white/40">Probability</span>
                        <p className="text-sm font-mono text-white/70">{Math.round(scenario.probability * 100)}%</p>
                      </div>
                      <button 
                        onClick={() => toggleScenario(i)}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                      >
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>
                  
                  {/* Expandable content */}
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-white/5 pt-4 space-y-4">
                      <p className="text-sm text-white/60 leading-relaxed">{scenario.description}</p>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-[10px] text-white/40 uppercase">Probability</span>
                          <div className="mt-1 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: `${scenario.probability * 100}%` }} />
                          </div>
                        </div>
                        <div>
                          <span className="text-[10px] text-white/40 uppercase">Confidence</span>
                          <div className="mt-1 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-white/30" style={{ width: `${scenario.confidence_score * 100}%` }} />
                          </div>
                        </div>
                      </div>
                      
                      {scenario.assumptions && scenario.assumptions.length > 0 && (
                        <div>
                          <p className="text-[10px] text-white/30 uppercase mb-2">Assumptions</p>
                          <ul className="space-y-1">
                            {scenario.assumptions.map((a, j) => (
                              <li key={j} className="text-xs text-white/50 flex items-start gap-2">
                                <span className="text-white/20">•</span>{a}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="text-center text-xs text-white/30 py-4">Powered by GPT-5.2</div>
    </div>
  );
};

// ========================
// TRENDS PAGE - Clean with Read More
// ========================
export const TrendsPage = () => {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedTrends, setExpandedTrends] = useState({});

  useEffect(() => {
    fetchTrends();
  }, []);

  const fetchTrends = async () => {
    try {
      const response = await axios.get(`${API}/trends`);
      setTrends(response.data.trends || []);
    } catch (e) {
      console.error("Failed to fetch trends:", e);
      toast.error("Failed to load trends");
    } finally {
      setLoading(false);
    }
  };

  const toggleTrend = (id) => {
    setExpandedTrends(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'partnerships', label: 'Partnerships' },
    { id: 'funding', label: 'Funding' },
    { id: 'pricing', label: 'Pricing' },
    { id: 'technology', label: 'Technology' },
    { id: 'destinations', label: 'Destinations' }
  ];

  const categoryColors = {
    partnerships: { bg: 'bg-blue-500', light: 'bg-blue-500/10', text: 'text-blue-400' },
    funding: { bg: 'bg-green-500', light: 'bg-green-500/10', text: 'text-green-400' },
    pricing: { bg: 'bg-yellow-500', light: 'bg-yellow-500/10', text: 'text-yellow-400' },
    technology: { bg: 'bg-purple-500', light: 'bg-purple-500/10', text: 'text-purple-400' },
    destinations: { bg: 'bg-pink-500', light: 'bg-pink-500/10', text: 'text-pink-400' }
  };

  const filteredTrends = selectedCategory === 'all' ? trends : trends.filter(t => t.trend_category === selectedCategory);

  const horizonLabels = {
    next_quarter: 'Q1',
    next_6_months: '6M',
    next_year: '1Y'
  };

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="trends-page">
      {/* Header */}
      <div>
        <span className="badge-bw badge-outline mb-4 inline-block"><TrendingUp size={12} /> Predictive Analytics</span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Trend Forecasts</h1>
        <p className="text-white/40 mt-2">AI-predicted industry trends</p>
      </div>

      {trends.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center spotlight-card p-12">
          <TrendingUp className="mb-4 text-white/20" size={64} />
          <h2 className="text-2xl font-bold mb-2">No Trends Yet</h2>
          <p className="text-white/40">Run the pipeline to generate trend forecasts</p>
        </div>
      ) : (
        <>
          {/* Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-4 py-2 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
                  selectedCategory === cat.id ? 'bg-white text-black' : 'bg-white/5 text-white/50 hover:bg-white/10'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Trends List - Compact Cards */}
          <div className="space-y-3">
            {filteredTrends.map((trend) => {
              const isExpanded = expandedTrends[trend.id];
              const color = categoryColors[trend.trend_category] || categoryColors.partnerships;
              
              return (
                <div key={trend.id} className="spotlight-card overflow-hidden">
                  {/* Compact Header - Always Visible */}
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase font-medium ${color.light} ${color.text} shrink-0`}>
                        {trend.trend_category}
                      </span>
                      <h3 className="font-medium text-white truncate">{trend.trend_name}</h3>
                    </div>
                    
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-white/30">{horizonLabels[trend.forecast_horizon] || trend.forecast_horizon}</span>
                      
                      {/* Confidence Badge */}
                      <div className={`px-2 py-1 rounded ${color.light} ${color.text} text-xs font-mono`}>
                        {Math.round(trend.confidence * 100)}%
                      </div>
                      
                      <button 
                        onClick={() => toggleTrend(trend.id)}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                      >
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>
                  
                  {/* Expandable Details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-white/5 pt-4 space-y-4">
                      <p className="text-sm text-white/60 leading-relaxed">{trend.description}</p>
                      
                      {/* Confidence Bar */}
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] text-white/40 uppercase">Confidence Level</span>
                          <span className="text-xs font-mono text-white/50">{Math.round(trend.confidence * 100)}%</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div className={`h-full ${color.bg}`} style={{ width: `${trend.confidence * 100}%` }} />
                        </div>
                      </div>
                      
                      {/* Potential Impact */}
                      {trend.potential_impact && (
                        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
                          <p className="text-[10px] text-white/40 uppercase mb-1">Potential Impact</p>
                          <p className="text-sm text-white/70">{trend.potential_impact}</p>
                        </div>
                      )}
                      
                      {/* Two Columns: Indicators & Actions */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {trend.key_indicators && trend.key_indicators.length > 0 && (
                          <div>
                            <p className="text-[10px] text-white/40 uppercase mb-2">Key Indicators</p>
                            <div className="flex flex-wrap gap-1">
                              {trend.key_indicators.map((indicator, i) => (
                                <span key={i} className="text-xs px-2 py-1 rounded bg-white/5 text-white/50">{indicator}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        {trend.recommended_actions && trend.recommended_actions.length > 0 && (
                          <div>
                            <p className="text-[10px] text-white/40 uppercase mb-2">Actions</p>
                            <ul className="space-y-1">
                              {trend.recommended_actions.slice(0, 3).map((action, i) => (
                                <li key={i} className="text-xs text-white/50 flex items-start gap-2">
                                  <ChevronRight size={12} className="text-white/30 mt-0.5 shrink-0" />{action}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
