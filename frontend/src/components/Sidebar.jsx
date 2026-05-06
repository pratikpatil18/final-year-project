import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Clock,
  BarChart3,
  Settings,
  LogOut,
  Shield,
  Radio,
} from "lucide-react";

function Sidebar({ user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Shield size={28} />
          <div>
            <h1>AI RANGER</h1>
            <span>Command Center</span>
          </div>
        </div>
      </div>

      <div className="sidebar-badge">
        <Radio size={14} className="pulse-icon" />
        <span>Live Monitoring</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </NavLink>
        <NavLink
          to="/history"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <Clock size={20} />
          <span>History</span>
        </NavLink>
        <NavLink
          to="/analysis"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <BarChart3 size={20} />
          <span>Analysis</span>
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
        >
          <Settings size={20} />
          <span>Settings</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="user-avatar">
            {user?.name?.charAt(0) || "A"}
          </div>
          <div className="user-info">
            <span className="user-name">{user?.name || "Admin"}</span>
            <span className="user-role">{user?.role || "Administrator"}</span>
          </div>
        </div>
        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
