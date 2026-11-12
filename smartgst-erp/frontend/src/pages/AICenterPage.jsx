import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../services/api';

const initialState = {
  business: null,
  forecast: null,
  anomalies: null,
  alerts: null,
  copilot: { answer: 'Ask a question about sales, purchases, products, invoices, or inventory.' },
};

const copilotQuestionOptions = [
  { group: 'Sales', label: 'How much did I sell this month?', question: 'How much did I sell this month?' },
  { group: 'Sales', label: 'How much did I sell last month?', question: 'How much did I sell last month?' },
  { group: 'Sales', label: 'How much have I sold this year?', question: 'How much have I sold this year?' },
  { group: 'Sales', label: 'Compare this month with last month', question: 'Compare this month sales with last month' },
  { group: 'Products', label: 'Which product sold the most?', question: 'Which product sold the most?' },
  { group: 'Products', label: 'Which product sold the most this month?', question: 'Which product sold the most this month?' },
  { group: 'Purchases', label: 'How much did I purchase this month?', question: 'How much did I purchase this month?' },
  { group: 'Purchases', label: 'How much did I purchase last month?', question: 'How much did I purchase last month?' },
  { group: 'Inventory', label: 'Which products are low in stock?', question: 'Which products are low in stock?' },
  { group: 'Customers', label: 'Who are my top customers?', question: 'Who are my top customers?' },
  { group: 'Invoices', label: 'How many invoices are paid and unpaid?', question: 'How many invoices are paid and unpaid?' },
  { group: 'Invoices', label: 'Invoice payment status this month', question: 'How many invoices are paid and unpaid this month?' },
  { group: 'Profit', label: 'What is my sales-minus-purchases this month?', question: 'What is my profit this month?' },
  { group: 'Profit', label: 'What is my sales-minus-purchases last month?', question: 'What is my profit last month?' },
  { group: 'Business summary', label: 'Show my business summary', question: 'Show my business summary' },
];

const formatINR = (value) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount)
    : 'Not available';
};

const formatDate = (value) => {
  if (!value) return '';
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString('en-IN');
};

const formatPeriod = (period) => (
  period?.start && period?.end
    ? `${formatDate(period.start)} – ${formatDate(period.end)}`
    : 'Period unavailable'
);

const SectionState = ({ status, message, emptyMessage, children }) => {
  if (status === 'error') return <p className="ai-section-state ai-section-state--error">{message || 'This section could not be loaded.'}</p>;
  if (status === 'loading') return <p className="ai-section-state">Loading data…</p>;
  if (emptyMessage) return <p className="ai-section-state">{emptyMessage}</p>;
  return children;
};

const AICenterPage = () => {
  const { user, logout } = useAuth();
  const [data, setData] = useState(initialState);
  const [sectionStates, setSectionStates] = useState({
    business: 'loading',
    forecast: 'loading',
    anomalies: 'loading',
    alerts: 'loading',
  });
  const [question, setQuestion] = useState('');
  const [selectedQuestion, setSelectedQuestion] = useState('');
  const [loading, setLoading] = useState(true);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotError, setCopilotError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setSectionStates({ business: 'loading', forecast: 'loading', anomalies: 'loading', alerts: 'loading' });
    const requests = [
      ['business', '/ai/business-summary'],
      ['forecast', '/ai/forecast/summary'],
      ['anomalies', '/ai/anomalies'],
      ['alerts', '/ai/alerts'],
    ];
    const results = await Promise.allSettled(requests.map(([, path]) => apiClient.get(path)));
    const nextData = {};
    const nextStates = {};
    results.forEach((result, index) => {
      const key = requests[index][0];
      if (result.status === 'fulfilled') {
        nextData[key] = result.value.data;
        nextStates[key] = 'loaded';
      } else {
        console.error(`AI Center ${key} request failed`, result.reason);
        nextData[key] = { status: 'error', message: 'Data is temporarily unavailable. Please retry.' };
        nextStates[key] = 'error';
      }
    });
    setData((current) => ({ ...current, ...nextData }));
    setSectionStates(nextStates);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const askCopilot = async (event) => {
    event?.preventDefault();
    if (!question.trim() || copilotLoading) return;
    try {
      setCopilotLoading(true);
      setCopilotError('');
      const response = await apiClient.post('/ai/copilot/query', { question: question.trim() });
      setData((current) => ({ ...current, copilot: response.data }));
    } catch (error) {
      console.error('AI Copilot request failed', error);
      setCopilotError('The answer could not be loaded. Please try again.');
    } finally {
      setCopilotLoading(false);
    }
  };

  const kpis = data.business?.kpis || {};
  const overviewCards = [
    { label: 'Recorded sales', value: sectionStates.business === 'loaded' ? formatINR(kpis.total_sales) : '—', tone: 'coral' },
    { label: 'Month to date', value: sectionStates.business === 'loaded' ? formatINR(kpis.current_month_sales) : '—', tone: 'mint' },
    { label: 'Invoices', value: sectionStates.business === 'loaded' ? (kpis.order_count ?? 0).toLocaleString('en-IN') : '—', tone: 'ink' },
    { label: 'Active alerts', value: sectionStates.alerts === 'loaded' ? (data.alerts?.count ?? 0).toLocaleString('en-IN') : '—', tone: 'gold' },
  ];

  if (loading) {
    return (
      <div className="dashboard-shell">
        <div className="container-main dashboard-content">
          <div className="dashboard-loading">Loading SmartGST AI Center…</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-shell ai-center-shell">
      <header className="dashboard-hero ai-center-hero">
        <div className="dashboard-hero__shade" />
        <div className="container-main dashboard-hero__content">
          <nav className="dashboard-nav">
            <div className="brand-lockup">
              <span className="brand-mark">S</span>
              <span>SmartGST <small>ERP</small></span>
            </div>
            <div className="dashboard-nav__actions">
              <span className="live-status"><span /> AI Center</span>
              <button onClick={logout} className="hero-logout">Sign out</button>
            </div>
          </nav>
          <div className="dashboard-welcome ai-center-welcome">
            <div>
              <p className="eyebrow">AI workspace · SmartGST</p>
              <h1>AI Center</h1>
              <p className="dashboard-welcome__copy">Welcome back, {user?.name || 'owner'}. Business intelligence, forecasting, anomaly review and alerts are available in one place.</p>
            </div>
            <div className="ai-center-actions">
              <Link to="/dashboard" className="hero-action">Back to dashboard <span>↗</span></Link>
              <Link to="/business" className="hero-action">Open business workspace <span>↗</span></Link>
            </div>
          </div>
        </div>
      </header>

      <main className="container-main dashboard-content">
        <section className="metric-grid ai-metric-grid" aria-label="AI Center overview">
          {overviewCards.map((item) => (
            <div key={item.label} className={`metric-card metric-card--${item.tone}`}>
              <div className="metric-card__top"><span>{item.label}</span><b>AI</b></div>
              <p>{item.value}</p>
              <small>{item.label === 'Month to date' ? 'Invoice totals' : 'Authenticated business records'}</small>
            </div>
          ))}
        </section>

        <section className="dashboard-columns ai-center-row">
          <div className="dashboard-panel dashboard-panel--invoices ai-panel">
            <div className="panel-heading">
              <div><span className="eyebrow eyebrow--dark">Business Intelligence</span><h2>AI Business Summary</h2></div>
              <button type="button" onClick={loadData} className="ai-refresh-button">Refresh</button>
            </div>
            <SectionState
              status={sectionStates.business}
              message={data.business?.message}
            >
              <p className="ai-panel__text">{data.business?.summary || 'Business summary is not available.'}</p>
              <div className="ai-panel__meta">
                <div><strong>Current period sales:</strong> {formatINR(kpis.current_month_sales)} <small>({formatPeriod(data.business?.periods?.current)})</small></div>
                <div><strong>Previous period sales:</strong> {formatINR(kpis.previous_month_sales)} <small>({formatPeriod(data.business?.periods?.previous)})</small></div>
                <div>
                  <strong>Change:</strong>{' '}
                  {kpis.period_change_percent === null || kpis.period_change_percent === undefined
                    ? 'Not calculable (previous-period sales are zero)'
                    : `${kpis.period_change_percent > 0 ? '+' : ''}${Number(kpis.period_change_percent).toFixed(2)}%`}
                </div>
                <div><strong>Average invoice value:</strong> {formatINR(kpis.average_order_value)} <small>(recorded sales ÷ invoices)</small></div>
                <div><strong>Top-selling product:</strong> {data.business?.top_products?.[0]?.product || 'No product-linked sales found'}</div>
                {kpis.total_profit_loss !== null && kpis.total_profit_loss !== undefined && (
                  <div><strong>Sales minus purchases:</strong> {formatINR(kpis.total_profit_loss)} <small>(existing recorded calculation)</small></div>
                )}
              </div>
            </SectionState>
          </div>

          <div className="dashboard-panel dashboard-panel--invoices ai-panel">
            <div className="panel-heading">
              <div><span className="eyebrow eyebrow--dark">Historical trend</span><h2>Sales Forecast</h2></div>
            </div>
            <SectionState
              status={sectionStates.forecast}
              message={data.forecast?.message}
              emptyMessage={data.forecast?.status === 'insufficient_data' ? data.forecast?.message : null}
            >
              {data.forecast?.sales_forecast ? (
                <>
                  <p className="ai-panel__text">{data.forecast.message}</p>
                  <div className="ai-panel__meta">
                    {['next_7_days', 'next_30_days', 'next_90_days'].map((period) => (
                      <div key={period}>
                        <strong>{period.replace('next_', 'Next ').replace('_days', ' days')}:</strong>{' '}
                        {formatINR(data.forecast.sales_forecast[period])}
                        <small> ({formatPeriod(data.forecast.forecast_periods?.[period])})</small>
                      </div>
                    ))}
                    <div><strong>Historical context:</strong> {data.forecast.historical_context?.days_with_sales || 0} sales days in the last 90 calendar days; 28-day sales {formatINR(data.forecast.historical_context?.last_28_days_sales)}.</div>
                  </div>
                </>
              ) : (
                <p className="ai-section-state">Forecast is unavailable because no reliable estimate could be calculated.</p>
              )}
            </SectionState>
          </div>
        </section>

        <section className="dashboard-columns ai-center-row">
          <div className="dashboard-panel dashboard-panel--invoices ai-panel">
            <div className="panel-heading">
              <div><span className="eyebrow eyebrow--dark">AI Copilot</span><h2>Ask SmartGST</h2></div>
            </div>
            <p className="ai-copilot-hint">Choose a suggested question or type your own, then select Ask.</p>
            <form className="ai-query-form" onSubmit={askCopilot}>
              <label className="ai-query-label" htmlFor="ai-question-picker">Suggested questions</label>
              <select
                id="ai-question-picker"
                value={selectedQuestion}
                onChange={(event) => {
                  setSelectedQuestion(event.target.value);
                  if (event.target.value) setQuestion(event.target.value);
                }}
                className="ai-query-input ai-question-select"
              >
                <option value="">Choose a business question…</option>
                {[...new Set(copilotQuestionOptions.map((option) => option.group))].map((group) => (
                  <optgroup key={group} label={group}>
                    {copilotQuestionOptions
                      .filter((option) => option.group === group)
                      .map((option) => (
                        <option key={option.question} value={option.question}>{option.label}</option>
                      ))}
                  </optgroup>
                ))}
              </select>
              <div className="ai-query-row">
                <input
                  value={question}
                  onChange={(event) => {
                    setQuestion(event.target.value);
                    setSelectedQuestion('');
                  }}
                  placeholder="Or type a question about your business"
                  className="ai-query-input"
                  aria-label="Ask SmartGST a business question"
                />
              <button
                type="submit"
                className="quick-action quick-action--orange ai-query-button"
                disabled={copilotLoading || !question.trim()}
              >
                {copilotLoading ? 'Thinking…' : 'Ask'}
              </button>
              </div>
            </form>
            <div className="ai-answer-box" aria-live="polite">
              {copilotError || data.copilot?.answer || 'Ask a question about your business records.'}
            </div>
          </div>

          <div className="dashboard-panel dashboard-panel--invoices ai-panel">
            <div className="panel-heading">
              <div><span className="eyebrow eyebrow--dark">Anomalies</span><h2>Review queue</h2></div>
            </div>
            <SectionState
              status={sectionStates.anomalies}
              message={data.anomalies?.message}
              emptyMessage={data.anomalies?.anomalies?.length === 0 ? 'No inventory anomalies detected.' : null}
            >
              <div className="ai-panel__meta">
                <div><strong>Active warnings:</strong> {data.anomalies?.count ?? 0}</div>
                {data.anomalies?.anomalies?.map((item) => (
                  <div key={item.id} className="ai-anomaly-item">
                    <div className="ai-anomaly-item__heading"><strong>{item.product || item.anomaly_type.replaceAll('_', ' ')}</strong><span className={`ai-severity ai-severity--${item.severity?.toLowerCase()}`}>{item.severity}</span></div>
                    <div>{item.reason}</div>
                    {item.recommended_action && <small>Recommended action: {item.recommended_action}</small>}
                  </div>
                ))}
              </div>
            </SectionState>
          </div>
        </section>

        <section className="dashboard-panel ai-panel ai-alert-panel">
          <div className="panel-heading">
            <div><span className="eyebrow eyebrow--dark">Automated Alerts</span><h2>SmartGST Alerts</h2></div>
          </div>
          <SectionState
            status={sectionStates.alerts}
            message={data.alerts?.message}
            emptyMessage={data.alerts?.alerts?.length === 0 ? 'No active alerts were raised by the existing business rules.' : null}
          >
            <div className="ai-alert-list">
              {data.alerts?.alerts?.map((alert) => (
                <div key={alert.alert_id} className="ai-alert-card">
                  <div className="ai-alert-card__title">
                    {alert.title}
                    <span className={`ai-severity ai-severity--${alert.severity?.toLowerCase()}`}>{alert.severity}</span>
                  </div>
                  <div className="ai-alert-card__desc">{alert.description}</div>
                  {alert.recommended_action && <div className="ai-alert-card__action">Recommended action: {alert.recommended_action}</div>}
                </div>
              ))}
            </div>
          </SectionState>
        </section>
      </main>
    </div>
  );
};

export default AICenterPage;
