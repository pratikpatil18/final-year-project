import { useState } from "react";
import { Shield, Lock, User, AlertCircle, Eye, EyeOff } from "lucide-react";

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success) {
        onLogin(data.user);
      } else {
        setError(data.message || "Invalid credentials");
      }
    } catch {
      setError("Connection failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-grid"></div>
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo"><Shield size={36} /></div>
          <h1>AI RANGER</h1>
          <p>Wildlife Protection Command Center</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          {error && (<div className="login-error"><AlertCircle size={16} /><span>{error}</span></div>)}
          <div className="input-group">
            <User size={18} className="input-icon" />
            <input id="login-username" type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </div>
          <div className="input-group">
            <Lock size={18} className="input-icon" />
            <input id="login-password" type={showPassword ? "text" : "password"} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <button id="login-submit" type="submit" className="login-btn" disabled={loading}>
            {loading ? <div className="spinner"></div> : <><Lock size={18} /><span>Authenticate</span></>}
          </button>
        </form>
        <div className="login-footer"><p>Authorized Personnel Only</p></div>
      </div>
    </div>
  );
}

export default LoginPage;
