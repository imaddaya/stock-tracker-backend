import { useState, useEffect } from "react";
import { useRouter } from "next/router";

export default function ResetPassword() {
  const router = useRouter();
  const { token } = router.query;

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const getPasswordValidation = () => {
    return {
      minLength: newPassword.length >= 8,
      hasUppercase: /[A-Z]/.test(newPassword),
      hasLowercase: /[a-z]/.test(newPassword),
      hasNumber: /\d/.test(newPassword),
      hasSpecial: /[!@#$%^&*]/.test(newPassword),
    };
  };

  const validation = getPasswordValidation();

  useEffect(() => {
    if (!router.isReady) return;
    
    if (!token) {
      setStatus("Missing token. Please check your email link.");
    }
  }, [token, router.isReady]);

  const handleSubmit = async () => {
    if (!token) {
      setStatus("Verification token is missing.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setStatus("Passwords do not match");
      return;
    }
    if (newPassword.length < 6) {
      setStatus("Password must be at least 6 characters");
      return;
    }

    setIsLoading(true);
    setStatus("");

    try {
      const response = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/auth/reset-password",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, new_password: newPassword }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setStatus(data.detail || "Reset failed");
        return;
      }

      setStatus("Password reset successfully. You may now log in.");
      setNewPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        router.push("/");
      }, 2000);
    } catch (error) {
      console.error("Error:", error);
      setStatus("Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const isReadyToSubmit = token && newPassword && confirmPassword;

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h2>Reset Your Password</h2>
      <input
        type="password"
        placeholder="New Password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        style={{ margin: "1rem", padding: "0.5rem" ,width: "300px"}}
      />
      <br />
      <ul
        style={{
          fontSize: "0.8rem",
          textAlign: "left",
          maxWidth: "300px",
          margin: "0 auto",
          paddingLeft: "1.2rem",
          listStyleType: "none",
        }}
      >
        <li style={{ color: validation.minLength ? "#28a745" : "#dc3545", marginBottom: "0.2rem" }}>
          {validation.minLength ? "✓" : "✗"} At least 8 characters
        </li>
        <li style={{ color: validation.hasUppercase ? "#28a745" : "#dc3545", marginBottom: "0.2rem" }}>
          {validation.hasUppercase ? "✓" : "✗"} At least one uppercase letter
        </li>
        <li style={{ color: validation.hasLowercase ? "#28a745" : "#dc3545", marginBottom: "0.2rem" }}>
          {validation.hasLowercase ? "✓" : "✗"} At least one lowercase letter
        </li>
        <li style={{ color: validation.hasNumber ? "#28a745" : "#dc3545", marginBottom: "0.2rem" }}>
          {validation.hasNumber ? "✓" : "✗"} At least one number
        </li>
        <li style={{ color: validation.hasSpecial ? "#28a745" : "#dc3545", marginBottom: "0.2rem" }}>
          {validation.hasSpecial ? "✓" : "✗"} At least one special character (!@#$%^&*)
        </li>
      </ul>
      <input
        type="password"
        placeholder="Confirm New Password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        style={{ margin: "1rem", padding: "0.5rem",width: "300px" }}
      />
      <br />
      <button
        onClick={handleSubmit}
        style={{ padding: "0.7rem 2rem" }}
        disabled={!isReadyToSubmit || isLoading}
      >
        {isLoading ? "Submitting..." : "Submit"}
      </button>
      {status && (
        <p style={{ color: status.toLowerCase().includes("success") ? "green" : "red" }}>
          {status}
        </p>
      )}
    </div>
  );
}
