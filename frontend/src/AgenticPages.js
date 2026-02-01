import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Brain, TrendingUp, Target, Zap, ChevronRight, Sparkles,
  Loader2, BarChart3, Activity, Shield, AlertTriangle,
  ArrowUpRight, ArrowDownRight, Minus, PieChart, LineChart
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ========================
// INSIGHTS PAGE - Redesigned with Better Visualization
// ========================
export const InsightsPage = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

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
      toast.success("Insights generated successfully!", { 
        description: `Analyzed ${response.data.events_analyzed} events` 
      });
      setTimeout(() => fetchInsights(), 2000);
    } catch (e) {
      toast.error("Failed to generate insights", { 
        description: e.response?.data?.detail || "Unknown error" 
      });
    } finally {
      setGenerating(false);
    }
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
          <p className="text-white/40 mb-8 max-w-md">
            Generate AI-powered insights to get impact analysis, trend forecasts, and recommendations
          </p>
          <button 
            onClick={generateInsights}
            disabled={generating}
            className="btn-premium-bw flex items-center gap-2"
            data-testid="generate-insights-btn"
          >
            {generating ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Generate Insights
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Calculate stats for visual summary
  const totalScenarios = insights.impact_scenarios?.length || 0;
  const criticalAlerts = insights.risk_alerts?.length || 0;
  const opportunities = insights.opportunities?.length || 0;

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="insights-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="badge-bw badge-outline mb-4 inline-block">
            <Brain size={12} /> AI Insights
          </span>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            Intelligence Overview
          </h1>
          <p className="text-white/40 mt-2">
            Generated: {insights.generated_at ? new Date(insights.generated_at).toLocaleString() : "N/A"}
          </p>
        </div>
        <button 
          onClick={generateInsights}
          disabled={generating}
          className="btn-outline-bw flex items-center gap-2"
          data-testid="regenerate-insights-btn"
        >
          {generating ? <Loader2 className="animate-spin" size={14} /> : <Sparkles size={14} />}
          Regenerate
        </button>
      </div>

      {/* Quick Stats - Visual Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-blue-500/10 flex items-center justify-center mb-3">
            <BarChart3 size={24} className="text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">{totalScenarios}</p>
          <p className="text-xs text-white/40 mt-1">Impact Scenarios</p>
        </div>
        <div className="spotlight-card p-5 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-red-500/10 flex items-center justify-center mb-3">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <p className="text-3xl font-bold text-white">{criticalAlerts}</p>
          <p className="text-xs text-white/40 mt-1">Risk Alerts</p>
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

      {/* Key Findings - Clean Cards */}
      {insights.key_findings && insights.key_findings.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <Target size={20} className="text-white/60" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-bold">Key Findings</h2>
              <p className="text-xs text-white/40">Top insights from the analysis</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {insights.key_findings.map((finding, i) => (
              <div key={i} className="p-5 rounded-xl bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 hover:border-white/10 transition-all">
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center mb-4">
                  <span className="text-sm font-bold text-white/60">{i + 1}</span>
                </div>
                <p className="text-white/70 text-sm leading-relaxed">{finding}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Alerts & Opportunities - Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        {/* Risk Alerts */}
        {insights.risk_alerts && insights.risk_alerts.length > 0 && (
          <div className="spotlight-card p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <AlertTriangle size={18} className="text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Risk Alerts</h3>
                <p className="text-xs text-white/40">Potential threats to monitor</p>
              </div>
            </div>
            <div className="space-y-3">
              {insights.risk_alerts.map((alert, i) => (
                <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-red-500/5 border border-red-500/10">
                  <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                    <ArrowDownRight size={12} className="text-red-400" />
                  </div>
                  <p className="text-sm text-red-300/80">{alert}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Opportunities */}
        {insights.opportunities && insights.opportunities.length > 0 && (
          <div className="spotlight-card p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                <Zap size={18} className="text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Opportunities</h3>
                <p className="text-xs text-white/40">Potential growth areas</p>
              </div>
            </div>
            <div className="space-y-3">
              {insights.opportunities.map((opp, i) => (
                <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-green-500/5 border border-green-500/10">
                  <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center shrink-0">
                    <ArrowUpRight size={12} className="text-green-400" />
                  </div>
                  <p className="text-sm text-green-300/80">{opp}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Impact Scenarios - Visual Cards */}
      {insights.impact_scenarios && insights.impact_scenarios.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <BarChart3 size={20} className="text-white/60" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-bold">Impact Scenarios</h2>
              <p className="text-xs text-white/40">Potential outcomes and their likelihood</p>
            </div>
          </div>
          <div className="space-y-4">
            {insights.impact_scenarios.map((scenario, i) => {
              const impactColor = {
                critical: { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500/20' },
                high: { bg: 'bg-orange-500', text: 'text-orange-400', border: 'border-orange-500/20' },
                medium: { bg: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500/20' },
                low: { bg: 'bg-blue-500', text: 'text-blue-400', border: 'border-blue-500/20' }
              }[scenario.impact_level] || { bg: 'bg-gray-500', text: 'text-gray-400', border: 'border-gray-500/20' };
              
              return (
                <div key={i} className={`p-5 rounded-xl bg-white/[0.02] border ${impactColor.border} hover:bg-white/[0.03] transition-all`}>
                  <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                    {/* Scenario Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">{scenario.scenario_name}</h3>
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${impactColor.bg}/10 ${impactColor.text}`}>
                          {scenario.impact_level}
                        </span>
                      </div>
                      <p className="text-sm text-white/50 leading-relaxed">{scenario.description}</p>
                    </div>
                    
                    {/* Visual Meters */}
                    <div className="flex lg:flex-col gap-4 lg:gap-3 lg:w-48">
                      {/* Probability */}
                      <div className="flex-1 lg:flex-none">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] text-white/40 uppercase">Probability</span>
                          <span className="text-xs font-mono text-white/60">{Math.round(scenario.probability * 100)}%</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${impactColor.bg} transition-all duration-500`}
                            style={{ width: `${scenario.probability * 100}%` }}
                          />
                        </div>
                      </div>
                      {/* Confidence */}
                      <div className="flex-1 lg:flex-none">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] text-white/40 uppercase">Confidence</span>
                          <span className="text-xs font-mono text-white/60">{Math.round(scenario.confidence_score * 100)}%</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-white/30 transition-all duration-500"
                            style={{ width: `${scenario.confidence_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Assumptions - Collapsed by default, cleaner */}
                  {scenario.assumptions && scenario.assumptions.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/5">
                      <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2">Key Assumptions</p>
                      <div className="flex flex-wrap gap-2">
                        {scenario.assumptions.slice(0, 3).map((assumption, j) => (
                          <span key={j} className="text-xs text-white/40 px-3 py-1 rounded-full bg-white/5">
                            {assumption.length > 50 ? assumption.slice(0, 50) + '...' : assumption}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Dashboard Recommendations - Compact Grid */}
      {insights.dashboard_recommendations && insights.dashboard_recommendations.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <PieChart size={20} className="text-white/60" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-bold">Recommended Dashboards</h2>
              <p className="text-xs text-white/40">Suggested visualizations for your data</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.dashboard_recommendations.map((widget, i) => {
              const priorityStyle = {
                P0: 'border-l-red-500',
                P1: 'border-l-orange-500',
                P2: 'border-l-blue-500'
              }[widget.priority] || 'border-l-gray-500';
              
              return (
                <div key={i} className={`p-4 rounded-xl bg-white/[0.02] border border-white/5 border-l-2 ${priorityStyle}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                      widget.priority === 'P0' ? 'bg-red-500/10 text-red-400' :
                      widget.priority === 'P1' ? 'bg-orange-500/10 text-orange-400' :
                      'bg-blue-500/10 text-blue-400'
                    }`}>
                      {widget.priority}
                    </span>
                    <span className="text-[10px] text-white/20 uppercase">{widget.widget_type}</span>
                  </div>
                  <h4 className="font-medium text-white mb-1">{widget.title}</h4>
                  <p className="text-xs text-white/40 leading-relaxed">{widget.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-center gap-6 text-xs text-white/30 py-4">
        <span>Processing time: {insights.processing_time_seconds?.toFixed(1)}s</span>
        <span>•</span>
        <span>Powered by GPT-5.2</span>
      </div>
    </div>
  );
};

// ========================
// TRENDS PAGE - Redesigned with Better Visualization
// ========================
export const TrendsPage = () => {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  // Category configuration
  const categories = [
    { id: 'all', label: 'All Trends', icon: TrendingUp },
    { id: 'partnerships', label: 'Partnerships', icon: Target, color: 'blue' },
    { id: 'funding', label: 'Funding', icon: BarChart3, color: 'green' },
    { id: 'pricing', label: 'Pricing', icon: Activity, color: 'yellow' },
    { id: 'technology', label: 'Technology', icon: Zap, color: 'purple' },
    { id: 'destinations', label: 'Destinations', icon: Target, color: 'pink' }
  ];

  const categoryColors = {
    partnerships: { bg: 'bg-blue-500', light: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
    funding: { bg: 'bg-green-500', light: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
    pricing: { bg: 'bg-yellow-500', light: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
    technology: { bg: 'bg-purple-500', light: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
    destinations: { bg: 'bg-pink-500', light: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20' }
  };

  const filteredTrends = selectedCategory === 'all' 
    ? trends 
    : trends.filter(t => t.trend_category === selectedCategory);

  // Group trends by category for summary
  const trendsByCategory = {};
  trends.forEach(t => {
    const cat = t.trend_category || 'other';
    if (!trendsByCategory[cat]) trendsByCategory[cat] = [];
    trendsByCategory[cat].push(t);
  });

  const horizonLabels = {
    next_quarter: 'Next Quarter',
    next_6_months: 'Next 6 Months',
    next_year: 'Next Year'
  };

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="trends-page">
      {/* Header */}
      <div>
        <span className="badge-bw badge-outline mb-4 inline-block">
          <TrendingUp size={12} /> Predictive Analytics
        </span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Trend Forecasts
        </h1>
        <p className="text-white/40 mt-2">
          AI-predicted tourism industry trends based on event patterns
        </p>
      </div>

      {trends.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center spotlight-card p-12">
          <TrendingUp className="mb-4 text-white/20" size={64} />
          <h2 className="text-2xl font-bold mb-2">No Trends Yet</h2>
          <p className="text-white/40">Run the pipeline to generate trend forecasts</p>
        </div>
      ) : (
        <>
          {/* Category Overview - Visual Summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(trendsByCategory).map(([category, catTrends]) => {
              const color = categoryColors[category] || { bg: 'bg-gray-500', light: 'bg-gray-500/10', text: 'text-gray-400' };
              const avgConfidence = catTrends.reduce((sum, t) => sum + (t.confidence || 0), 0) / catTrends.length;
              
              return (
                <div 
                  key={category} 
                  className={`spotlight-card p-4 cursor-pointer transition-all hover:scale-[1.02] ${
                    selectedCategory === category ? 'ring-1 ring-white/20' : ''
                  }`}
                  onClick={() => setSelectedCategory(selectedCategory === category ? 'all' : category)}
                >
                  <div className={`w-10 h-10 rounded-xl ${color.light} flex items-center justify-center mb-3`}>
                    <TrendingUp size={18} className={color.text} />
                  </div>
                  <p className="text-2xl font-bold text-white">{catTrends.length}</p>
                  <p className="text-xs text-white/40 capitalize mt-1">{category}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full ${color.bg}`} style={{ width: `${avgConfidence * 100}%` }} />
                    </div>
                    <span className="text-[10px] text-white/30">{Math.round(avgConfidence * 100)}%</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-4 py-2 rounded-full text-xs font-medium transition-all flex items-center gap-2 whitespace-nowrap ${
                  selectedCategory === cat.id
                    ? 'bg-white text-black'
                    : 'bg-white/5 text-white/50 hover:bg-white/10'
                }`}
              >
                <cat.icon size={14} />
                {cat.label}
              </button>
            ))}
          </div>

          {/* Trends List - Clean Visual Cards */}
          <div className="space-y-4">
            {filteredTrends.map((trend) => {
              const color = categoryColors[trend.trend_category] || categoryColors.partnerships;
              
              return (
                <div key={trend.id} className={`spotlight-card p-6 border-l-2 ${color.border}`}>
                  {/* Header Row */}
                  <div className="flex flex-col lg:flex-row lg:items-start gap-4 mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${color.light} ${color.text}`}>
                          {trend.trend_category}
                        </span>
                        <span className="text-xs text-white/30 uppercase">
                          {horizonLabels[trend.forecast_horizon] || trend.forecast_horizon}
                        </span>
                      </div>
                      <h3 className="text-xl font-semibold text-white">{trend.trend_name}</h3>
                    </div>
                    
                    {/* Confidence Gauge */}
                    <div className="lg:w-32 text-center">
                      <div className="relative w-20 h-20 mx-auto">
                        <svg className="w-20 h-20 transform -rotate-90">
                          <circle
                            cx="40"
                            cy="40"
                            r="32"
                            stroke="currentColor"
                            strokeWidth="6"
                            fill="transparent"
                            className="text-white/5"
                          />
                          <circle
                            cx="40"
                            cy="40"
                            r="32"
                            stroke="currentColor"
                            strokeWidth="6"
                            fill="transparent"
                            strokeDasharray={`${trend.confidence * 201} 201`}
                            className={color.text}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-lg font-bold text-white">{Math.round(trend.confidence * 100)}%</span>
                        </div>
                      </div>
                      <p className="text-[10px] text-white/40 uppercase mt-1">Confidence</p>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-white/60 leading-relaxed mb-4">{trend.description}</p>

                  {/* Potential Impact */}
                  {trend.potential_impact && (
                    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity size={14} className="text-white/40" />
                        <p className="text-xs text-white/40 uppercase font-medium">Potential Impact</p>
                      </div>
                      <p className="text-sm text-white/70">{trend.potential_impact}</p>
                    </div>
                  )}

                  {/* Key Indicators & Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Key Indicators */}
                    {trend.key_indicators && trend.key_indicators.length > 0 && (
                      <div>
                        <p className="text-xs text-white/40 uppercase font-medium mb-2 flex items-center gap-2">
                          <LineChart size={12} /> Key Indicators
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {trend.key_indicators.map((indicator, i) => (
                            <span key={i} className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-white/50 border border-white/5">
                              {indicator}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommended Actions */}
                    {trend.recommended_actions && trend.recommended_actions.length > 0 && (
                      <div>
                        <p className="text-xs text-white/40 uppercase font-medium mb-2 flex items-center gap-2">
                          <ChevronRight size={12} /> Recommended Actions
                        </p>
                        <ul className="space-y-1.5">
                          {trend.recommended_actions.slice(0, 3).map((action, i) => (
                            <li key={i} className="text-xs text-white/50 flex items-start gap-2">
                              <span className={`w-1.5 h-1.5 rounded-full ${color.bg} mt-1.5 shrink-0`} />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
