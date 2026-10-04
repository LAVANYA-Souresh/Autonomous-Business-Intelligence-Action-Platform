
import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [metrics, setMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(true);

  const [revenueTrend, setRevenueTrend] = useState([]);
  const [trendLoading, setTrendLoading] = useState(true);

  const [lastUpdated, setLastUpdated] = useState(null);

  // Refresh live business data
  const refreshData = () => {
    setMetricsLoading(true);
    setTrendLoading(true);

    fetch("http://127.0.0.1:8000/metrics")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to refresh metrics");
        }

        return response.json();
      })
      .then((data) => {
        setMetrics(data);
        setMetricsLoading(false);
      })
      .catch(() => {
        setMetricsLoading(false);
      });

    fetch("http://127.0.0.1:8000/revenue-trend")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to refresh revenue trend");
        }

        return response.json();
      })
      .then((data) => {
        setRevenueTrend(data.data);
        setTrendLoading(false);
        setLastUpdated(new Date());
      })
      .catch(() => {
        setTrendLoading(false);
      });
  };

  // Average Order Value
  const averageOrderValue =
    metrics && metrics.orders > 0
      ? metrics.revenue / metrics.orders
      : 0;

  // Absolute revenue difference
  const revenueDifference =
    revenueTrend.length >= 2
      ? revenueTrend[revenueTrend.length - 1].revenue -
        revenueTrend[revenueTrend.length - 2].revenue
      : 0;

  // Revenue percentage change
  const revenueChange =
    revenueTrend.length >= 2
      ? ((revenueTrend[revenueTrend.length - 1].revenue -
          revenueTrend[revenueTrend.length - 2].revenue) /
          revenueTrend[revenueTrend.length - 2].revenue) *
        100
      : 0;

  // Load live business metrics when the page opens
  useEffect(() => {
    fetch("http://127.0.0.1:8000/metrics")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load metrics");
        }

        return response.json();
      })
      .then((data) => {
        setMetrics(data);
        setMetricsLoading(false);
      })
      .catch(() => {
        setMetricsLoading(false);
      });
  }, []);

  // Load revenue trend when the page opens
  useEffect(() => {
    fetch("http://127.0.0.1:8000/revenue-trend")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load revenue trend");
        }

        return response.json();
      })
      .then((data) => {
        setRevenueTrend(data.data);
        setTrendLoading(false);

        // Set timestamp when initial data finishes loading
        setLastUpdated(new Date());
      })
      .catch(() => {
        setTrendLoading(false);
      });
  }, []);

  // Ask the business AI
  const askQuestion = async (selectedQuestion = question) => {
    if (!selectedQuestion.trim()) {
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: selectedQuestion,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Something went wrong."
        );
      }

      setAnswer(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Format numbers using Indian numbering
  const formatRevenue = (value) => {
    return new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="app">

      {/* Header */}
      <header className="topbar">
        <div>
          <h1>AI Business Intelligence</h1>

          <p>
            Autonomous Business Operations & Analytics Platform
          </p>
        </div>

        <div className="status-pill">
          <span className="status-dot"></span>
          API Online
        </div>
      </header>

      <main className="container">

        {/* Live Business Metrics */}
        <section className="metrics-section">

          <div className="section-heading">

            <div>
              <span className="eyebrow">
                LIVE BUSINESS METRICS
              </span>

              <h2>
                {metrics?.period || "Business Overview"}
              </h2>

              {lastUpdated && (
                <span className="last-updated">
                  Last updated:{" "}
                  {lastUpdated.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              )}
            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={refreshData}
              disabled={metricsLoading || trendLoading}
            >
              {metricsLoading || trendLoading
                ? "Refreshing..."
                : "↻ Refresh Data"}
            </button>

          </div>

          {metricsLoading ? (
            <div className="metrics-loading">
              Loading business metrics...
            </div>
          ) : metrics ? (
            <div className="metrics-grid">

              {/* Revenue */}
              <div className="metric-card">
                <span className="metric-label">
                  Revenue
                </span>

                <strong className="metric-value">
                  ₹{formatRevenue(metrics.revenue)}
                </strong>

                <span className="metric-description">
                  Total revenue
                </span>

              </div>

              {/* Orders */}
              <div className="metric-card">
                <span className="metric-label">
                  Orders
                </span>

                <strong className="metric-value">
                  {formatRevenue(metrics.orders)}
                </strong>

                <span className="metric-description">
                  Orders processed
                </span>
              </div>

              {/* Return Rate */}
              <div className="metric-card">
                <span className="metric-label">
                  Return Rate
                </span>

                <strong className="metric-value">
                  {metrics.return_rate.toFixed(2)}%
                </strong>

                <span className="metric-description">
                  Order return rate
                </span>
              </div>

              {/* Average Order Value */}
              <div className="metric-card">
                <span className="metric-label">
                  Average Order Value
                </span>

                <strong className="metric-value">
                  ₹{formatRevenue(averageOrderValue)}
                </strong>

                <span className="metric-description">
                  Average revenue per order
                </span>
              </div>

            </div>
          ) : (
            <div className="metrics-loading">
              Unable to load business metrics.
            </div>
          )}

        </section>

        {/* Revenue Trend */}
        <section className="trend-section">

          <div className="section-heading">

            <div>
              <span className="eyebrow">
                REVENUE TREND
              </span>

              <h2>
                Monthly Revenue Performance
              </h2>
            </div>

          </div>

          {trendLoading ? (
            <div className="metrics-loading">
              Loading revenue trend...
            </div>
          ) : revenueTrend.length > 0 ? (
            <div className="trend-card">

              {/* Revenue Change */}
              <div className="trend-summary">

                <div>
                  <span className="metric-label">
                    Revenue Change
                  </span>

                  <strong
                    className={`trend-change ${
                      revenueChange >= 0
                        ? "positive"
                        : "negative"
                    }`}
                  >
                    {revenueChange >= 0 ? "+" : ""}
                    {revenueChange.toFixed(2)}%
                  </strong>

                  <span className="metric-description">
                    April → May 2025
                  </span>

                  <span className="trend-difference">
                    {revenueDifference >= 0 ? "+" : "-"}₹
                    {formatRevenue(
                      Math.abs(revenueDifference)
                    )}
                  </span>
                </div>

              </div>

              {/* Chart Label */}
              <div className="chart-label">
                Revenue (₹)
              </div>

              {/* Revenue Bars */}
              <div className="trend-bars">

                {revenueTrend.map((item) => {

                  const maxRevenue = Math.max(
                    ...revenueTrend.map(
                      (entry) => entry.revenue
                    )
                  );

                  const height =
                    (item.revenue / maxRevenue) * 100;

                  return (
                    <div
                      className="trend-column"
                      key={item.month}
                    >

                      <div className="trend-value">
                        ₹{formatRevenue(item.revenue)}
                      </div>

                      <div className="trend-bar-container">

                        <div
                          className="trend-bar"
                          style={{
                            height: `${height}%`,
                          }}
                        ></div>

                      </div>

                      <div className="trend-month">
                        {item.month}
                      </div>

                    </div>
                  );
                })}

              </div>

            </div>
          ) : (
            <div className="metrics-loading">
              Unable to load revenue trend.
            </div>
          )}

        </section>

        {/* Ask AI */}
        <section className="question-card">

          <div className="eyebrow">
            ASK THE BUSINESS AI
          </div>

          <h2>
            Ask questions about your business data.
          </h2>

          <p>
            Use natural language. The system converts your
            question into validated SQL and retrieves verified
            business evidence.
          </p>

          <div className="question-box">

            <input
              type="text"
              value={question}
              onChange={(e) =>
                setQuestion(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  askQuestion();
                }
              }}
              placeholder="Example: Which product generated the most revenue in May 2025?"
            />

            <button
              type="button"
              onClick={() => askQuestion()}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Ask AI"}
            </button>

          </div>

          <div className="preset-questions">

            <button
              type="button"
              onClick={() => {
                const q =
                  "Which product generated the most revenue in May 2025?";

                setQuestion(q);
                askQuestion(q);
              }}
            >
              Highest revenue product
            </button>

            <button
              type="button"
              onClick={() => {
                const q =
                  "Which region generated the most revenue in May 2025?";

                setQuestion(q);
                askQuestion(q);
              }}
            >
              Highest revenue region
            </button>

            <button
              type="button"
              onClick={() => {
                const q =
                  "How did revenue change between April and May 2025?";

                setQuestion(q);
                askQuestion(q);
              }}
            >
              Revenue trend
            </button>

          </div>

        </section>

        {/* Loading Result */}
        {loading && (
          <section className="result-card loading-card">

            <div className="eyebrow">
              AI ANALYSIS
            </div>

            <h3>
              Analyzing business data...
            </h3>

            <p>
              Generating SQL, validating the query,
              retrieving PostgreSQL evidence, and
              verifying the result.
            </p>

          </section>
        )}

        {/* Error Result */}
        {error && (
          <section className="result-card error-card">

            <div className="eyebrow">
              ERROR
            </div>

            <h3>
              Unable to complete analysis
            </h3>

            <p>
              {error}
            </p>

          </section>
        )}

        {/* Verified Answer */}
        {answer && !loading && (
          <section className="result-card">

            <div className="result-header">

              <div>
                <div className="eyebrow">
                  VERIFIED BUSINESS ANSWER
                </div>

                <h3>
                  AI Analysis Result
                </h3>
              </div>

              <span className="verified-badge">
                ✓ VERIFIED
              </span>

            </div>

            <div className="answer">
              {answer}
            </div>

            <div className="evidence-note">
              Answer generated from validated PostgreSQL
              business data.
            </div>

          </section>
        )}

        {/* System Architecture */}
        <section className="architecture">

          <div className="eyebrow">
            SYSTEM ARCHITECTURE
          </div>

          <h2>
            From natural language to verified business
            intelligence.
          </h2>

          <div className="architecture-grid">

            <div className="architecture-card">
              <span>01</span>

              <h3>
                Natural Language
              </h3>

              <p>
                Business users ask questions without
                writing SQL.
              </p>
            </div>

            <div className="architecture-card">
              <span>02</span>

              <h3>
                AI Orchestration
              </h3>

              <p>
                AI plans the analysis and generates
                the required query.
              </p>
            </div>

            <div className="architecture-card">
              <span>03</span>

              <h3>
                Verified Data
              </h3>

              <p>
                SQL is validated before accessing
                PostgreSQL business data.
              </p>
            </div>

            <div className="architecture-card">
              <span>04</span>

              <h3>
                Actionable Insight
              </h3>

              <p>
                Verified results are transformed into
                clear business answers.
              </p>
            </div>

          </div>

        </section>

      </main>

      <footer>
        NovaMart AI Business Intelligence • Portfolio Project
      </footer>

    </div>
  );
}

export default App;

