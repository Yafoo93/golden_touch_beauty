"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { apiFetch } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";

type Branch = { id: string; code: string; name: string };
type CatalogItem = {
  id: string; type: "product" | "service"; name: string; option: string;
  sku: string; category: string; price: string; available_quantity: number | null;
  image_path: string;
};
type Workspace = {
  branches: Branch[]; selected_branch: string | null;
  products: CatalogItem[]; services: CatalogItem[];
};
type SaleLine = CatalogItem & { quantity: number };
type POSCustomer = { id: string; full_name: string; email: string; phone_number: string };
type PaymentMethod = "cash" | "card" | "mobile_money" | "bank_transfer";
type PaymentLine = { id: number; method: PaymentMethod; amount: string; reference: string };
type SavedSale = { reference: string; status: string; payment_status: string; paid_amount: string; outstanding_amount: string };

export function POSWorkspace() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [branch, setBranch] = useState("");
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState<"all" | "product" | "service">("all");
  const [lines, setLines] = useState<SaleLine[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<POSCustomer | null>(null);
  const [customerSearch, setCustomerSearch] = useState("");
  const [customerResults, setCustomerResults] = useState<POSCustomer[]>([]);
  const [customerLoading, setCustomerLoading] = useState(false);
  const [payments, setPayments] = useState<PaymentLine[]>([{ id: 1, method: "cash", amount: "", reference: "" }]);
  const [nextPaymentId, setNextPaymentId] = useState(2);
  const [saving, setSaving] = useState(false);
  const [saleError, setSaleError] = useState("");
  const [savedSale, setSavedSale] = useState<SavedSale | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    function syncConnectivity() {
      setIsOnline(window.navigator.onLine);
    }
    syncConnectivity();
    window.addEventListener("online", syncConnectivity);
    window.addEventListener("offline", syncConnectivity);
    return () => {
      window.removeEventListener("online", syncConnectivity);
      window.removeEventListener("offline", syncConnectivity);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true); setError("");
      try {
        const query = branch ? `?branch=${encodeURIComponent(branch)}` : "";
        const result = await apiFetch<Workspace>(`pos/workspace/${query}`);
        if (!cancelled) {
          setWorkspace(result);
          setBranch(result.selected_branch ?? "");
          setLines([]);
          setSelectedCustomer(null);
          setCustomerSearch("");
          setCustomerResults([]);
          setPayments([{ id: 1, method: "cash", amount: "", reference: "" }]);
          setNextPaymentId(2);
          setSavedSale(null);
          setSaleError("");
        }
      } catch {
        if (!cancelled) setError("The POS catalogue could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [branch]);

  useEffect(() => {
    const term = customerSearch.trim();
    if (!branch || term.length < 2) {
      setCustomerResults([]);
      setCustomerLoading(false);
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setCustomerLoading(true);
      try {
        const result = await apiFetch<{ results: POSCustomer[] }>(
          `pos/customers/?branch=${encodeURIComponent(branch)}&search=${encodeURIComponent(term)}`,
        );
        if (!cancelled) setCustomerResults(result.results);
      } catch {
        if (!cancelled) setCustomerResults([]);
      } finally {
        if (!cancelled) setCustomerLoading(false);
      }
    }, 300);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [branch, customerSearch]);

  const catalogue = useMemo(() => {
    const all = [...(workspace?.products ?? []), ...(workspace?.services ?? [])];
    const term = search.trim().toLowerCase();
    return all.filter((item) =>
      (kind === "all" || item.type === kind) &&
      (!term || `${item.name} ${item.option} ${item.sku} ${item.category}`.toLowerCase().includes(term)),
    );
  }, [workspace, search, kind]);

  const total = lines.reduce((sum, line) => sum + Number(line.price) * line.quantity, 0);
  const productQuantity = lines
    .filter((line) => line.type === "product")
    .reduce((sum, line) => sum + line.quantity, 0);
  const serviceQuantity = lines
    .filter((line) => line.type === "service")
    .reduce((sum, line) => sum + line.quantity, 0);
  const paidAmount = payments.reduce((sum, payment) => sum + (Number(payment.amount) || 0), 0);
  const outstandingAmount = Math.max(total - paidAmount, 0);
  const paymentIsValid = payments.length > 0 && payments.every((payment) =>
    Number(payment.amount) > 0 && (payment.method === "cash" || payment.reference.trim().length > 0),
  ) && paidAmount <= total;
  function add(item: CatalogItem) {
    setSavedSale(null); setSaleError("");
    setLines((current) => {
      const existing = current.find((line) => line.id === item.id && line.type === item.type);
      if (existing) return current.map((line) => line === existing ? {
        ...line,
        quantity: Math.min(line.quantity + 1, item.available_quantity ?? 99),
      } : line);
      return [...current, { ...item, quantity: 1 }];
    });
  }
  function change(line: SaleLine, quantity: number) {
    setSavedSale(null); setSaleError("");
    if (quantity < 1) {
      setLines((current) => current.filter((item) => item !== line));
      return;
    }
    setLines((current) => current.map((item) => item === line ? {
      ...item, quantity: Math.min(quantity, item.available_quantity ?? 99),
    } : item));
  }

  function updatePayment(id: number, changes: Partial<PaymentLine>) {
    setSavedSale(null); setSaleError("");
    setPayments((current) => current.map((payment) => payment.id === id ? { ...payment, ...changes } : payment));
  }

  function addPayment() {
    setPayments((current) => [...current, { id: nextPaymentId, method: "cash", amount: "", reference: "" }]);
    setNextPaymentId((value) => value + 1);
  }

  async function recordPayment() {
    if (!branch || !lines.length || !paymentIsValid) return;
    if (!window.navigator.onLine) {
      setIsOnline(false);
      setSaleError("Sale completion is blocked while offline. Reconnect, then check Sale History before trying again.");
      return;
    }
    setSaving(true); setSaleError(""); setSavedSale(null);
    try {
      const result = await apiFetch<SavedSale>("pos/sales/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          branch,
          customer: selectedCustomer?.id ?? null,
          lines: lines.map((line) => ({ item_type: line.type, item_reference: line.id, quantity: line.quantity })),
          payments: payments.map(({ method, amount, reference }) => ({ method, amount, reference })),
        }),
      });
      setSavedSale(result);
      setWorkspace((current) => current ? {
        ...current,
        products: current.products.map((product) => {
          const sold = lines.find((line) => line.type === "product" && line.id === product.id);
          return sold && product.available_quantity !== null
            ? { ...product, available_quantity: Math.max(0, product.available_quantity - sold.quantity) }
            : product;
        }),
      } : current);
    } catch (caught) {
      if (!window.navigator.onLine) setIsOnline(false);
      setSaleError(
        !window.navigator.onLine
          ? "Connectivity was lost. This sale is not confirmed in this browser. Reconnect and check Sale History before attempting another payment."
          : caught instanceof Error
            ? `${caught.message} The sale was not confirmed. Check Sale History before retrying.`
            : "The sale was not confirmed. Check Sale History before retrying.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="pos-workspace">
      {!isOnline ? <aside className="pos-connectivity-alert" role="alert" aria-live="assertive">
        <strong>POS is offline — sale completion is blocked.</strong>
        <span>Reconnect to the internet, then check <Link href="/pos/sales">Sale History</Link> before accepting or retrying payment. Offline sales are not queued in Phase 1.</span>
      </aside> : null}
      <header className="pos-workspace__header">
        <div><p>Staff portal · Point of sale</p><h1>Current sale</h1><span>Search the selected branch catalogue and compose an in-clinic sale.</span></div>
        <label>POS branch<select value={branch} onChange={(event) => setBranch(event.target.value)} disabled={loading}>
          <option value="">Select an assigned branch</option>
          {(workspace?.branches ?? []).map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
        </select></label>
      </header>
      <div className="pos-workspace__layout">
        <section className="pos-catalogue">
          <div className="pos-catalogue__tools">
            <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products, services, SKU or category" aria-label="Search POS catalogue" />
            <div>{(["all", "product", "service"] as const).map((value) => <button className={kind === value ? "is-active" : ""} onClick={() => setKind(value)} type="button" key={value}>{value === "all" ? "All" : `${value}s`}</button>)}</div>
          </div>
          {loading ? <LoadingIndicator label="Loading branch catalogue…" /> : error ? <EmptyState title="POS unavailable" description={error} /> : !workspace?.selected_branch ? <EmptyState title="Select a POS branch" description="Choose one of your assigned branches before adding products or services to the current sale." /> : catalogue.length === 0 ? <EmptyState title="No matching items" description="Try another search or catalogue filter." /> : (
            <div className="pos-catalogue__grid">{catalogue.map((item) => <article key={`${item.type}:${item.id}`}>
              <small>{item.type} · {item.category}</small><h2>{item.name}</h2><p>{item.option}{item.sku ? ` · ${item.sku}` : ""}</p>
              <div><strong>{formatGhanaCedis(item.price)}</strong><button type="button" onClick={() => add(item)}>Add</button></div>
              {item.available_quantity !== null ? <span>{item.available_quantity} available</span> : null}
            </article>)}</div>
          )}
        </section>
        <aside className="pos-sale" aria-label="Current sale">
          <header><div><p>Current sale</p><h2>{lines.length} line{lines.length === 1 ? "" : "s"}</h2></div>{lines.length ? <button type="button" onClick={() => setLines([])}>Clear</button> : null}</header>
          <section className="pos-sale__customer" aria-labelledby="pos-customer-title">
            <div><h3 id="pos-customer-title">Customer</h3><span>{selectedCustomer ? "Existing customer" : "Walk-in customer"}</span></div>
            {selectedCustomer ? <article>
              <div><strong>{selectedCustomer.full_name}</strong><small>{selectedCustomer.phone_number} · {selectedCustomer.email}</small></div>
              <button type="button" onClick={() => setSelectedCustomer(null)}>Use walk-in</button>
            </article> : <>
              <label htmlFor="pos-customer-search">Find an existing customer</label>
              <input id="pos-customer-search" type="search" value={customerSearch} onChange={(event) => setCustomerSearch(event.target.value)} placeholder="Name, email, or phone" disabled={!workspace?.selected_branch} />
              {customerLoading ? <small>Searching customers…</small> : null}
              {customerResults.length ? <div className="pos-sale__customer-results">{customerResults.map((customer) => <button type="button" key={customer.id} onClick={() => {
                setSelectedCustomer(customer); setCustomerSearch(""); setCustomerResults([]);
              }}><strong>{customer.full_name}</strong><small>{customer.phone_number} · {customer.email}</small></button>)}</div> : customerSearch.trim().length >= 2 && !customerLoading ? <small>No matching customers. This sale will remain a walk-in sale.</small> : null}
            </>}
          </section>
          {lines.length ? <div className="pos-sale__mix" aria-label="Sale item summary">
            <span>{productQuantity} product{productQuantity === 1 ? "" : "s"}</span>
            <span>{serviceQuantity} service{serviceQuantity === 1 ? "" : "s"}</span>
          </div> : null}
          {lines.length === 0 ? <p className="pos-sale__empty">Add a product or service to begin this sale.</p> : <div className="pos-sale__lines">{lines.map((line) => <article key={`${line.type}:${line.id}`}>
            <div><span className={`pos-sale__type pos-sale__type--${line.type}`}>{line.type}</span><strong>{line.name}</strong><small>{line.option}</small></div><b>{formatGhanaCedis(Number(line.price) * line.quantity)}</b>
            <div className="pos-sale__quantity"><button type="button" onClick={() => change(line, line.quantity - 1)}>−</button><span>{line.quantity}</span><button type="button" onClick={() => change(line, line.quantity + 1)}>+</button></div>
          </article>)}</div>}
          {lines.length ? <section className="pos-sale__payments" aria-labelledby="pos-payments-title">
            <div><h3 id="pos-payments-title">Payments</h3><button type="button" onClick={addPayment}>+ Split payment</button></div>
            {payments.map((payment, index) => <fieldset key={payment.id}>
              <legend>Payment {index + 1}</legend>
              <select value={payment.method} onChange={(event) => updatePayment(payment.id, { method: event.target.value as PaymentMethod, reference: "" })} aria-label={`Payment ${index + 1} method`}>
                <option value="cash">Cash</option>
                <option value="card">Card / approved electronic</option>
                <option value="mobile_money">Mobile money / approved electronic</option>
                <option value="bank_transfer">Bank transfer record</option>
              </select>
              <input type="number" min="0.01" step="0.01" value={payment.amount} onChange={(event) => updatePayment(payment.id, { amount: event.target.value })} placeholder="Amount" aria-label={`Payment ${index + 1} amount`} />
              {payment.method !== "cash" ? <input value={payment.reference} onChange={(event) => updatePayment(payment.id, { reference: event.target.value })} placeholder="Transaction / transfer reference" aria-label={`Payment ${index + 1} reference`} /> : null}
              {payments.length > 1 ? <button type="button" onClick={() => setPayments((current) => current.filter((item) => item.id !== payment.id))}>Remove</button> : null}
            </fieldset>)}
            <dl><div><dt>Paid</dt><dd>{formatGhanaCedis(paidAmount)}</dd></div><div><dt>Outstanding</dt><dd>{formatGhanaCedis(outstandingAmount)}</dd></div></dl>
            {paidAmount > total ? <p className="pos-sale__payment-error">Payment entries cannot exceed the sale total.</p> : null}
          </section> : null}
          <footer><span>Total</span><strong>{formatGhanaCedis(total)}</strong><button type="button" title={!isOnline ? "Reconnect to complete this sale" : undefined} disabled={!isOnline || !branch || !lines.length || !paymentIsValid || saving || Boolean(savedSale)} onClick={() => void recordPayment()}>{!isOnline ? "Offline — completion blocked" : saving ? "Completing sale…" : savedSale ? "Sale completed" : "Complete sale"}</button>{saleError ? <small className="pos-sale__payment-error">{saleError} <Link href="/pos/sales">Check Sale History</Link>.</small> : savedSale ? <small className="pos-sale__payment-success">Sale {savedSale.reference} completed · {savedSale.payment_status.replaceAll("_", " ")} · {formatGhanaCedis(savedSale.outstanding_amount)} outstanding. <Link href={`/pos/sales/${savedSale.reference}`}>View and print receipt</Link>.</small> : <small>Use one payment for cash or electronic payment, or add entries for a split payment. Paying less than the total records a partial payment.</small>}</footer>
        </aside>
      </div>
    </main>
  );
}
