"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import {
  getStats,
  getCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  getLoanProducts,
  createLoanProduct,
  updateLoanProduct,
  deleteLoanProduct,
  getPrequalRules,
  createPrequalRule,
  updatePrequalRule,
  deletePrequalRule,
  getPrequalResults,
  getConfig,
  updateConfig,
  resetData,
} from "@/lib/adminApi";

type Tab = "overview" | "customers" | "products" | "rules" | "results" | "config";

const ADMIN_PASSWORD = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "";

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [customers, setCustomers] = useState<Record<string, unknown>[]>([]);
  const [products, setProducts] = useState<Record<string, unknown>[]>([]);
  const [rules, setRules] = useState<Record<string, unknown>[]>([]);
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [config, setConfig] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      setAuthenticated(true);
      setPasswordError(false);
    } else {
      setPasswordError(true);
    }
  }

  useEffect(() => {
    if (authenticated) loadData();
  }, [authenticated]);

  async function loadData() {
    setLoading(true);
    try {
      const [s, c, p, r, res, cfg] = await Promise.all([
        getStats(),
        getCustomers(),
        getLoanProducts(),
        getPrequalRules(),
        getPrequalResults(),
        getConfig(),
      ]);
      setStats(s);
      setCustomers(c.customers || []);
      setProducts(p.products || []);
      setRules(r.rules || []);
      setResults(res.results || []);
      setConfig(cfg.config || []);
    } catch (err) {
      setMessage({ type: "error", text: "Failed to load data. Is the backend running?" });
    }
    setLoading(false);
  }

  function showMessage(type: "success" | "error", text: string) {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  }

  async function handleResetData() {
    if (!confirm("Reset all data to defaults? This will overwrite current data.")) return;
    setSaving(true);
    try {
      await resetData();
      await loadData();
      showMessage("success", "Data reset successfully");
    } catch {
      showMessage("error", "Failed to reset data");
    }
    setSaving(false);
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "customers", label: "Customers" },
    { key: "products", label: "Loan Products" },
    { key: "rules", label: "Pre-Qual Rules" },
    { key: "results", label: "Results Log" },
    { key: "config", label: "Config" },
  ];

  if (!authenticated) {
    return (
      <div className="h-screen flex flex-col bg-gray-100">
        <Header showAdmin={false} />
        <div className="flex-1 flex items-center justify-center">
          <form onSubmit={handleLogin} className="bg-white rounded-xl shadow-sm border p-8 w-full max-w-sm">
            <h2 className="text-xl font-bold text-gray-800 mb-6 text-center">Admin Access</h2>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setPasswordError(false); }}
              className={`w-full border rounded-lg px-3 py-2 text-sm mb-1 focus:outline-none focus:ring-2 focus:ring-citi-blue ${
                passwordError ? "border-red-400" : "border-gray-300"
              }`}
              placeholder="Enter admin password"
              autoFocus
            />
            {passwordError && (
              <p className="text-xs text-red-600 mb-3">Incorrect password</p>
            )}
            <button
              type="submit"
              className="w-full mt-4 px-4 py-2 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light transition-colors"
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <Header showAdmin={false} />
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Title + actions */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Admin Panel</h2>
            <div className="flex gap-2">
              <button
                onClick={handleResetData}
                disabled={saving}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {saving ? "Resetting..." : "Reset to Defaults"}
              </button>
              <button
                onClick={loadData}
                disabled={loading}
                className="px-4 py-2 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light disabled:opacity-50"
              >
                {loading ? "Loading..." : "Refresh"}
              </button>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div
              className={`mb-4 p-3 rounded-lg text-sm ${
                message.type === "success"
                  ? "bg-green-100 text-green-800 border border-green-200"
                  : "bg-red-100 text-red-800 border border-red-200"
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="flex gap-0">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? "border-citi-blue text-citi-blue"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading...</div>
          ) : (
            <>
              {activeTab === "overview" && <OverviewTab stats={stats} />}
              {activeTab === "customers" && (
                <CustomersTab
                  customers={customers}
                  onCreate={async (data) => {
                    await createCustomer(data);
                    await loadData();
                    showMessage("success", "Customer created");
                  }}
                  onUpdate={async (id, data) => {
                    await updateCustomer(id, data);
                    await loadData();
                    showMessage("success", "Customer updated");
                  }}
                  onDelete={async (id) => {
                    await deleteCustomer(id);
                    await loadData();
                    showMessage("success", "Customer deleted");
                  }}
                />
              )}
              {activeTab === "products" && (
                <ProductsTab
                  products={products}
                  onCreate={async (data) => {
                    await createLoanProduct(data);
                    await loadData();
                    showMessage("success", "Product created");
                  }}
                  onUpdate={async (id, data) => {
                    await updateLoanProduct(id, data);
                    await loadData();
                    showMessage("success", "Product updated");
                  }}
                  onDelete={async (id) => {
                    await deleteLoanProduct(id);
                    await loadData();
                    showMessage("success", "Product deleted");
                  }}
                />
              )}
              {activeTab === "rules" && (
                <RulesTab
                  rules={rules}
                  products={products}
                  onCreate={async (data) => {
                    await createPrequalRule(data);
                    await loadData();
                    showMessage("success", "Rule created");
                  }}
                  onUpdate={async (id, data) => {
                    await updatePrequalRule(id, data);
                    await loadData();
                    showMessage("success", "Rule updated");
                  }}
                  onDelete={async (id) => {
                    await deletePrequalRule(id);
                    await loadData();
                    showMessage("success", "Rule deleted");
                  }}
                />
              )}
              {activeTab === "results" && <ResultsTab results={results} />}
              {activeTab === "config" && (
                <ConfigTab
                  config={config}
                  onUpdate={async (key, value) => {
                    await updateConfig(key, value);
                    await loadData();
                    showMessage("success", "Config updated");
                  }}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ====== Overview Tab ======
function OverviewTab({ stats }: { stats: Record<string, number> | null }) {
  if (!stats) return null;
  const cards = [
    { label: "Total Customers", value: stats.total_customers, color: "bg-blue-500" },
    { label: "Active Products", value: stats.active_products, color: "bg-green-500" },
    { label: "Pre-Qualifications", value: stats.total_prequalifications, color: "bg-purple-500" },
    { label: "Approval Rate", value: `${stats.approval_rate}%`, color: "bg-amber-500" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="bg-white rounded-xl shadow-sm border p-6">
          <div className={`w-10 h-10 ${card.color} rounded-lg flex items-center justify-center mb-3`}>
            <span className="text-white text-lg font-bold">#</span>
          </div>
          <p className="text-sm text-gray-500">{card.label}</p>
          <p className="text-2xl font-bold text-gray-800">{card.value}</p>
        </div>
      ))}
    </div>
  );
}

// ====== Customers Tab ======
const emptyCustomer: Record<string, unknown> = {
  customer_id: "", first_name: "", last_name: "", date_of_birth: "", postcode: "",
  email: "", phone: "", account_type: "current", risk_score: 5,
  annual_income: 0, employment_status: "full_time", residency_status: "uk_resident",
  eligibility_flags: { pre_approved: false, existing_loan_holder: false, premium_customer: false },
};

function CustomersTab({
  customers,
  onCreate,
  onUpdate,
  onDelete,
}: {
  customers: Record<string, unknown>[];
  onCreate: (data: Record<string, unknown>) => Promise<void>;
  onUpdate: (id: number, data: Record<string, unknown>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Record<string, unknown>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [createData, setCreateData] = useState<Record<string, unknown>>({ ...emptyCustomer });

  function startEdit(customer: Record<string, unknown>) {
    setEditingId(customer.id as number);
    setEditData({
      first_name: customer.first_name,
      last_name: customer.last_name,
      postcode: customer.postcode,
      email: customer.email,
      phone: customer.phone,
      risk_score: customer.risk_score,
      annual_income: customer.annual_income,
      employment_status: customer.employment_status,
      residency_status: customer.residency_status,
      eligibility_flags: customer.eligibility_flags,
    });
  }

  async function saveEdit() {
    if (editingId === null) return;
    await onUpdate(editingId, editData);
    setEditingId(null);
  }

  async function handleCreate() {
    await onCreate(createData);
    setCreateData({ ...emptyCustomer });
    setShowCreate(false);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this customer?")) return;
    await onDelete(id);
  }

  const editFlags = (editData.eligibility_flags || {}) as Record<string, boolean>;

  return (
    <div>
      <div className="flex justify-end mb-3">
        <button onClick={() => setShowCreate(!showCreate)} className="px-3 py-1.5 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light">
          {showCreate ? "Cancel" : "+ Add Customer"}
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-4">
          <h3 className="font-semibold mb-4">New Customer</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <label className="block text-gray-500 mb-1">Customer ID</label>
              <input type="text" value={createData.customer_id as string} onChange={(e) => setCreateData({ ...createData, customer_id: e.target.value })} className="w-full border rounded px-2 py-1" placeholder="CITI-UK-XXXXX" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">First Name</label>
              <input type="text" value={createData.first_name as string} onChange={(e) => setCreateData({ ...createData, first_name: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Last Name</label>
              <input type="text" value={createData.last_name as string} onChange={(e) => setCreateData({ ...createData, last_name: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Date of Birth</label>
              <input type="text" value={createData.date_of_birth as string} onChange={(e) => setCreateData({ ...createData, date_of_birth: e.target.value })} className="w-full border rounded px-2 py-1" placeholder="DD/MM/YYYY" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Postcode</label>
              <input type="text" value={createData.postcode as string} onChange={(e) => setCreateData({ ...createData, postcode: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Email</label>
              <input type="email" value={createData.email as string} onChange={(e) => setCreateData({ ...createData, email: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Phone</label>
              <input type="text" value={createData.phone as string} onChange={(e) => setCreateData({ ...createData, phone: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Account Type</label>
              <select value={createData.account_type as string} onChange={(e) => setCreateData({ ...createData, account_type: e.target.value })} className="w-full border rounded px-2 py-1">
                <option value="current">Current</option>
                <option value="savings">Savings</option>
                <option value="premium">Premium</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Risk Score (1-10)</label>
              <input type="number" min="1" max="10" value={createData.risk_score as number} onChange={(e) => setCreateData({ ...createData, risk_score: parseInt(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Annual Income</label>
              <input type="number" value={createData.annual_income as number} onChange={(e) => setCreateData({ ...createData, annual_income: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Employment</label>
              <select value={createData.employment_status as string} onChange={(e) => setCreateData({ ...createData, employment_status: e.target.value })} className="w-full border rounded px-2 py-1">
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="self_employed">Self Employed</option>
                <option value="retired">Retired</option>
                <option value="unemployed">Unemployed</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Residency</label>
              <select value={createData.residency_status as string} onChange={(e) => setCreateData({ ...createData, residency_status: e.target.value })} className="w-full border rounded px-2 py-1">
                <option value="uk_resident">UK Resident</option>
                <option value="non_resident">Non Resident</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex gap-4 text-sm">
            {["pre_approved", "existing_loan_holder", "premium_customer"].map((flag) => (
              <label key={flag} className="flex items-center gap-1">
                <input type="checkbox" checked={!!(createData.eligibility_flags as Record<string, boolean>)?.[flag]} onChange={(e) => setCreateData({ ...createData, eligibility_flags: { ...(createData.eligibility_flags as Record<string, boolean>), [flag]: e.target.checked } })} />
                {flag.replace(/_/g, " ")}
              </label>
            ))}
          </div>
          <div className="mt-4">
            <button onClick={handleCreate} className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">Create Customer</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Customer</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Postcode</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">DOB</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Account</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Risk</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Income</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Employment</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Flags</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {customers.map((c) => {
                const isEditing = editingId === (c.id as number);
                const flags = c.eligibility_flags as Record<string, boolean> | undefined;
                return (
                  <tr key={c.id as number} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <div className="flex flex-col gap-1">
                          <input type="text" value={editData.first_name as string} onChange={(e) => setEditData({ ...editData, first_name: e.target.value })} className="w-28 border rounded px-2 py-1 text-sm" placeholder="First" />
                          <input type="text" value={editData.last_name as string} onChange={(e) => setEditData({ ...editData, last_name: e.target.value })} className="w-28 border rounded px-2 py-1 text-sm" placeholder="Last" />
                        </div>
                      ) : (
                        <div>
                          <p className="font-medium">{c.first_name as string} {c.last_name as string}</p>
                          <p className="text-xs text-gray-400">{c.customer_id as string}</p>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <input type="text" value={editData.postcode as string} onChange={(e) => setEditData({ ...editData, postcode: e.target.value })} className="w-24 border rounded px-2 py-1 text-sm" />
                      ) : (
                        c.postcode as string
                      )}
                    </td>
                    <td className="px-4 py-3">{c.date_of_birth as string}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                        {c.account_type as string}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <input type="number" min="1" max="10" value={editData.risk_score as number} onChange={(e) => setEditData({ ...editData, risk_score: parseInt(e.target.value) })} className="w-16 border rounded px-2 py-1 text-sm" />
                      ) : (
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${(c.risk_score as number) <= 3 ? "bg-green-100 text-green-700" : (c.risk_score as number) <= 6 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>
                          {c.risk_score as number}/10
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <input type="number" value={editData.annual_income as number} onChange={(e) => setEditData({ ...editData, annual_income: parseFloat(e.target.value) })} className="w-24 border rounded px-2 py-1 text-sm" />
                      ) : (
                        `£${((c.annual_income as number) || 0).toLocaleString()}`
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <select value={editData.employment_status as string} onChange={(e) => setEditData({ ...editData, employment_status: e.target.value })} className="border rounded px-2 py-1 text-sm">
                          <option value="full_time">Full Time</option>
                          <option value="part_time">Part Time</option>
                          <option value="self_employed">Self Employed</option>
                          <option value="retired">Retired</option>
                          <option value="unemployed">Unemployed</option>
                        </select>
                      ) : (
                        c.employment_status as string
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <div className="flex flex-col gap-1 text-xs">
                          {["pre_approved", "existing_loan_holder", "premium_customer"].map((flag) => (
                            <label key={flag} className="flex items-center gap-1">
                              <input type="checkbox" checked={!!editFlags[flag]} onChange={(e) => setEditData({ ...editData, eligibility_flags: { ...editFlags, [flag]: e.target.checked } })} />
                              {flag.replace(/_/g, " ")}
                            </label>
                          ))}
                        </div>
                      ) : (
                        <div className="flex gap-1 flex-wrap">
                          {flags?.pre_approved && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">pre-approved</span>}
                          {flags?.existing_loan_holder && <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">has loan</span>}
                          {flags?.premium_customer && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">premium</span>}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isEditing ? (
                        <div className="flex gap-1">
                          <button onClick={saveEdit} className="text-xs bg-green-600 text-white px-2 py-1 rounded">Save</button>
                          <button onClick={() => setEditingId(null)} className="text-xs bg-gray-300 text-gray-700 px-2 py-1 rounded">Cancel</button>
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <button onClick={() => startEdit(c)} className="text-xs text-citi-blue hover:underline">Edit</button>
                          <button onClick={() => handleDelete(c.id as number)} className="text-xs text-red-600 hover:underline">Delete</button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ====== Products Tab ======
const emptyProduct: Record<string, unknown> = {
  product_code: "", product_name: "", description: "",
  min_amount: 1000, max_amount: 50000, min_term_months: 12, max_term_months: 60,
  representative_apr: 5.0, min_apr: 3.0, max_apr: 25.0,
  features: [], is_active: true,
};

function ProductsTab({
  products,
  onCreate,
  onUpdate,
  onDelete,
}: {
  products: Record<string, unknown>[];
  onCreate: (data: Record<string, unknown>) => Promise<void>;
  onUpdate: (id: number, data: Record<string, unknown>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Record<string, unknown>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [createData, setCreateData] = useState<Record<string, unknown>>({ ...emptyProduct });
  const [featuresInput, setFeaturesInput] = useState("");

  function startEdit(p: Record<string, unknown>) {
    setEditingId(p.id as number);
    setEditData({
      product_name: p.product_name,
      description: p.description,
      representative_apr: p.representative_apr,
      min_apr: p.min_apr,
      max_apr: p.max_apr,
      min_amount: p.min_amount,
      max_amount: p.max_amount,
      min_term_months: p.min_term_months,
      max_term_months: p.max_term_months,
      features: p.features,
      is_active: p.is_active,
    });
    setFeaturesInput(((p.features as string[]) || []).join(", "));
  }

  async function saveEdit() {
    if (editingId === null) return;
    await onUpdate(editingId, { ...editData, features: featuresInput.split(",").map((s) => s.trim()).filter(Boolean) });
    setEditingId(null);
  }

  async function handleCreate() {
    await onCreate(createData);
    setCreateData({ ...emptyProduct });
    setShowCreate(false);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this loan product?")) return;
    await onDelete(id);
  }

  return (
    <div>
      <div className="flex justify-end mb-3">
        <button onClick={() => setShowCreate(!showCreate)} className="px-3 py-1.5 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light">
          {showCreate ? "Cancel" : "+ Add Product"}
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-4">
          <h3 className="font-semibold mb-4">New Loan Product</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <label className="block text-gray-500 mb-1">Product Code</label>
              <input type="text" value={createData.product_code as string} onChange={(e) => setCreateData({ ...createData, product_code: e.target.value })} className="w-full border rounded px-2 py-1" placeholder="e.g. AUTO_LOAN" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Product Name</label>
              <input type="text" value={createData.product_name as string} onChange={(e) => setCreateData({ ...createData, product_name: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div className="col-span-2">
              <label className="block text-gray-500 mb-1">Description</label>
              <input type="text" value={createData.description as string} onChange={(e) => setCreateData({ ...createData, description: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Rep. APR %</label>
              <input type="number" step="0.1" value={createData.representative_apr as number} onChange={(e) => setCreateData({ ...createData, representative_apr: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Min APR %</label>
              <input type="number" step="0.1" value={createData.min_apr as number} onChange={(e) => setCreateData({ ...createData, min_apr: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Max APR %</label>
              <input type="number" step="0.1" value={createData.max_apr as number} onChange={(e) => setCreateData({ ...createData, max_apr: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Min Amount</label>
              <input type="number" value={createData.min_amount as number} onChange={(e) => setCreateData({ ...createData, min_amount: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Max Amount</label>
              <input type="number" value={createData.max_amount as number} onChange={(e) => setCreateData({ ...createData, max_amount: parseFloat(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Min Term (months)</label>
              <input type="number" value={createData.min_term_months as number} onChange={(e) => setCreateData({ ...createData, min_term_months: parseInt(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Max Term (months)</label>
              <input type="number" value={createData.max_term_months as number} onChange={(e) => setCreateData({ ...createData, max_term_months: parseInt(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div className="col-span-2">
              <label className="block text-gray-500 mb-1">Features (comma-separated)</label>
              <input type="text" value={(createData.features as string[])?.join(", ") || ""} onChange={(e) => setCreateData({ ...createData, features: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} className="w-full border rounded px-2 py-1" placeholder="e.g. No early repayment fee, Flexible terms" />
            </div>
            <div>
              <label className="flex items-center gap-2 mt-5">
                <input type="checkbox" checked={createData.is_active as boolean} onChange={(e) => setCreateData({ ...createData, is_active: e.target.checked })} />
                Active
              </label>
            </div>
          </div>
          <div className="mt-4">
            <button onClick={handleCreate} className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">Create Product</button>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {products.map((p) => {
          const isEditing = editingId === (p.id as number);
          const features = (p.features as string[]) || [];
          return (
            <div key={p.id as number} className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  {isEditing ? (
                    <div className="grid grid-cols-2 gap-2 mb-2">
                      <div>
                        <label className="block text-xs text-gray-500">Product Name</label>
                        <input type="text" value={editData.product_name as string} onChange={(e) => setEditData({ ...editData, product_name: e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500">Description</label>
                        <input type="text" value={editData.description as string} onChange={(e) => setEditData({ ...editData, description: e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold">{p.product_name as string}</h3>
                        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-mono">{p.product_code as string}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${p.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                          {p.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{p.description as string}</p>
                    </>
                  )}
                </div>
                {isEditing ? (
                  <div className="flex gap-1 ml-4">
                    <button onClick={saveEdit} className="text-xs bg-green-600 text-white px-3 py-1.5 rounded">Save</button>
                    <button onClick={() => setEditingId(null)} className="text-xs bg-gray-300 text-gray-700 px-3 py-1.5 rounded">Cancel</button>
                  </div>
                ) : (
                  <div className="flex gap-2 ml-4">
                    <button onClick={() => startEdit(p)} className="text-xs text-citi-blue hover:underline">Edit</button>
                    <button onClick={() => handleDelete(p.id as number)} className="text-xs text-red-600 hover:underline">Delete</button>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Representative APR</p>
                  {isEditing ? (
                    <input type="number" step="0.1" value={editData.representative_apr as number} onChange={(e) => setEditData({ ...editData, representative_apr: parseFloat(e.target.value) })} className="w-24 border rounded px-2 py-1 mt-1" />
                  ) : (
                    <p className="font-semibold text-lg">{p.representative_apr as number}%</p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">APR Range</p>
                  {isEditing ? (
                    <div className="flex gap-1 mt-1">
                      <input type="number" step="0.1" value={editData.min_apr as number} onChange={(e) => setEditData({ ...editData, min_apr: parseFloat(e.target.value) })} className="w-16 border rounded px-2 py-1" />
                      <span>-</span>
                      <input type="number" step="0.1" value={editData.max_apr as number} onChange={(e) => setEditData({ ...editData, max_apr: parseFloat(e.target.value) })} className="w-16 border rounded px-2 py-1" />
                    </div>
                  ) : (
                    <p className="font-medium">{p.min_apr as number}% - {p.max_apr as number}%</p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">Borrowing Range</p>
                  {isEditing ? (
                    <div className="flex gap-1 mt-1">
                      <input type="number" value={editData.min_amount as number} onChange={(e) => setEditData({ ...editData, min_amount: parseFloat(e.target.value) })} className="w-24 border rounded px-2 py-1" />
                      <span>-</span>
                      <input type="number" value={editData.max_amount as number} onChange={(e) => setEditData({ ...editData, max_amount: parseFloat(e.target.value) })} className="w-24 border rounded px-2 py-1" />
                    </div>
                  ) : (
                    <p className="font-medium">£{((p.min_amount as number) || 0).toLocaleString()} - £{((p.max_amount as number) || 0).toLocaleString()}</p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">Term</p>
                  {isEditing ? (
                    <div className="flex gap-1 mt-1">
                      <input type="number" value={editData.min_term_months as number} onChange={(e) => setEditData({ ...editData, min_term_months: parseInt(e.target.value) })} className="w-16 border rounded px-2 py-1" />
                      <span>-</span>
                      <input type="number" value={editData.max_term_months as number} onChange={(e) => setEditData({ ...editData, max_term_months: parseInt(e.target.value) })} className="w-16 border rounded px-2 py-1" />
                      <span className="self-center text-gray-500">mo</span>
                    </div>
                  ) : (
                    <p className="font-medium">{p.min_term_months as number} - {p.max_term_months as number} months</p>
                  )}
                </div>
              </div>
              {isEditing ? (
                <div className="mt-4">
                  <label className="block text-xs text-gray-500 mb-1">Features (comma-separated)</label>
                  <input type="text" value={featuresInput} onChange={(e) => setFeaturesInput(e.target.value)} className="w-full border rounded px-2 py-1 text-sm" />
                  <label className="flex items-center gap-2 mt-2 text-sm">
                    <input type="checkbox" checked={editData.is_active as boolean} onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })} />
                    Active
                  </label>
                </div>
              ) : (
                <div className="mt-4 flex flex-wrap gap-2">
                  {features.map((f, i) => (
                    <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">{f}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ====== Rules Tab ======
const emptyRule: Record<string, unknown> = {
  product_code: "", rule_name: "", rule_type: "threshold",
  parameters: {}, priority: 1, is_active: true,
};

function RulesTab({
  rules,
  products,
  onCreate,
  onUpdate,
  onDelete,
}: {
  rules: Record<string, unknown>[];
  products: Record<string, unknown>[];
  onCreate: (data: Record<string, unknown>) => Promise<void>;
  onUpdate: (id: number, data: Record<string, unknown>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Record<string, unknown>>({});
  const [editParams, setEditParams] = useState<string>("");
  const [showCreate, setShowCreate] = useState(false);
  const [createData, setCreateData] = useState<Record<string, unknown>>({ ...emptyRule });
  const [createParams, setCreateParams] = useState("{}");

  function startEdit(rule: Record<string, unknown>) {
    setEditingId(rule.id as number);
    setEditData({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      priority: rule.priority,
      is_active: rule.is_active,
    });
    setEditParams(JSON.stringify(rule.parameters, null, 2));
  }

  async function saveEdit() {
    if (editingId === null) return;
    try {
      await onUpdate(editingId, { ...editData, parameters: JSON.parse(editParams) });
      setEditingId(null);
    } catch {
      alert("Invalid JSON in parameters");
    }
  }

  async function handleCreate() {
    try {
      await onCreate({ ...createData, parameters: JSON.parse(createParams) });
      setCreateData({ ...emptyRule });
      setCreateParams("{}");
      setShowCreate(false);
    } catch {
      alert("Invalid JSON in parameters");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this rule?")) return;
    await onDelete(id);
  }

  return (
    <div>
      <div className="flex justify-end mb-3">
        <button onClick={() => setShowCreate(!showCreate)} className="px-3 py-1.5 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light">
          {showCreate ? "Cancel" : "+ Add Rule"}
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-4">
          <h3 className="font-semibold mb-4">New Pre-Qualification Rule</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <label className="block text-gray-500 mb-1">Product</label>
              <select value={createData.product_code as string} onChange={(e) => setCreateData({ ...createData, product_code: e.target.value })} className="w-full border rounded px-2 py-1">
                <option value="">Select...</option>
                {products.map((p) => (
                  <option key={p.product_code as string} value={p.product_code as string}>{p.product_name as string}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Rule Name</label>
              <input type="text" value={createData.rule_name as string} onChange={(e) => setCreateData({ ...createData, rule_name: e.target.value })} className="w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Type</label>
              <select value={createData.rule_type as string} onChange={(e) => setCreateData({ ...createData, rule_type: e.target.value })} className="w-full border rounded px-2 py-1">
                <option value="threshold">threshold</option>
                <option value="range">range</option>
                <option value="boolean">boolean</option>
                <option value="scoring">scoring</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Priority</label>
              <input type="number" value={createData.priority as number} onChange={(e) => setCreateData({ ...createData, priority: parseInt(e.target.value) })} className="w-full border rounded px-2 py-1" />
            </div>
            <div className="col-span-2 md:col-span-4">
              <label className="block text-gray-500 mb-1">Parameters (JSON)</label>
              <textarea value={createParams} onChange={(e) => setCreateParams(e.target.value)} rows={3} className="w-full border rounded px-2 py-1 text-xs font-mono" />
            </div>
            <div>
              <label className="flex items-center gap-2 mt-1">
                <input type="checkbox" checked={createData.is_active as boolean} onChange={(e) => setCreateData({ ...createData, is_active: e.target.checked })} />
                Active
              </label>
            </div>
          </div>
          <div className="mt-4">
            <button onClick={handleCreate} className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">Create Rule</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Product</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Rule Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Type</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Parameters</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Priority</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Active</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rules.map((r) => {
              const isEditing = editingId === (r.id as number);
              return (
                <tr key={r.id as number} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{(r.product_name as string) || (r.product_code as string)}</td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <input type="text" value={editData.rule_name as string} onChange={(e) => setEditData({ ...editData, rule_name: e.target.value })} className="w-40 border rounded px-2 py-1 text-sm" />
                    ) : (
                      r.rule_name as string
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <select value={editData.rule_type as string} onChange={(e) => setEditData({ ...editData, rule_type: e.target.value })} className="border rounded px-2 py-1 text-sm">
                        <option value="threshold">threshold</option>
                        <option value="range">range</option>
                        <option value="boolean">boolean</option>
                        <option value="scoring">scoring</option>
                      </select>
                    ) : (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">{r.rule_type as string}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <textarea value={editParams} onChange={(e) => setEditParams(e.target.value)} rows={3} className="w-64 border rounded px-2 py-1 text-xs font-mono" />
                    ) : (
                      <code className="text-xs text-gray-600">{JSON.stringify(r.parameters)}</code>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <input type="number" value={editData.priority as number} onChange={(e) => setEditData({ ...editData, priority: parseInt(e.target.value) })} className="w-16 border rounded px-2 py-1 text-sm" />
                    ) : (
                      r.priority as number
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <input type="checkbox" checked={editData.is_active as boolean} onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })} />
                    ) : (
                      <span className={`w-2 h-2 rounded-full inline-block ${r.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <div className="flex gap-1">
                        <button onClick={saveEdit} className="text-xs bg-green-600 text-white px-2 py-1 rounded">Save</button>
                        <button onClick={() => setEditingId(null)} className="text-xs bg-gray-300 text-gray-700 px-2 py-1 rounded">Cancel</button>
                      </div>
                    ) : (
                      <div className="flex gap-1">
                        <button onClick={() => startEdit(r)} className="text-xs text-citi-blue hover:underline">Edit</button>
                        <button onClick={() => handleDelete(r.id as number)} className="text-xs text-red-600 hover:underline">Delete</button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ====== Results Tab ======
function ResultsTab({ results }: { results: Record<string, unknown>[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
      {results.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No pre-qualification results yet. Run the chatbot to generate results.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Customer</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Product</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Requested</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Approved</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">APR</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Score</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {results.map((r) => (
                <tr key={r.id as number} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-xs">
                    {new Date(r.created_at as string).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">{(r.customer_id as string) || "New customer"}</td>
                  <td className="px-4 py-3">{r.product_code as string}</td>
                  <td className="px-4 py-3">£{((r.requested_amount as number) || 0).toLocaleString()}</td>
                  <td className="px-4 py-3">£{((r.prequalified_amount as number) || 0).toLocaleString()}</td>
                  <td className="px-4 py-3">{r.indicative_apr as number}%</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      (r.affordability_score as number) >= 60
                        ? "bg-green-100 text-green-700"
                        : (r.affordability_score as number) >= 30
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {r.affordability_score as number}/100
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      r.decision === "approved"
                        ? "bg-green-100 text-green-700"
                        : r.decision === "partial"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {r.decision as string}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ====== Config Tab ======
function ConfigTab({
  config,
  onUpdate,
}: {
  config: Record<string, unknown>[];
  onUpdate: (key: string, value: Record<string, unknown>) => Promise<void>;
}) {
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>("");

  function startEdit(cfg: Record<string, unknown>) {
    setEditingKey(cfg.config_key as string);
    setEditValue(JSON.stringify(cfg.config_value, null, 2));
  }

  async function saveEdit() {
    if (!editingKey) return;
    try {
      await onUpdate(editingKey, JSON.parse(editValue));
      setEditingKey(null);
    } catch {
      alert("Invalid JSON");
    }
  }

  return (
    <div className="space-y-4">
      {config.map((cfg) => {
        const isEditing = editingKey === (cfg.config_key as string);
        return (
          <div key={cfg.config_key as string} className="bg-white rounded-xl shadow-sm border p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-800">{cfg.config_key as string}</h4>
                <p className="text-xs text-gray-500 mt-0.5">{cfg.description as string}</p>
              </div>
              {isEditing ? (
                <div className="flex gap-1 ml-4">
                  <button onClick={saveEdit} className="text-xs bg-green-600 text-white px-2 py-1 rounded">Save</button>
                  <button onClick={() => setEditingKey(null)} className="text-xs bg-gray-300 text-gray-700 px-2 py-1 rounded">Cancel</button>
                </div>
              ) : (
                <button onClick={() => startEdit(cfg)} className="text-xs text-citi-blue hover:underline ml-4">Edit</button>
              )}
            </div>
            {isEditing ? (
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                rows={5}
                className="w-full border rounded px-3 py-2 text-sm font-mono mt-2"
              />
            ) : (
              <pre className="mt-2 text-xs bg-gray-50 rounded p-3 overflow-x-auto">
                {JSON.stringify(cfg.config_value, null, 2)}
              </pre>
            )}
          </div>
        );
      })}
    </div>
  );
}
