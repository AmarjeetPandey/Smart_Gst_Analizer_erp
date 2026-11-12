import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/dashboardService';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [summary, setSummary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [showProductCatalog, setShowProductCatalog] = useState(false);
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    const loadSummary = async () => {
      try {
        const data = await dashboardService.getSummary();
        setSummary(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    loadSummary();
    dashboardService.getAnalyzerInsights().then((data) => setInsights(data.insights || [])).catch((error) => console.error(error));
  }, []);

  const handleProductsClick = async () => {
    if (showProductCatalog) {
      setShowProductCatalog(false);
      return;
    }

    try {
      setLoadingProducts(true);
      const data = await dashboardService.getProducts();
      const activeProducts = data.filter((product) => product.is_active !== false);
      setProducts(activeProducts);
      setShowProductCatalog(true);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingProducts(false);
    }
  };

  return (
    <div className="dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero__shade" />
        <div className="container-main dashboard-hero__content">
          <nav className="dashboard-nav">
            <div className="brand-lockup">
              <span className="brand-mark">S</span>
              <span>SmartGST <small>ERP</small></span>
            </div>
            <div className="dashboard-nav__actions">
              <span className="live-status"><span /> Live workspace</span>
              <button onClick={logout} className="hero-logout">Sign out</button>
            </div>
          </nav>
          <div className="dashboard-welcome">
            <div>
              <p className="eyebrow">Business overview · {new Date().toLocaleDateString('en-IN', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
              <h1>Your business, with full Analytics.</h1>
              <p className="dashboard-welcome__copy">Welcome back, {user?.name || 'business owner'}. Here is what is moving today.</p>
            </div>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <Link to="/ai-center" className="hero-action">Open AI Center <span>↗</span></Link>
              <Link to="/business" className="hero-action">Open business workspace <span>↗</span></Link>
            </div>
          </div>
        </div>
      </header>

      <main className="container-main dashboard-content">
        {loading ? (
          <div className="dashboard-loading">Loading your business data...</div>
        ) : (
          <>
            <section className="metric-grid">
              <div className="metric-card metric-card--coral">
                <div className="metric-card__top"><span>Total sales</span><b>↗</b></div>
                <p>₹{Number(summary?.total_sales || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                <small>Across your invoices</small>
              </div>
              <div className="metric-card metric-card--ink">
                <div className="metric-card__top"><span>Outstanding</span><b>!</b></div>
                <p>₹{Number(summary?.outstanding || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                <small>Pending payments</small>
              </div>
              <div className="metric-card metric-card--mint">
                <div className="metric-card__top"><span>Purchases</span><b>◆</b></div>
                <p>₹{Number(summary?.total_purchases || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                <small>Recorded purchases</small>
              </div>
              <div className="metric-card metric-card--gold">
                <div className="metric-card__top"><span>Collected</span><b>✓</b></div>
                <p>₹{Number(summary?.paid_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                <small>Received from invoices</small>
              </div>
            </section>

            <section className="quick-actions">
              <div><span className="eyebrow eyebrow--dark">Quick actions</span><strong>Keep the day moving</strong></div>
              <Link to="/business" className="quick-action quick-action--orange"><span>＋</span> New invoice</Link>
              <Link to="/business" className="quick-action quick-action--blue"><span>＋</span> Add customer</Link>
              <Link to="/business" className="quick-action quick-action--green"><span>＋</span> Add product</Link>
            </section>

            <section className="analyzer-strip">
              <div className="analyzer-strip__title"><span className="eyebrow eyebrow--dark">Smart analyzer</span><strong>Signals worth your attention</strong></div>
              {insights.slice(0, 3).map((insight) => (
                <div className={`analyzer-insight analyzer-insight--${insight.severity}`} key={`${insight.type}-${insight.title}`}>
                  <span className="analyzer-insight__dot" />
                  <div><b>{insight.title}</b><small>{insight.message}</small></div>
                </div>
              ))}
            </section>

            <section className="dashboard-columns">
              <div className="dashboard-panel dashboard-panel--invoices">
                <div className="panel-heading"><div><span className="eyebrow eyebrow--dark">Sales pulse</span><h2>Recent invoices</h2></div><Link to="/business">View all ↗</Link></div>
                <div className="invoice-list">
                  {summary?.recent_invoices?.length ? summary.recent_invoices.map((invoice) => (
                    <div className="invoice-row" key={invoice.id}>
                      <span className="invoice-avatar">{invoice.invoice_number?.slice(-2) || 'IN'}</span>
                      <div className="invoice-row__name"><strong>{invoice.invoice_number}</strong><small>{invoice.status?.replace('_', ' ')}</small></div>
                      <div className="invoice-row__amount"><strong>₹{Number(invoice.total_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong><small>Paid ₹{Number(invoice.paid_amount || 0).toFixed(2)}</small></div>
                    </div>
                  )) : <p className="empty-state">No invoices yet. Create your first one from the workspace.</p>}
                </div>
              </div>

              <button type="button" className="dashboard-panel catalog-panel" onClick={handleProductsClick}>
                <div className="catalog-panel__image" />
                <div className="catalog-panel__content"><span className="eyebrow">Inventory glance</span><h2>{summary?.total_products || 0} products</h2><p>Open your active product catalog</p><span className="catalog-link">Explore catalog <b>↗</b></span></div>
              </button>
            </section>

            <section className="dashboard-foot-metrics">
              <button
                type="button"
                className="mini-stat mini-stat--blue"
                onClick={handleProductsClick}
              >
                <span>Products in catalog</span><strong>{summary?.total_products || 0}</strong>
              </button>
              <div className="mini-stat mini-stat--yellow"><span>Registered customers</span><strong>{summary?.total_customers || 0}</strong></div>
              <div className="mini-stat mini-stat--violet"><span>Net position</span><strong>₹{Number((summary?.total_sales || 0) - (summary?.total_purchases || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
            </section>

            {showProductCatalog && (
              <div className="dashboard-panel catalog-table-panel">
                <div className="panel-heading"><div><span className="eyebrow eyebrow--dark">Product detail</span><h2>Active product catalog</h2></div><button type="button" onClick={handleProductsClick}>Close ×</button></div>
                {loadingProducts ? (
                  <p>Loading products...</p>
                ) : products.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="table w-full">
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>SKU</th>
                          <th>Price</th>
                          <th>Quantity</th>
                          <th>Sales Qty</th>
                          <th>Profit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {products.map((product) => {
                          const profit = Number(product.sales_quantity || 0) * (Number(product.selling_price || 0) - Number(product.purchase_price || 0));

                          return (
                            <tr key={product.id}>
                              <td>{product.name}</td>
                              <td>{product.sku || '-'}</td>
                              <td>₹{Number(product.selling_price || 0).toFixed(2)}</td>
                              <td>{Number(product.quantity || 0)}</td>
                              <td>{Number(product.sales_quantity || 0)}</td>
                              <td>₹{profit.toFixed(2)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No active products found.</p>
                )}
              </div>
            )}

          </>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
