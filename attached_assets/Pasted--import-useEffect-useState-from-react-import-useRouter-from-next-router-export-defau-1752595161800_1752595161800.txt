
import { useEffect, useState } from "react";
import { useRouter } from "next/router";

export default function ProfilePage() {
  const [userEmail, setUserEmail] = useState("");
  const [emailReminderTime, setEmailReminderTime] = useState("");
  const [emailReminderEnabled, setEmailReminderEnabled] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("••••••••");
  const [isEditingApiKey, setIsEditingApiKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showApiWarning, setShowApiWarning] = useState(false);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPasswordResetMessage, setShowPasswordResetMessage] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const email = localStorage.getItem("user_email");
    
    if (!token) {
      router.push("/");
      return;
    }

    setUserEmail(email || "");
    
    // Fetch user profile data
    fetchProfileData(token);
  }, [router]);

  const fetchProfileData = async (token: string) => {
    try {
      const res = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/user/profile",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        const data = await res.json();
        setApiKey(data.alpha_vantage_api_key || "");
        setEmailReminderTime(data.email_reminder_time || "");
        setEmailReminderEnabled(data.email_reminder_enabled || false);
      }
    } catch (err) {
      console.error("Error fetching profile:", err);
    }
  };

  const handleSetEmailReminder = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setLoading(true);
    try {
      const res = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/user/email-reminder",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ 
            reminder_time: emailReminderEnabled ? emailReminderTime : null,
            enabled: emailReminderEnabled 
          }),
        }
      );

      if (res.ok) {
        setStatus(emailReminderEnabled ? "Daily email reminder enabled!" : "Email reminder disabled!");
      } else {
        const data = await res.json();
        setStatus(data.detail || "Failed to update email reminder");
      }
    } catch (err) {
      setStatus("Error updating email reminder");
    }
    setLoading(false);
  };

  const handleUpdateApiKey = async () => {
    const token = localStorage.getItem("access_token");
    if (!token || !newApiKey.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/user/update-api-key",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ new_api_key: newApiKey }),
        }
      );

      if (res.ok) {
        setApiKey(newApiKey);
        setIsEditingApiKey(false);
        setNewApiKey("");
        setStatus("API key updated successfully!");
      } else {
        const data = await res.json();
        setStatus(data.detail || "Failed to update API key");
      }
    } catch (err) {
      setStatus("Error updating API key");
    }
    setLoading(false);
  };

  const handleChangePassword = async () => {
    if (!userEmail.trim()) {
      setStatus("Email not found");
      return;
    }

    setLoading(true);
    setShowPasswordResetMessage(true);
    try {
      const response = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/auth/forgot-password",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email: userEmail }),
        }
      );

      const data = await response.json();
      setStatus("Password reset email sent!");
    } catch (error) {
      setStatus("Password reset email sent!");
    }
    setLoading(false);
  };

  const handleDeleteAccount = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setLoading(true);
    try {
      const res = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/user/delete-account",
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        setStatus("Account deletion email sent. Check your email and confirm within 30 minutes.");
        setShowDeleteConfirm(false);
      } else {
        const data = await res.json();
        setStatus(data.detail || "Failed to initiate account deletion");
      }
    } catch (err) {
      setStatus("Error initiating account deletion");
    }
    setLoading(false);
  };

  return (
    <div style={{ fontFamily: "'Poppins', sans-serif", padding: "2rem", maxWidth: "600px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            router.push("/loggedin");
          }}
          style={{
            textDecoration: "underline",
            color: "#0070f3",
            cursor: "pointer",
            fontSize: "0.9rem",
          }}
        >
          &larr; Return to main page
        </a>
      </div>

      <h1 style={{ marginBottom: "2rem", textAlign: "center" }}>Profile Settings</h1>

      {/* User Email */}
      <div style={{ marginBottom: "2rem", padding: "1rem", border: "1px solid #ddd", borderRadius: "8px" }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.5rem" }}>
          User Email:
        </label>
        <span style={{ color: "#666", fontSize: "1rem" }}>{userEmail}</span>
      </div>

      {/* Email Reminder Time */}
      <div style={{ 
        marginBottom: "2rem", 
        padding: "1rem", 
        border: "1px solid #ddd", 
        borderRadius: "8px",
        backgroundColor: emailReminderEnabled ? "white" : "#f5f5f5",
        opacity: emailReminderEnabled ? 1 : 0.6
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <label style={{ fontWeight: "bold", color: emailReminderEnabled ? "black" : "#999" }}>
            Daily Email Reminder:
          </label>
          
          {/* Custom On/Off Switch */}
          <div
            onClick={() => setEmailReminderEnabled(!emailReminderEnabled)}
            style={{
              position: "relative",
              width: "60px",
              height: "30px",
              backgroundColor: emailReminderEnabled ? "#4CAF50" : "#ccc",
              borderRadius: "15px",
              cursor: "pointer",
              transition: "background-color 0.3s",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "3px",
                left: emailReminderEnabled ? "33px" : "3px",
                width: "24px",
                height: "24px",
                backgroundColor: "white",
                borderRadius: "50%",
                transition: "left 0.3s",
                boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              }}
            />
          </div>
        </div>
        
        <div style={{ marginBottom: "1rem" }}>
          <span style={{ 
            fontSize: "0.9rem", 
            color: emailReminderEnabled ? "#666" : "#999",
            fontStyle: "italic"
          }}>
            {emailReminderEnabled ? "Receive daily email with your stocks information" : "Email reminders are disabled"}
          </span>
        </div>
        
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <label style={{ 
            fontSize: "0.9rem", 
            color: emailReminderEnabled ? "#666" : "#999" 
          }}>
            Time:
          </label>
          <input
            type="time"
            value={emailReminderTime}
            onChange={(e) => setEmailReminderTime(e.target.value)}
            disabled={!emailReminderEnabled}
            style={{
              padding: "0.5rem",
              border: emailReminderEnabled ? "1px solid #ccc" : "1px solid #ddd",
              borderRadius: "4px",
              fontSize: "1rem",
              backgroundColor: emailReminderEnabled ? "white" : "#f5f5f5",
              color: emailReminderEnabled ? "black" : "#999",
              cursor: emailReminderEnabled ? "text" : "not-allowed",
            }}
          />
          <button
            onClick={handleSetEmailReminder}
            disabled={loading || !emailReminderEnabled || !emailReminderTime}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: emailReminderEnabled && emailReminderTime ? "#007bff" : "#ccc",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: (loading || !emailReminderEnabled || !emailReminderTime) ? "not-allowed" : "pointer",
              fontSize: "1rem",
            }}
          >
            {loading ? "Updating..." : "Save Time"}
          </button>
        </div>
      </div>

      {/* API Key */}
      <div style={{ marginBottom: "2rem", padding: "1rem", border: "1px solid #ddd", borderRadius: "8px" }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.5rem" }}>
          Alpha Vantage API Key:
        </label>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
          {isEditingApiKey ? (
            <>
              <input
                type="text"
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
                placeholder="Enter new API key"
                style={{
                  flex: 1,
                  padding: "0.5rem",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  fontSize: "1rem",
                }}
              />
              <button
                onClick={handleUpdateApiKey}
                disabled={loading || !newApiKey.trim()}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#28a745",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                Update
              </button>
              <button
                onClick={() => {
                  setIsEditingApiKey(false);
                  setNewApiKey("");
                }}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <span style={{ flex: 1, fontFamily: "monospace", fontSize: "0.9rem" }}>
                {showApiKey ? apiKey : "••••••••••••••••"}
              </span>
              <button
                onClick={() => setShowApiKey(!showApiKey)}
                style={{
                  padding: "0.3rem 0.8rem",
                  backgroundColor: "#17a2b8",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "0.8rem",
                }}
              >
                {showApiKey ? "Hide" : "Show"}
              </button>
            </>
          )}
        </div>
        {!isEditingApiKey && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              onClick={() => {
                setIsEditingApiKey(true);
                setNewApiKey(apiKey);
              }}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#ffc107",
                color: "black",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9rem",
              }}
            >
              Upgrade API Key
            </button>
            <div 
              style={{ position: "relative", display: "inline-block" }}
              onMouseEnter={() => setShowApiWarning(true)}
              onMouseLeave={() => setShowApiWarning(false)}
            >
              <span
                style={{
                  fontSize: "1.2rem",
                  cursor: "help",
                  color: "#dc3545",
                }}
              >
                ⚠️
              </span>
              {showApiWarning && (
                <div
                  style={{
                    position: "absolute",
                    bottom: "130%",
                    left: "50%",
                    transform: "translateX(-50%)",
                    backgroundColor: "#333",
                    color: "white",
                    padding: "0.8rem",
                    borderRadius: "6px",
                    fontSize: "0.8rem",
                    width: "300px",
                    maxWidth: "300px",
                    zIndex: 1000,
                    boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
                    lineHeight: "1.4",
                  }}
                >
                  <div style={{ color: "#ff6b6b", fontWeight: "bold", marginBottom: "0.3rem" }}>
                    ⚠️ WARNING
                  </div>
                  <div style={{ color: "#ff6b6b" }}>
                    Creating multiple API keys from the same location will cause an IP ban. Change API only when upgrading the key. This can be done once/week.
                  </div>
                  <div
                    style={{
                      position: "absolute",
                      top: "100%",
                      left: "50%",
                      transform: "translateX(-50%)",
                      width: 0,
                      height: 0,
                      borderLeft: "6px solid transparent",
                      borderRight: "6px solid transparent",
                      borderTop: "6px solid #333",
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Password */}
      <div style={{ marginBottom: "2rem", padding: "1rem", border: "1px solid #ddd", borderRadius: "8px" }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.5rem" }}>
          Password:
        </label>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
          <span style={{ flex: 1, fontFamily: "monospace" }}>
            {showPassword ? "current_password_hidden" : "••••••••"}
          </span>
          <button
            onClick={() => setShowPassword(!showPassword)}
            style={{
              padding: "0.3rem 0.8rem",
              backgroundColor: "#17a2b8",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.8rem",
            }}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
        <button
          onClick={handleChangePassword}
          disabled={loading}
          style={{
            padding: "0.5rem 1rem",
            backgroundColor: "#fd7e14",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "0.9rem",
            marginBottom: "0.5rem",
          }}
        >
          {loading ? "Sending..." : "Change Password"}
        </button>
        {showPasswordResetMessage && (
          <div style={{ 
            fontSize: "0.9rem", 
            color: "#28a745", 
            fontStyle: "italic",
            marginTop: "0.5rem"
          }}>
            If your email is registered and verified, you'll receive password reset instructions.
          </div>
        )}
      </div>

      {/* Delete Account */}
      <div style={{ marginBottom: "2rem", padding: "1rem", border: "2px solid #dc3545", borderRadius: "8px", backgroundColor: "#fff5f5" }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: "0.5rem", color: "#dc3545" }}>
          Danger Zone:
        </label>
        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#dc3545",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
          >
            Delete Account
          </button>
        ) : (
          <div>
            <p style={{ color: "#dc3545", marginBottom: "1rem", fontWeight: "bold" }}>
              ARE YOU SURE? This action will send a verification email. You have 30 minutes to confirm account deletion.
            </p>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                onClick={handleDeleteAccount}
                disabled={loading}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#dc3545",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontSize: "0.9rem",
                }}
              >
                {loading ? "Sending..." : "Yes, Delete My Account"}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      
    </div>
  );
}
