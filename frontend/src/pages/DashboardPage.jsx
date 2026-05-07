import { useState, useEffect, useRef } from "react";
import {
  Upload, Shield, AlertTriangle, Activity, Clock,
  Camera, Crosshair, Zap, X, Film,
} from "lucide-react";

function DashboardPage() {
  const [stats, setStats] = useState({ total: 0, critical: 0, health: 98.5, responseTime: 42 });
  const [detections, setDetections] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewKind, setPreviewKind] = useState("image");
  const [lastResult, setLastResult] = useState(null);
  const [showAlert, setShowAlert] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [systemStatus, setSystemStatus] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    fetchSystemStatus();
  }, []);

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

  const fetchSystemStatus = async () => {
    try {
      const res = await fetch("/");
      const data = await res.json();
      setSystemStatus(data);
    } catch (err) {
      console.error("Failed to fetch system status:", err);
    }
  };

  const formatUploadError = (data) => {
    if (data?.model_ready === false) {
      return data.hint || data.error || "The detection model is not configured.";
    }
    return data?.error || data?.message || "Upload failed";
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setErrorMessage("");
    setPreviewKind(file.type.startsWith("video/") ? "video" : "image");
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
        throw new Error(formatUploadError(data));
      }

      setLastResult(data.detection);
      setPreviewKind("image");
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
      fetchSystemStatus();
    } finally {
      setUploading(false);
    }
  };

  const recentAlerts = detections.slice(0, 3);
  const modelNotReady = systemStatus?.model_ready === false;

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
          <p>Process camera frames or videos to detect illegal weapons near protected animals</p>
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
        <div className="cctv-section glass-card">
          <div className="section-header"><Camera size={20} /><h3>Forest Camera Review</h3></div>
          <div className="cctv-viewport">
            {previewUrl ? (
              <div className="cctv-preview">
                {previewKind === "video" ? (
                  <video src={previewUrl} controls muted className="cctv-video-preview" />
                ) : (
                  <img src={previewUrl} alt="Forest camera frame" />
                )}
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
                    <span>{previewKind === "video" ? "Extracting and analyzing frames..." : "Analyzing frame..."}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="cctv-placeholder">
                <Film size={48} />
                <p>Upload a forest surveillance frame or short video to run the weapon detector</p>
              </div>
            )}
          </div>
          {modelNotReady && (
            <div className="detection-result threat">
              <div className="result-header">
                <AlertTriangle size={20} />
                <span className="result-type">Model Setup Required</span>
              </div>
              <div className="result-details">
                <span>{systemStatus.hint}</span>
                <span>Set <code>MODEL_PATH</code> in <code>backend/.env</code> or place the trained file at <code>model/runs/train/weapon_detector2/weights/best.pt</code>.</span>
              </div>
            </div>
          )}
          <div className="cctv-controls">
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept="image/*,video/*" hidden />
            <button className="upload-btn" onClick={() => fileInputRef.current?.click()} disabled={uploading || modelNotReady}>
              <Upload size={18} /><span>{modelNotReady ? "Configure Model To Upload" : uploading ? "Analyzing..." : "Upload Image Or Video"}</span>
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
                <span>Source: {lastResult.source_type === "video" ? "Video" : "Image"}</span>
                <span>Confidence: {(lastResult.confidence * 100).toFixed(0)}%</span>
                <span>Location: {lastResult.location}</span>
                <span>Objects Found: {lastResult.detection_count || 0}</span>
                {lastResult.source_type === "video" && (
                  <span>Alert Frame: {lastResult.source_timestamp_seconds?.toFixed(2)}s</span>
                )}
                {lastResult.notification && (
                  <span>Email Alert: {lastResult.notification.message}</span>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="alert-section glass-card">
          <div className="section-header"><AlertTriangle size={20} /><h3>Recent Alerts</h3></div>
          <div className="alert-list">
            {recentAlerts.length === 0 ? (
              <div className="no-alerts"><Shield size={32} /><p>No detections yet</p><span>Upload a frame or video to begin</span></div>
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
