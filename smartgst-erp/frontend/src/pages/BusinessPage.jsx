import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { dashboardService } from '../services/dashboardService';

const getRequestErrorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((issue) => issue.msg).filter(Boolean).join(', ') || fallback;
  }
  return typeof detail === 'string' ? detail : fallback;
};

const BusinessPage = () => {
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [lastCreatedInvoice, setLastCreatedInvoice] = useState(null);
  const [sendingInvoice, setSendingInvoice] = useState(false);
  const [loading, setLoading] = useState(true);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [form, setForm] = useState({ name: '', phone: '', email: '' });
  const [productForm, setProductForm] = useState({ name: '', sku: '', purchase_price: '', selling_price: '', quantity: '0' });
  const [vendorForm, setVendorForm] = useState({ name: '', phone: '', email: '' });
  const [purchaseForm, setPurchaseForm] = useState({ purchase_number: '', vendor_id: '', product_id: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', purchase_date: new Date().toISOString().split('T')[0] });
  const [invoiceForm, setInvoiceForm] = useState({ invoice_number: '', shop_name: '', company_gstin: '', company_address: '', company_state: '', company_state_code: '', company_phone: '', company_email: '', customer_id: '', recipient_email: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', cgst_rate: '0', sgst_rate: '0', igst_rate: '0', discount_percentage: '0', invoice_date: new Date().toISOString().split('T')[0], paid_amount: '0', remaining_amount: '0', sku: '', payment_proof: null });

  const loadData = async () => {
    try {
      setLoading(true);
      const [customerData, productData, invoiceData, vendorData, purchaseData, companyProfile] = await Promise.all([
        dashboardService.getCustomers(),
        dashboardService.getProducts(),
        dashboardService.getInvoices(),
        dashboardService.getVendors(),
        dashboardService.getPurchases(),
        dashboardService.getCompanyProfile().catch(() => ({})),
      ]);
      setCustomers(customerData);
      setProducts(productData);
      setInvoices(invoiceData);
      setVendors(vendorData);
      setPurchases(purchaseData);
      setInvoiceForm((current) => ({ ...current, ...companyProfile, invoice_number: companyProfile.next_invoice_number || current.invoice_number, shop_name: companyProfile.shop_name || current.shop_name }));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Unable to load business data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const updateInvoiceAmount = (field, value) => {
    const nextForm = { ...invoiceForm, [field]: value };
    const quantity = Number(nextForm.quantity || 0);
    const unitPrice = Number(nextForm.unit_price || 0);
    const gstRate = Number(nextForm.gst_rate || 0);
    const cgstRate = Number(nextForm.cgst_rate || 0);
    const sgstRate = Number(nextForm.sgst_rate || 0);
    const igstRate = Number(nextForm.igst_rate || 0);
    const discountPercentage = Number(nextForm.discount_percentage || 0);
    const paidAmount = Number(nextForm.paid_amount || 0);
    const grossSubtotal = quantity * unitPrice;
    const discountAmount = grossSubtotal * Math.min(Math.max(discountPercentage, 0), 100) / 100;
    const subtotal = Math.max(grossSubtotal - discountAmount, 0);
    const totalTaxRate = cgstRate + sgstRate + igstRate || gstRate;
    const totalAmount = subtotal * (1 + totalTaxRate / 100);

    setInvoiceForm({
      ...nextForm,
      remaining_amount: Math.max(totalAmount - paidAmount, 0).toFixed(2),
    });
  };

  const handleClearHistory = async () => {
    const confirmation = window.prompt('This permanently deletes your business records. Type CLEAR to continue.');
    if (confirmation !== 'CLEAR') {
      if (confirmation !== null) toast.error('History was not cleared. Type CLEAR exactly.');
      return;
    }

    try {
      setClearingHistory(true);
      await dashboardService.clearBusinessHistory(confirmation);
      setCustomers([]);
      setProducts([]);
      setInvoices([]);
      setVendors([]);
      setPurchases([]);
      toast.success('Business history cleared. Your account is still active.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not clear business history');
    } finally {
      setClearingHistory(false);
    }
  };

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
      toast.error(getRequestErrorMessage(error, 'Could not add product'));
    }
  };

  const handleVendorSubmit = async (e) => {
    e.preventDefault();
    try {
      await dashboardService.createVendor({ ...vendorForm, phone: vendorForm.phone || '0000000000' });
      toast.success('Vendor added');
      setVendorForm({ name: '', phone: '', email: '' });
      loadData();
    } catch (error) {
      toast.error('Could not add vendor');
    }
  };

  const handlePurchaseSubmit = async (e) => {
    e.preventDefault();
    try {
      await dashboardService.createPurchase({
        purchase_number: purchaseForm.purchase_number,
        purchase_date: purchaseForm.purchase_date,
        vendor_id: purchaseForm.vendor_id ? Number(purchaseForm.vendor_id) : null,
        items: [{ product_id: purchaseForm.product_id ? Number(purchaseForm.product_id) : null, description: purchaseForm.description, quantity: Number(purchaseForm.quantity), unit_price: Number(purchaseForm.unit_price), gst_rate: Number(purchaseForm.gst_rate) }],
      });
      toast.success('Purchase received and stock updated');
      setPurchaseForm({ purchase_number: '', vendor_id: '', product_id: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', purchase_date: new Date().toISOString().split('T')[0] });
      loadData();
    } catch (error) {
      toast.error(getRequestErrorMessage(error, 'Could not receive purchase'));
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

      const hasExplicitTaxRates = [invoiceForm.cgst_rate, invoiceForm.sgst_rate, invoiceForm.igst_rate]
        .some((rate) => Number(rate || 0) > 0);
      const payload = {
        invoice_number: invoiceForm.invoice_number || null,
        shop_name: invoiceForm.shop_name || null,
        company_gstin: invoiceForm.company_gstin || null,
        company_address: invoiceForm.company_address || null,
        company_state: invoiceForm.company_state || null,
        company_state_code: invoiceForm.company_state_code || null,
        company_phone: invoiceForm.company_phone || null,
        company_email: invoiceForm.company_email || null,
        invoice_date: invoiceForm.invoice_date,
        customer_id: invoiceForm.customer_id ? Number(invoiceForm.customer_id) : null,
        branch_id: null,
        notes: 'Created from business page',
        paid_amount: Number(invoiceForm.paid_amount || 0),
        discount_percentage: Number(invoiceForm.discount_percentage || 0),
        remaining_amount: Number(invoiceForm.remaining_amount || 0),
        sku: invoiceForm.sku,
        payment_proof_data: paymentProofData,
        items: [
          {
            description: invoiceForm.description,
            quantity: Number(invoiceForm.quantity || 1),
            unit_price: Number(invoiceForm.unit_price || 0),
            gst_rate: Number(invoiceForm.gst_rate || 0),
            cgst_rate: hasExplicitTaxRates ? Number(invoiceForm.cgst_rate || 0) : null,
            sgst_rate: hasExplicitTaxRates ? Number(invoiceForm.sgst_rate || 0) : null,
            igst_rate: hasExplicitTaxRates ? Number(invoiceForm.igst_rate || 0) : null,
          },
        ],
      };

      const createdInvoice = await dashboardService.createInvoice(payload);
      setLastCreatedInvoice({ ...createdInvoice, payment_proof_expected: Boolean(invoiceForm.payment_proof), recipient_email: invoiceForm.recipient_email || customers.find((customer) => customer.id === Number(invoiceForm.customer_id))?.email || '' });
      toast.success('Created invoice');
      setInvoiceForm((current) => ({ ...current, invoice_number: createdInvoice.invoice_number ? createdInvoice.invoice_number.replace(/(\d+)$/, (match) => String(Number(match) + 1).padStart(match.length, '0')) : '', customer_id: '', recipient_email: '', description: '', quantity: '1', unit_price: '0', gst_rate: '0', cgst_rate: '0', sgst_rate: '0', igst_rate: '0', discount_percentage: '0', invoice_date: new Date().toISOString().split('T')[0], paid_amount: '0', remaining_amount: '0', sku: '', payment_proof: null }));
      loadData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((issue) => issue.msg).filter(Boolean).join(', ')
        : detail;
      toast.error(message || 'Could not create invoice');
    }
  };

  const downloadInvoice = async (format) => {
    if (!lastCreatedInvoice) return;
    try {
      const file = format === 'pdf'
        ? await dashboardService.downloadInvoicePdf(lastCreatedInvoice.id)
        : await dashboardService.downloadInvoiceExcel(lastCreatedInvoice.id);
      const url = URL.createObjectURL(file);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice-${lastCreatedInvoice.invoice_number}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error(`Could not download ${format.toUpperCase()} invoice`);
    }
  };

  const handleSendInvoice = async () => {
    if (!lastCreatedInvoice?.recipient_email) {
      toast.error('Enter the client Gmail address before sending');
      return;
    }
    try {
      setSendingInvoice(true);
      await dashboardService.sendInvoiceEmail(lastCreatedInvoice.id, lastCreatedInvoice.recipient_email, lastCreatedInvoice.payment_proof_expected);
      toast.success('Invoice sent to client email');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not send invoice email');
    } finally {
      setSendingInvoice(false);
    }
  };

  return (
    <div className="workspace-shell">
      <header className="workspace-hero">
        <div className="workspace-hero__shade" />
        <div className="container-main workspace-hero__content">
          <div className="workspace-topline"><span className="workspace-brand"><span className="brand-mark">S</span> SmartGST <small>WORKSPACE</small></span><div className="workspace-topline__actions"><span className="workspace-chip">Operations desk · Live</span><button type="button" className="workspace-button workspace-button--danger" onClick={handleClearHistory} disabled={clearingHistory}>{clearingHistory ? 'Clearing...' : 'Clear business history'}</button></div></div>
          <div className="workspace-intro"><div><span className="eyebrow">Build your business</span><h1>From first sale<br />to full picture.</h1><p>Capture customers, products and invoices in one calm workspace.</p></div><div className="workspace-hero__stats"><div><strong>{customers.length}</strong><span>Customers</span></div><div><strong>{products.length}</strong><span>Products</span></div><div><strong>{invoices.length}</strong><span>Invoices</span></div></div></div>
        </div>
      </header>

      <main className="container-main workspace-content">
        <div className="workspace-section-label"><span className="eyebrow eyebrow--dark">Create records</span><h2>Move the business forward</h2><p>Everything you add here appears instantly in your dashboard.</p></div>

        <div className="workspace-form-grid">
          <div className="workspace-card workspace-card--customer">
            <div className="workspace-card__icon">♧</div><span className="eyebrow eyebrow--dark">Relationship</span><h3>Add customer</h3><p>Keep your client book close and current.</p>
            <form onSubmit={handleCustomerSubmit} className="space-y-3">
              <input className="input-field" placeholder="Customer name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <input className="input-field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              <input className="input-field" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <button className="workspace-button workspace-button--coral">Save customer <span>↗</span></button>
            </form>
          </div>

          <div className="workspace-card workspace-card--product">
            <div className="workspace-card__icon">✦</div><span className="eyebrow eyebrow--dark">Inventory</span><h3>Add product</h3><p>Give every item a place in your catalog.</p>
            <form onSubmit={handleProductSubmit} className="space-y-3">
              <input className="input-field" placeholder="Product name" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} required />
              <input className="input-field" placeholder="SKU" value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} />
              <input className="input-field" type="number" placeholder="Initial quantity" value={productForm.quantity} onChange={(e) => setProductForm({ ...productForm, quantity: e.target.value })} required />
              <input className="input-field" type="number" placeholder="Purchase price" value={productForm.purchase_price} onChange={(e) => setProductForm({ ...productForm, purchase_price: e.target.value })} required />
              <input className="input-field" type="number" placeholder="Selling price" value={productForm.selling_price} onChange={(e) => setProductForm({ ...productForm, selling_price: e.target.value })} required />
              <button className="workspace-button workspace-button--teal">Save product <span>↗</span></button>
            </form>
          </div>
        </div>

        <div className="workspace-form-grid workspace-secondary-forms">
          <div className="workspace-card workspace-card--vendor">
            <div className="workspace-card__icon">◌</div><span className="eyebrow eyebrow--dark">Suppliers</span><h3>Add vendor</h3><p>Keep purchase partners and payment details ready.</p>
            <form onSubmit={handleVendorSubmit} className="space-y-3">
              <input className="input-field" placeholder="Vendor name" value={vendorForm.name} onChange={(e) => setVendorForm({ ...vendorForm, name: e.target.value })} required />
              <input className="input-field" placeholder="Phone" value={vendorForm.phone} onChange={(e) => setVendorForm({ ...vendorForm, phone: e.target.value })} />
              <input className="input-field" placeholder="Email" value={vendorForm.email} onChange={(e) => setVendorForm({ ...vendorForm, email: e.target.value })} />
              <button className="workspace-button workspace-button--blue">Save vendor <span>↗</span></button>
            </form>
          </div>
          <div className="workspace-card workspace-card--purchase">
            <div className="workspace-card__icon">↓</div><span className="eyebrow eyebrow--dark">Stock intake</span><h3>Receive purchase</h3><p>Record incoming stock and update inventory together.</p>
            <form onSubmit={handlePurchaseSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input className="input-field" placeholder="Purchase number" value={purchaseForm.purchase_number} onChange={(e) => setPurchaseForm({ ...purchaseForm, purchase_number: e.target.value })} required />
              <input className="input-field" type="date" value={purchaseForm.purchase_date} onChange={(e) => setPurchaseForm({ ...purchaseForm, purchase_date: e.target.value })} required />
              <select className="input-field" value={purchaseForm.vendor_id} onChange={(e) => setPurchaseForm({ ...purchaseForm, vendor_id: e.target.value })}><option value="">Select vendor</option>{vendors.map((vendor) => <option key={vendor.id} value={vendor.id}>{vendor.name}</option>)}</select>
              <select className="input-field" value={purchaseForm.product_id} onChange={(e) => setPurchaseForm({ ...purchaseForm, product_id: e.target.value })}><option value="">Select product</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}</select>
              <input className="input-field md:col-span-2" placeholder="Item description" value={purchaseForm.description} onChange={(e) => setPurchaseForm({ ...purchaseForm, description: e.target.value })} required />
              <input className="input-field" type="number" min="1" placeholder="Quantity" value={purchaseForm.quantity} onChange={(e) => setPurchaseForm({ ...purchaseForm, quantity: e.target.value })} required />
              <input className="input-field" type="number" min="0" placeholder="Unit price" value={purchaseForm.unit_price} onChange={(e) => setPurchaseForm({ ...purchaseForm, unit_price: e.target.value })} required />
              <input className="input-field" type="number" min="0" max="100" placeholder="GST %" value={purchaseForm.gst_rate} onChange={(e) => setPurchaseForm({ ...purchaseForm, gst_rate: e.target.value })} required />
              <button className="workspace-button workspace-button--green md:col-span-2">Receive purchase <span>↗</span></button>
            </form>
          </div>
        </div>

        <div className="invoice-builder">
          <div className="invoice-builder__art" />
          <div className="invoice-builder__content"><span className="eyebrow">Sales desk</span><h2>Create invoice</h2><p>Turn a completed sale into a clear, trackable record.</p>
          <form onSubmit={handleInvoiceSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input-field" placeholder="First invoice number (e.g. INV-001)" value={invoiceForm.invoice_number} onChange={(e) => setInvoiceForm({ ...invoiceForm, invoice_number: e.target.value })} required={invoices.length === 0} readOnly={invoices.length > 0} />
            <input className="input-field" placeholder="Your shop name (shown on invoice)" value={invoiceForm.shop_name} onChange={(e) => setInvoiceForm({ ...invoiceForm, shop_name: e.target.value })} required />
            <input className="input-field" placeholder="Company GSTIN" value={invoiceForm.company_gstin} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_gstin: e.target.value })} />
            <input className="input-field" placeholder="Company address" value={invoiceForm.company_address} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_address: e.target.value })} />
            <input className="input-field" placeholder="Company state" value={invoiceForm.company_state} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_state: e.target.value })} />
            <input className="input-field" placeholder="State code" value={invoiceForm.company_state_code} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_state_code: e.target.value })} />
            <input className="input-field" type="tel" placeholder="Company phone" value={invoiceForm.company_phone} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_phone: e.target.value })} />
            <input className="input-field" type="email" placeholder="Company Gmail" value={invoiceForm.company_email} onChange={(e) => setInvoiceForm({ ...invoiceForm, company_email: e.target.value })} />
            <input className="input-field" type="date" value={invoiceForm.invoice_date} onChange={(e) => setInvoiceForm({ ...invoiceForm, invoice_date: e.target.value })} required />
            <select className="input-field" value={invoiceForm.customer_id} onChange={(e) => setInvoiceForm({ ...invoiceForm, customer_id: e.target.value })}>
              <option value="">Select customer (optional)</option>
              {customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}
            </select>
            <input className="input-field" placeholder="Description" value={invoiceForm.description} onChange={(e) => setInvoiceForm({ ...invoiceForm, description: e.target.value })} required />
            <input className="input-field" type="email" placeholder="Client Gmail (for sending invoice)" value={invoiceForm.recipient_email} onChange={(e) => setInvoiceForm({ ...invoiceForm, recipient_email: e.target.value })} />
            <input className="input-field" placeholder="SKU" value={invoiceForm.sku} onChange={(e) => setInvoiceForm({ ...invoiceForm, sku: e.target.value })} />
            <input className="input-field" type="number" placeholder="Quantity" value={invoiceForm.quantity} onChange={(e) => updateInvoiceAmount('quantity', e.target.value)} required />
            <input className="input-field" type="number" placeholder="Unit price" value={invoiceForm.unit_price} onChange={(e) => updateInvoiceAmount('unit_price', e.target.value)} required />
            <input className="input-field" type="number" placeholder="GST %" value={invoiceForm.gst_rate} onChange={(e) => updateInvoiceAmount('gst_rate', e.target.value)} required />
            <input className="input-field" type="number" min="0" max="100" placeholder="CGST %" value={invoiceForm.cgst_rate} onChange={(e) => updateInvoiceAmount('cgst_rate', e.target.value)} />
            <input className="input-field" type="number" min="0" max="100" placeholder="SGST %" value={invoiceForm.sgst_rate} onChange={(e) => updateInvoiceAmount('sgst_rate', e.target.value)} />
            <input className="input-field" type="number" min="0" max="100" placeholder="IGST %" value={invoiceForm.igst_rate} onChange={(e) => updateInvoiceAmount('igst_rate', e.target.value)} />
            <input className="input-field" type="number" min="0" max="100" placeholder="Discount %" value={invoiceForm.discount_percentage} onChange={(e) => updateInvoiceAmount('discount_percentage', e.target.value)} />
            <input className="input-field" type="number" min="0" placeholder="Paid amount" value={invoiceForm.paid_amount} onChange={(e) => updateInvoiceAmount('paid_amount', e.target.value)} />
            <input className="input-field" type="number" placeholder="Remaining amount" value={invoiceForm.remaining_amount} readOnly aria-readonly="true" />
            <input className="input-field" type="file" accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx" onChange={(e) => setInvoiceForm({ ...invoiceForm, payment_proof: e.target.files?.[0] || null })} />
            <button className="workspace-button workspace-button--gold md:col-span-2">Create invoice <span>↗</span></button>
          </form>
          {lastCreatedInvoice && (
            <div className="mt-5 rounded-lg border border-white/30 bg-white/10 p-4">
              <p className="font-semibold text-white">Invoice {lastCreatedInvoice.invoice_number} is ready</p>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
                <input className="input-field" type="email" placeholder="Client Gmail" value={lastCreatedInvoice.recipient_email} onChange={(e) => setLastCreatedInvoice({ ...lastCreatedInvoice, recipient_email: e.target.value })} />
                <button type="button" className="workspace-button workspace-button--blue" onClick={handleSendInvoice} disabled={sendingInvoice}>{sendingInvoice ? 'Sending...' : 'Send invoice email'}</button>
                <button type="button" className="workspace-button workspace-button--coral" onClick={() => downloadInvoice('pdf')}>Download PDF</button>
                <button type="button" className="workspace-button workspace-button--teal" onClick={() => downloadInvoice('excel')}>Export Excel</button>
              </div>
            </div>
          )}
          </div>
        </div>

        <div className="workspace-data-card">
          <div className="workspace-data-card__heading"><div><span className="eyebrow eyebrow--dark">Sales pulse</span><h2>Recent invoices</h2></div><span>{invoices.length} total</span></div>
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

        <div className="workspace-lists">
          <div className="workspace-list-card workspace-list-card--peach">
            <div className="workspace-data-card__heading"><div><span className="eyebrow eyebrow--dark">Relationships</span><h2>Customers</h2></div><strong>{customers.length}</strong></div>
            <ul className="workspace-list">
              {customers.map((customer) => (
                <li key={customer.id}><span className="list-avatar">{customer.name?.slice(0, 1)}</span><span><b>{customer.name}</b><small>{customer.phone}</small></span></li>
              ))}
            </ul>
          </div>
          <div className="workspace-list-card workspace-list-card--blue">
            <div className="workspace-data-card__heading"><div><span className="eyebrow eyebrow--dark">Inventory</span><h2>Products</h2></div><strong>{products.length}</strong></div>
            <ul className="workspace-list">
              {products.map((product) => (
                <li key={product.id}><span className="list-avatar">✦</span><span><b>{product.name}</b><small>₹{Number(product.selling_price || 0).toFixed(2)} · Qty {Number(product.quantity || 0)}</small></span></li>
              ))}
            </ul>
          </div>
        </div>

        <div className="workspace-data-card workspace-purchases-card">
          <div className="workspace-data-card__heading"><div><span className="eyebrow eyebrow--dark">Stock intake history</span><h2>Recent purchases</h2></div><span>{purchases.length} total</span></div>
          <div className="overflow-x-auto"><table className="table w-full"><thead><tr><th>Purchase</th><th>Status</th><th>Total</th><th>Date</th></tr></thead><tbody>{purchases.map((purchase) => <tr key={purchase.id}><td>{purchase.purchase_number}</td><td>{purchase.status}</td><td>₹{Number(purchase.total_amount || 0).toFixed(2)}</td><td>{purchase.purchase_date}</td></tr>)}</tbody></table></div>
        </div>
      </main>
    </div>
  );
};

export default BusinessPage;
