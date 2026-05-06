import { useState, useEffect, useRef } from "react";
import {
  Upload, Shield, AlertTriangle, Activity, Clock,
  Camera, Crosshair, Zap, X,
} from "lucide-react";

function DashboardPage() {
  const [stats, setStats] = useState({ total: 0, critical: 0, health: 98.5, responseTime: 42 });
  const [detections, setDetections] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [showAlert, setShowAlert] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch("/history");
      const data = await res.json();
      const list = data.detections || [];
      setDetections(list);
      const total = list.length;
      const critical = list.filter((d) => d.severity === "critical").length;
      setStats((p) => ({ ...p, total, critical }));
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setErrorMessage("");
    setPreviewUrl(URL.createObjectURL(file));
    setLastResult(null);
    handleUpload(file);
  };

  const handleUpload = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("image", file);
    try {
      const res = await fetch("/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || data.message || "Upload failed");
      }

      setLastResult(data.detection);
      setPreviewUrl(data.detection.image_url);
      setDetections((prev) => [data.detection, ...prev]);
      setStats((prev) => ({
        ...prev,
        total: prev.total + 1,
        critical: data.detection.severity === "critical" ? prev.critical + 1 : prev.critical,
      }));
      if (data.detection.detection_type !== "No Weapon") {
        setShowAlert(true);
        setTimeout(() => setShowAlert(false), 5000);
      }
    } catch (err) {
      console.error("Upload failed:", err);
      setErrorMessage(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const recentAlerts = detections.slice(0, 3);

  return (
    <div className="dashboard-page">
      {showAlert && lastResult && (
        <div className="alert-overlay">
          <div className="alert-banner">
            <AlertTriangle size={24} />
            <span>⚠️ THREAT DETECTED: {lastResult.detection_type.toUpperCase()} at {lastResult.location}</span>
            <button onClick={() => setShowAlert(false)}><X size={18} /></button>
          </div>
        </div>
      )}

      <div className="page-header">
        <div>
          <h2>Wildlife Forest Threat Monitoring</h2>
          <p>Analyze ranger camera frames for illegal weapons near protected animals</p>
        </div>
        <div className="live-badge"><span className="live-dot"></span>LIVE MONITORING</div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue"><Shield size={22} /></div>
          <div className="stat-info"><span className="stat-value">{stats.total}</span><span className="stat-label">Total Detections</span></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red"><AlertTriangle size={22} /></div>
          <div className="stat-info"><span className="stat-value">{stats.critical}</span><span className="stat-label">Critical Alerts</span></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Activity size={22} /></div>
          <div className="stat-info"><span className="stat-value">{stats.health}%</span><span className="stat-label">System Health</span></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><Clock size={22} /></div>
          <div className="stat-info"><span className="stat-value">{stats.responseTime}ms</span><span className="stat-label">Mean Response</span></div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* CCTV Feed Simulation */}
        <div className="cctv-section glass-card">
          <div className="section-header"><Camera size={20} /><h3>Forest Camera Review</h3></div>
          <div className="cctv-viewport">
            {previewUrl ? (
              <div className="cctv-preview">
                <img src={previewUrl} alt="Forest camera frame" />
                <div className="cctv-overlay">
                  <div className="scan-line"></div>
                  <div className="cctv-corners">
                    <span className="corner tl"></span><span className="corner tr"></span>
                    <span className="corner bl"></span><span className="corner br"></span>
                  </div>
                  <div className="cctv-info">
                    <span>CAM-01 | {new Date().toLocaleTimeString()}</span>
                    <span className="rec-badge">● REC</span>
                  </div>
                </div>
                {uploading && (
                  <div className="analyzing-overlay">
                    <div className="analyzing-spinner"></div>
                    <span>Analyzing frame...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="cctv-placeholder"><Camera size={48} /><p>Upload a forest surveillance frame to run the weapon detector</p></div>
            )}
          </div>
          <div className="cctv-controls">
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept="image/*" hidden />
            <button className="upload-btn" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              <Upload size={18} /><span>{uploading ? "Analyzing..." : "Upload Camera Frame"}</span>
            </button>
          </div>
          {errorMessage && (
            <div className="detection-result threat">
              <div className="result-header">
                <AlertTriangle size={20} />
                <span className="result-type">Processing Error</span>
              </div>
              <div className="result-details">
                <span>{errorMessage}</span>
              </div>
            </div>
          )}
          {lastResult && !uploading && (
            <div className={`detection-result ${lastResult.detection_type === "No Weapon" ? "safe" : "threat"}`}>
              <div className="result-header">
                {lastResult.detection_type === "No Weapon" ? <Crosshair size={20} /> : <Zap size={20} />}
                <span className="result-type">{lastResult.detection_type}</span>
              </div>
              <div className="result-details">
                <span>Confidence: {(lastResult.confidence * 100).toFixed(0)}%</span>
                <span>Location: {lastResult.location}</span>
                <span>Objects Found: {lastResult.detection_count || 0}</span>
                {lastResult.notification && (
                  <span>Email Alert: {lastResult.notification.message}</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Alert Panel */}
        <div className="alert-section glass-card">
          <div className="section-header"><AlertTriangle size={20} /><h3>Recent Alerts</h3></div>
          <div className="alert-list">
            {recentAlerts.length === 0 ? (
              <div className="no-alerts"><Shield size={32} /><p>No detections yet</p><span>Upload a camera frame to begin</span></div>
            ) : (
              recentAlerts.map((alert, index) => (
                <div key={alert.id} className={`alert-item ${alert.severity}`} style={{ animationDelay: `${index * 0.1}s` }}>
                  <div className="alert-dot"></div>
                  <div className="alert-content">
                    <span className="alert-type">{alert.detection_type}</span>
                    <span className="alert-location">{alert.location}</span>
                    <span className="alert-time">{alert.timestamp}</span>
                  </div>
                  <span className={`alert-badge ${alert.severity}`}>{alert.severity}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
