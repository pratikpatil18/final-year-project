import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { BarChart3, TrendingUp, AlertTriangle, Shield } from "lucide-react";

const COLORS = ["#ef4444", "#f59e0b", "#10b981"];

function AnalysisPage() {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => { fetchAnalysis(); }, []);

  const fetchAnalysis = async () => {
    try {
      const res = await fetch("/analysis");
      setAnalysis(await res.json());
    } catch (err) {
      console.error("Failed to fetch analysis:", err);
    }
  };

  const barData = analysis
    ? [
      { name: "Gun", count: analysis.gun_count, fill: "#ef4444" },
      { name: "Knife", count: analysis.knife_count, fill: "#f59e0b" },
      { name: "No Weapon", count: analysis.no_weapon_count, fill: "#10b981" },
    ]
    : [];

  const pieData = analysis
    ? [
      { name: "Gun", value: analysis.gun_count },
      { name: "Knife", value: analysis.knife_count },
      { name: "No Weapon", value: analysis.no_weapon_count },
    ].filter((d) => d.value > 0)
    : [];

  const tooltipStyle = {
    background: "rgba(15,23,42,0.95)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "8px",
    color: "#e2e8f0",
  };

  return (
    <div className="analysis-page">
      <div className="page-header">
        <div><h2>Wildlife Threat Analysis</h2><p>Weapon detection trends from forest camera reviews</p></div>
        {analysis && (
          <div className={`threat-level ${analysis.threat_level?.toLowerCase()}`}>
            <AlertTriangle size={16} />
            <span>Threat Level: {analysis.threat_level}</span>
          </div>
        )}
      </div>

      <div className="analysis-stats">
        <div className="analysis-stat-card glass-card">
          <div className="stat-icon red"><AlertTriangle size={20} /></div>
          <div><span className="stat-value">{analysis?.gun_count || 0}</span><span className="stat-label">Firearms Detected</span></div>
        </div>
        <div className="analysis-stat-card glass-card">
          <div className="stat-icon yellow"><AlertTriangle size={20} /></div>
          <div><span className="stat-value">{analysis?.knife_count || 0}</span><span className="stat-label">Knives Detected</span></div>
        </div>
        <div className="analysis-stat-card glass-card">
          <div className="stat-icon green"><Shield size={20} /></div>
          <div><span className="stat-value">{analysis?.no_weapon_count || 0}</span><span className="stat-label">No Weapon</span></div>
        </div>
        <div className="analysis-stat-card glass-card">
          <div className="stat-icon blue"><TrendingUp size={20} /></div>
          <div><span className="stat-value">{analysis?.total || 0}</span><span className="stat-label">Total Scans</span></div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card glass-card">
          <div className="section-header"><BarChart3 size={20} /><h3>Weapon Distribution</h3></div>
          {barData.some((d) => d.count > 0) ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData} barSize={50}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {barData.map((entry, i) => (<Cell key={i} fill={entry.fill} />))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-chart"><BarChart3 size={48} /><p>No data yet. Upload images to generate analysis.</p></div>
          )}
        </div>

        <div className="chart-card glass-card">
          <div className="section-header"><TrendingUp size={20} /><h3>Detection Breakdown</h3></div>
          {pieData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                    {pieData.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                  </Pie>
                  <Legend wrapperStyle={{ color: "#94a3b8" }} />
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-chart"><TrendingUp size={48} /><p>No data available for breakdown chart.</p></div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalysisPage;
