import { useState, useEffect } from "react";
import { Search, Clock, Filter } from "lucide-react";

function HistoryPage() {
  const [detections, setDetections] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("All");

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch("/history");
      const data = await res.json();
      setDetections(data.detections || []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  const filtered = detections.filter((d) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      d.original_filename?.toLowerCase().includes(term) ||
      d.detection_type?.toLowerCase().includes(term) ||
      d.location?.toLowerCase().includes(term);
    const matchesType = filterType === "All" || d.detection_type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="history-page">
      <div className="page-header">
        <div><h2>Detection History</h2><p>{detections.length} total records</p></div>
      </div>

      <div className="history-controls glass-card">
        <div className="search-box">
          <Search size={18} />
          <input type="text" placeholder="Search by filename, type or location..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <div className="filter-group">
          <Filter size={16} />
          {["All", "Gun", "Knife", "No Weapon"].map((type) => (
            <button key={type} className={`filter-btn ${filterType === type ? "active" : ""}`} onClick={() => setFilterType(type)}>{type}</button>
          ))}
        </div>
      </div>

      <div className="history-table-wrapper glass-card">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <Clock size={48} />
            <h3>No Records Found</h3>
            <p>{detections.length === 0 ? "Upload forest camera frames from the dashboard to see history" : "No results match your filter"}</p>
          </div>
        ) : (
          <table className="history-table">
            <thead>
              <tr><th>#</th><th>Image</th><th>Filename</th><th>Detection</th><th>Confidence</th><th>Location</th><th>Date &amp; Time</th></tr>
            </thead>
            <tbody>
              {filtered.map((d, i) => (
                <tr key={d.id} style={{ animationDelay: `${i * 0.05}s` }}>
                  <td className="td-id">{d.id}</td>
                  <td><div className="table-thumb"><img src={d.image_url} alt={d.original_filename} /></div></td>
                  <td className="td-filename">{d.original_filename}</td>
                  <td><span className={`type-badge ${d.detection_type === "No Weapon" ? "safe" : "threat"}`}>{d.detection_type}</span></td>
                  <td>{(d.confidence * 100).toFixed(0)}%</td>
                  <td>{d.location}</td>
                  <td className="td-time">{d.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;
