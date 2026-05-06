import { useState } from "react";
import { User, Mail, Shield, Save } from "lucide-react";

function SettingsPage({ user }) {
  const [name, setName] = useState(user?.name || "System Admin");
  const [email, setEmail] = useState(user?.email || "admin@airanger.com");
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <div><h2>Settings</h2><p>Manage your profile &amp; preferences</p></div>
      </div>

      <div className="settings-grid">
        <div className="profile-card glass-card">
          <div className="profile-avatar-section">
            <div className="profile-avatar"><Shield size={40} /></div>
            <div className="profile-avatar-info">
              <h3>{name}</h3>
              <span>{user?.role || "System Administrator"}</span>
            </div>
          </div>
        </div>

        <form className="settings-form glass-card" onSubmit={handleSave}>
          <h3>Profile Information</h3>
          <div className="form-group">
            <label><User size={16} /> Full Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label><Mail size={16} /> Email Address</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="form-group">
            <label><Shield size={16} /> Role</label>
            <input type="text" value={user?.role || "System Administrator"} disabled />
          </div>
          <button type="submit" className="save-btn">
            <Save size={18} /><span>{saved ? "Saved!" : "Save Changes"}</span>
          </button>
          {saved && <div className="save-success">✓ Profile updated successfully</div>}
        </form>

        <div className="system-info glass-card">
          <h3>System Information</h3>
          <div className="info-row"><span>Application</span><span>AI Ranger v2.0</span></div>
          <div className="info-row"><span>Detection Engine</span><span>Neural Net Simulator</span></div>
          <div className="info-row"><span>Backend Status</span><span className="status-online">● Online</span></div>
          <div className="info-row"><span>Last Updated</span><span>{new Date().toLocaleDateString()}</span></div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
