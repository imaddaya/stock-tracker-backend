import { useEffect, useState } from "react";
import { useRouter } from "next/router";

type StockSummary = {
  symbol: string;
  name: string;           
  open?: number;                     
  high?: number;                      
  low?: number;    
  price?: number;     
  volume?: number;                     
  latest_trading_day?: string;        
  previous_close?: number;         
  change?: number;                   
  change_percent?: string; 
};

export default function MyStocks() {
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loadingSymbol, setLoadingSymbol] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    fetch(
      "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/portfolio/summary",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setStocks(data);
        } else {
          console.warn("Unexpected summary format:", data);
        }
      })
      .catch(console.error);
  }, [router]);

  const handleRemove = async (symbol: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const res = await fetch(
        "https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/portfolio/remove",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ stock_symbol: symbol }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        alert(`Failed to remove stock: ${errorData.detail || "Unknown error"}`);
        return;
      }

      setStocks((prev) => prev.filter((stock) => stock.symbol !== symbol));
    } catch (err) {
      console.error("Error removing stock:", err);
      alert("An error occurred while removing the stock.");
    }
  };

  const handleRefresh = async (symbol: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    setLoadingSymbol(symbol);
    try {
      const res = await fetch(
        `https://a1a01c3c-3efd-4dbc-b944-2de7bec0d5c1-00-b7jcjcvwjg4y.pike.replit.dev/portfolio/summary/${symbol}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        alert(`Failed to refresh stock: ${errorData.detail || "Unknown error"}`);
        setLoadingSymbol(null);
        return;
      }

      const updatedStock: StockSummary = await res.json();

      setStocks((prev) =>
        prev.map((stock) => (stock.symbol === symbol ? updatedStock : stock))
      );
    } catch (err) {
      console.error("Error refreshing stock:", err);
      alert("An error occurred while refreshing the stock.");
    }
    setLoadingSymbol(null);
  };

  return (
    <div style={{ fontFamily: "'Poppins', sans-serif", padding: "2rem" }}>
      <div style={{ marginBottom: "1rem" }}>
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

      <h1 style={{ marginBottom: "2rem" }}>My Stocks</h1>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill,minmax(250px,1fr))",
          gap: "1.5rem",
        }}
      >
        {stocks.length === 0 && <p>No stocks in your portfolio.</p>}
        {stocks.map(({ symbol, name, price, change_percent, open, high, low, volume, latest_trading_day, previous_close, change }) => (

          <div
            key={symbol}
            style={{
              border: "1px solid #ccc",
              borderRadius: "10px",
              padding: "1rem",
              boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
              position: "relative",
            }}
          >
            {/* Symbol and refresh button container */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "0.5rem",
              }}
            >
              <h3 style={{ margin: 0 }}>{symbol}</h3>
              <button
                onClick={() => handleRefresh(symbol)}
                disabled={loadingSymbol === symbol}
                title="Refresh stock data"
                style={{
                  fontSize: "0.8rem",
                  padding: "0.15rem 0.5rem",
                  cursor: "pointer",
                  borderRadius: "4px",
                  border: "1px solid #0070f3",
                  backgroundColor:
                    loadingSymbol === symbol ? "#cce4ff" : "white",
                  color: "#0070f3",
                }}
              >
                {loadingSymbol === symbol ? "Loading..." : "Refresh"}
              </button>
            </div>

            <p style={{ margin: "0.3rem 0" }}>
              <strong>Company:</strong> {name || "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Open:</strong> {typeof open === "number" ? open.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>High:</strong> {typeof high === "number" ? high.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Low:</strong> {typeof low === "number" ? low.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Price:</strong> {typeof price === "number" ? price.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Volume:</strong> {typeof volume === "number" ? volume.toLocaleString() : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Latest Trading Day:</strong> {latest_trading_day || "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Previous Close:</strong> {typeof previous_close === "number" ? previous_close.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Change:</strong> {typeof change === "number" ? change.toFixed(2) : "N/A"}
            </p>
            <p style={{ margin: "0.3rem 0" }}>
              <strong>Change Percent:</strong> {change_percent ?? "N/A"}
            </p>

            <div
              style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}
            >
              <button
                style={{
                  flex: 1,
                  padding: "0.5rem",
                  cursor: "pointer",
                  backgroundColor: "#e74c3c",
                  border: "none",
                  color: "white",
                  borderRadius: "5px",
                }}
                onClick={() => handleRemove(symbol)}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
