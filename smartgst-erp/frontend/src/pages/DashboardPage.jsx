import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/dashboardService';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [summary, setSummary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [catalogTotal, setCatalogTotal] = useState(0);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [showProductCatalog, setShowProductCatalog] = useState(false);

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
      setCatalogTotal(activeProducts.reduce((total, product) => total + (Number(product.quantity || 0) * Number(product.purchase_price || 0)), 0));
      setShowProductCatalog(true);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingProducts(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="container-main py-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome, {user?.name}</p>
          </div>
          <div className="flex gap-2">
            <Link to="/business" className="btn-primary">Manage Business</Link>
            <button onClick={logout} className="btn-danger">Logout</button>
          </div>
        </div>
      </header>

      <main className="container-main py-8">
        {loading ? (
          <p>Loading your business data...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-8">
              <div className="card">
                <h3 className="text-gray-600 text-sm font-medium">Total Sales</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">₹{Number(summary?.total_sales || 0).toFixed(2)}</p>
                <p className="text-gray-500 text-xs mt-1">Across your invoices</p>
              </div>

              <div className="card">
                <h3 className="text-gray-600 text-sm font-medium">Outstanding</h3>
                <p className="text-3xl font-bold text-red-600 mt-2">₹{Number(summary?.outstanding || 0).toFixed(2)}</p>
                <p className="text-gray-500 text-xs mt-1">Pending payments</p>
              </div>

              <div className="card">
                <h3 className="text-gray-600 text-sm font-medium">Total Purchases</h3>
                <p className="text-3xl font-bold text-purple-600 mt-2">₹{catalogTotal.toFixed(2)}</p>
                <p className="text-gray-500 text-xs mt-1">Active catalog price total</p>
              </div>

              <div className="card">
                <h3 className="text-gray-600 text-sm font-medium">Total Paid Amount</h3>
                <p className="text-3xl font-bold text-green-600 mt-2">₹{Number(summary?.paid_amount || 0).toFixed(2)}</p>
                <p className="text-gray-500 text-xs mt-1">Amount received from invoices</p>
              </div>

              <button
                type="button"
                className="card text-left cursor-pointer hover:shadow-md transition"
                onClick={handleProductsClick}
              >
                <h3 className="text-gray-600 text-sm font-medium">Products</h3>
                <p className="text-3xl font-bold text-blue-600 mt-2">{summary?.total_products || 0}</p>
                <p className="text-gray-500 text-xs mt-1">Click to view active catalog</p>
              </button>

              <div className="card">
                <h3 className="text-gray-600 text-sm font-medium">Customers</h3>
                <p className="text-3xl font-bold text-yellow-600 mt-2">{summary?.total_customers || 0}</p>
                <p className="text-gray-500 text-xs mt-1">Registered clients</p>
              </div>
            </div>

            {showProductCatalog && (
              <div className="card mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Product Catalog</h2>
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

            <div className="card">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Invoices</h2>
              <div className="overflow-x-auto">
                <table className="table w-full">
                  <thead>
                    <tr>
                      <th>Invoice</th>
                      <th>Status</th>
                      <th>Total</th>
                      <th>Paid</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary?.recent_invoices?.map((invoice) => (
                      <tr key={invoice.id}>
                        <td>{invoice.invoice_number}</td>
                        <td>{invoice.status}</td>
                        <td>₹{Number(invoice.total_amount || 0).toFixed(2)}</td>
                        <td>₹{Number(invoice.paid_amount || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
