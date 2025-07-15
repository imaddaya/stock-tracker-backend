
import { useState, useEffect } from "react";
import { useRouter } from "next/router";

export default function ConfirmAccountDeletion() {
  const router = useRouter();
  const { token } = router.query;

  const [status, setStatus] = useState("Processing account deletion...");

  useEffect(() => {
    if (!token) return;

    const tokenStr = Array.isArray(token) ? token[0] : token;

    fetch(
      `https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/auth/confirm-account-deletion?token=${encodeURIComponent(
        tokenStr
      )}`,
      {
        method: "POST",
      }
    )
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.detail || "Account deletion failed.");
        }

        setStatus("Account deleted successfully. You will be redirected to the homepage...");
        
        // Clear any stored auth data
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_email");
        
        setTimeout(() => {
          router.push("/"); // go to homepage
        }, 3000);
      })
      .catch((err) => {
        setStatus(`Error deleting account: ${err.message}`);
      });
  }, [token, router]);

  return (
    <div style={{ 
      padding: "2rem", 
      textAlign: "center",
      fontFamily: "'Poppins', sans-serif",
      maxWidth: "600px",
      margin: "0 auto"
    }}>
      <h2 style={{ 
        color: status.includes("Error") ? "#dc3545" : 
              status.includes("successfully") ? "#28a745" : "#6c757d",
        marginBottom: "1rem"
      }}>
        Account Deletion Confirmation
      </h2>
      <p style={{ fontSize: "1.1rem", lineHeight: "1.5" }}>
        {status}
      </p>
      {status.includes("Error") && (
        <div style={{ marginTop: "2rem" }}>
          <button
            onClick={() => router.push("/")}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            Return to Homepage
          </button>
        </div>
      )}
    </div>
  );
}
