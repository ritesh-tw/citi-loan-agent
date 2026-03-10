/**
 * Admin API client for managing loan application data.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function adminFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Stats
export async function getStats() {
  return adminFetch("/api/admin/stats");
}

// Customers
export async function getCustomers() {
  return adminFetch("/api/admin/customers");
}

export async function updateCustomer(id: number, data: Record<string, unknown>) {
  return adminFetch(`/api/admin/customers/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function createCustomer(data: Record<string, unknown>) {
  return adminFetch("/api/admin/customers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteCustomer(id: number) {
  return adminFetch(`/api/admin/customers/${id}`, {
    method: "DELETE",
  });
}

// Loan Products
export async function getLoanProducts() {
  return adminFetch("/api/admin/loan-products");
}

export async function updateLoanProduct(id: number, data: Record<string, unknown>) {
  return adminFetch(`/api/admin/loan-products/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function createLoanProduct(data: Record<string, unknown>) {
  return adminFetch("/api/admin/loan-products", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteLoanProduct(id: number) {
  return adminFetch(`/api/admin/loan-products/${id}`, {
    method: "DELETE",
  });
}

// Pre-qualification Rules
export async function getPrequalRules() {
  return adminFetch("/api/admin/prequalification-rules");
}

export async function updatePrequalRule(id: number, data: Record<string, unknown>) {
  return adminFetch(`/api/admin/prequalification-rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function createPrequalRule(data: Record<string, unknown>) {
  return adminFetch("/api/admin/prequalification-rules", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deletePrequalRule(id: number) {
  return adminFetch(`/api/admin/prequalification-rules/${id}`, {
    method: "DELETE",
  });
}

// Pre-qualification Results
export async function getPrequalResults() {
  return adminFetch("/api/admin/prequalification-results");
}

// Config
export async function getConfig() {
  return adminFetch("/api/admin/config");
}

export async function updateConfig(key: string, value: Record<string, unknown>) {
  return adminFetch(`/api/admin/config/${key}`, {
    method: "PUT",
    body: JSON.stringify({ config_value: value }),
  });
}

// Reset
export async function resetData() {
  return adminFetch("/api/admin/reset-data", { method: "POST" });
}
