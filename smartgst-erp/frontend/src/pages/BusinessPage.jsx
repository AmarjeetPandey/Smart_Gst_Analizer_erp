import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { dashboardService } from '../services/dashboardService';

const BusinessPage = () => {
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', phone: '', email: '' });
  const [productForm, setProductForm] = useState({ name: '', sku: '', purchase_price: '', selling_price: '', quantity: '0' });
  const [invoiceForm, setInvoiceForm] = useState({ invoice_number: '', customer_id: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', invoice_date: new Date().toISOString().split('T')[0], paid_amount: '0', remaining_amount: '0', sku: '', payment_proof: null });

  const loadData = async () => {
    try {
      setLoading(true);
      const [customerData, productData, invoiceData] = await Promise.all([
        dashboardService.getCustomers(),
        dashboardService.getProducts(),
        dashboardService.getInvoices(),
      ]);
      setCustomers(customerData);
      setProducts(productData);
      setInvoices(invoiceData);
    } catch (error) {
      toast.error('Unable to load business data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCustomerSubmit = async (e) => {
    e.preventDefault();
    try {
      await dashboardService.createCustomer({ ...form, phone: form.phone || '0000000000' });
      toast.success('Customer added');
      setForm({ name: '', phone: '', email: '' });
      loadData();
    } catch (error) {
      toast.error('Could not add customer');
    }
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    try {
      await dashboardService.createProduct({
        ...productForm,
        purchase_price: Number(productForm.purchase_price || 0),
        selling_price: Number(productForm.selling_price || 0),
        quantity: Number(productForm.quantity || 0),
        unit: 'pieces',
        gst_rate: 0,
      });
      toast.success('Product added');
      setProductForm({ name: '', sku: '', purchase_price: '', selling_price: '', quantity: '0' });
      loadData();
    } catch (error) {
      toast.error('Could not add product');
    }
  };

  const handleInvoiceSubmit = async (e) => {
    e.preventDefault();
    try {
      let paymentProofData = null;
      if (invoiceForm.payment_proof) {
        const fileToBase64 = (file) => new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.readAsDataURL(file);
          reader.onload = () => resolve(reader.result);
          reader.onerror = (error) => reject(error);
        });
        paymentProofData = await fileToBase64(invoiceForm.payment_proof);
      }

      const payload = {
        invoice_number: invoiceForm.invoice_number,
        invoice_date: invoiceForm.invoice_date,
        customer_id: invoiceForm.customer_id ? Number(invoiceForm.customer_id) : null,
        branch_id: null,
        notes: 'Created from business page',
        paid_amount: Number(invoiceForm.paid_amount || 0),
        remaining_amount: Number(invoiceForm.remaining_amount || 0),
        sku: invoiceForm.sku,
        payment_proof_data: paymentProofData,
        items: [
          {
            description: invoiceForm.description,
            quantity: Number(invoiceForm.quantity || 1),
            unit_price: Number(invoiceForm.unit_price || 0),
            gst_rate: Number(invoiceForm.gst_rate || 0),
          },
        ],
      };

      await dashboardService.createInvoice(payload);
      toast.success('Created invoice');
      setInvoiceForm({ invoice_number: '', customer_id: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', invoice_date: new Date().toISOString().split('T')[0], paid_amount: '0', remaining_amount: '0', sku: '', payment_proof: null });
      loadData();
    } catch (error) {
      toast.error('Could not create invoice');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="card">
          <h1 className="text-2xl font-bold">Business Operations</h1>
          <p className="text-gray-600">Manage real customers, products, and invoices for your account.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Add Customer</h2>
            <form onSubmit={handleCustomerSubmit} className="space-y-3">
              <input className="input-field" placeholder="Customer name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <input className="input-field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              <input className="input-field" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <button className="btn-primary">Save Customer</button>
            </form>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Add Product</h2>
            <form onSubmit={handleProductSubmit} className="space-y-3">
              <input className="input-field" placeholder="Product name" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} required />
              <input className="input-field" placeholder="SKU" value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} />
              <input className="input-field" type="number" placeholder="Initial quantity" value={productForm.quantity} onChange={(e) => setProductForm({ ...productForm, quantity: e.target.value })} required />
              <input className="input-field" type="number" placeholder="Purchase price" value={productForm.purchase_price} onChange={(e) => setProductForm({ ...productForm, purchase_price: e.target.value })} required />
              <input className="input-field" type="number" placeholder="Selling price" value={productForm.selling_price} onChange={(e) => setProductForm({ ...productForm, selling_price: e.target.value })} required />
              <button className="btn-primary">Save Product</button>
            </form>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Create Invoice</h2>
          <form onSubmit={handleInvoiceSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input-field" placeholder="Invoice number" value={invoiceForm.invoice_number} onChange={(e) => setInvoiceForm({ ...invoiceForm, invoice_number: e.target.value })} required />
            <input className="input-field" type="date" value={invoiceForm.invoice_date} onChange={(e) => setInvoiceForm({ ...invoiceForm, invoice_date: e.target.value })} required />
            <select className="input-field" value={invoiceForm.customer_id} onChange={(e) => setInvoiceForm({ ...invoiceForm, customer_id: e.target.value })}>
              <option value="">Select customer (optional)</option>
              {customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}
            </select>
            <input className="input-field" placeholder="Description" value={invoiceForm.description} onChange={(e) => setInvoiceForm({ ...invoiceForm, description: e.target.value })} required />
            <input className="input-field" placeholder="SKU" value={invoiceForm.sku} onChange={(e) => setInvoiceForm({ ...invoiceForm, sku: e.target.value })} />
            <input className="input-field" type="number" placeholder="Quantity" value={invoiceForm.quantity} onChange={(e) => setInvoiceForm({ ...invoiceForm, quantity: e.target.value })} required />
            <input className="input-field" type="number" placeholder="Unit price" value={invoiceForm.unit_price} onChange={(e) => setInvoiceForm({ ...invoiceForm, unit_price: e.target.value })} required />
            <input className="input-field" type="number" placeholder="GST %" value={invoiceForm.gst_rate} onChange={(e) => setInvoiceForm({ ...invoiceForm, gst_rate: e.target.value })} required />
            <input className="input-field" type="number" placeholder="Paid amount" value={invoiceForm.paid_amount} onChange={(e) => setInvoiceForm({ ...invoiceForm, paid_amount: e.target.value })} />
            <input className="input-field" type="number" placeholder="Remaining amount" value={invoiceForm.remaining_amount} onChange={(e) => setInvoiceForm({ ...invoiceForm, remaining_amount: e.target.value })} />
            <input className="input-field" type="file" accept="image/*" onChange={(e) => setInvoiceForm({ ...invoiceForm, payment_proof: e.target.files?.[0] || null })} />
            <button className="btn-primary md:col-span-2">Create Invoice</button>
          </form>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recent Invoices</h2>
          {loading ? <p>Loading...</p> : (
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
                  {invoices.map((invoice) => (
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
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Customers</h2>
            <ul className="space-y-2">
              {customers.map((customer) => (
                <li key={customer.id} className="border-b pb-2">{customer.name} — {customer.phone}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Products</h2>
            <ul className="space-y-2">
              {products.map((product) => (
                <li key={product.id} className="border-b pb-2">{product.name} — ₹{Number(product.selling_price || 0).toFixed(2)} • Qty {Number(product.quantity || 0)}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessPage;
