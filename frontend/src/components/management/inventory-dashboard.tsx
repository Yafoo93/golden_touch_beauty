"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementInventoryItem } from "@/lib/management-inventory";

export function InventoryDashboard({
  inventory,
  initialLowOnly = false,
}: {
  inventory: ManagementInventoryItem[];
  initialLowOnly?: boolean;
}) {
  const [branch, setBranch] = useState("all");
  const [search, setSearch] = useState("");
  const [lowOnly, setLowOnly] = useState(initialLowOnly);
  const branches = useMemo(
    () =>
      Array.from(
        new Map(
          inventory.map((item) => [
            item.branch_id,
            { id: item.branch_id, name: item.branch_name, code: item.branch_code },
          ]),
        ).values(),
      ).sort((a, b) => a.name.localeCompare(b.name)),
    [inventory],
  );
  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    return inventory.filter(
      (item) =>
        (branch === "all" || item.branch_id === branch) &&
        (!lowOnly || item.is_low_stock) &&
        (!query ||
          [item.product_name, item.variant_name, item.sku, item.category_name]
            .join(" ")
            .toLowerCase()
            .includes(query)),
    );
  }, [branch, inventory, lowOnly, search]);
  const totals = visible.reduce(
    (sum, item) => ({
      onHand: sum.onHand + item.quantity_on_hand,
      reserved: sum.reserved + item.quantity_reserved,
      available: sum.available + item.quantity_available,
      low: sum.low + Number(item.is_low_stock),
    }),
    { onHand: 0, reserved: 0, available: 0, low: 0 },
  );

  return (
    <div className="inventory-dashboard">
      <section className="inventory-dashboard__filters" aria-label="Inventory filters">
        <div className="form-field">
          <label className="form-field__label" htmlFor="inventory-search">Search stock</label>
          <input className="form-field__control" id="inventory-search" type="search" placeholder="Product, variant, SKU, or category" value={search} onChange={(event) => setSearch(event.target.value)} />
        </div>
        <div className="form-field">
          <label className="form-field__label" htmlFor="inventory-branch">Branch</label>
          <select className="form-field__control" id="inventory-branch" value={branch} onChange={(event) => setBranch(event.target.value)}>
            <option value="all">All accessible branches</option>
            {branches.map((item) => <option value={item.id} key={item.id}>{item.name} ({item.code})</option>)}
          </select>
        </div>
        <label className="management-form__toggle">
          <input type="checkbox" checked={lowOnly} onChange={(event) => setLowOnly(event.target.checked)} />
          <span><strong>Low stock only</strong><small>At or below reorder level.</small></span>
        </label>
      </section>

      <section className="inventory-dashboard__totals" aria-label="Visible inventory totals">
        <div><strong>{visible.length}</strong><span>Stock records</span></div>
        <div><strong>{totals.onHand}</strong><span>On hand</span></div>
        <div><strong>{totals.reserved}</strong><span>Reserved</span></div>
        <div><strong>{totals.available}</strong><span>Available</span></div>
        <div className={totals.low ? "inventory-dashboard__warning" : ""}><strong>{totals.low}</strong><span>Low stock</span></div>
      </section>

      {!visible.length ? (
        <EmptyState title="No stock records found" description="Try another branch, search term, or remove the low-stock filter." />
      ) : (
        <div className="inventory-dashboard__table-wrap">
          <table className="inventory-dashboard__table">
            <thead><tr><th>Product</th><th>Branch</th><th>Price</th><th>On hand</th><th>Reserved</th><th>Available</th><th>Reorder</th><th>Status</th></tr></thead>
            <tbody>
              {visible.map((item) => (
                <tr key={item.id}>
                  <td><Link className="inventory-dashboard__product-link" href={`/management/inventory/${item.variant_id}`}><strong>{item.product_name}</strong><span>{item.variant_name} / {item.sku}</span></Link><small>{item.category_name}</small></td>
                  <td><strong>{item.branch_name}</strong><span>{item.branch_code}</span></td>
                  <td>{formatGhanaCedis(item.selling_price)}</td>
                  <td>{item.quantity_on_hand}</td>
                  <td>{item.quantity_reserved}</td>
                  <td>{item.quantity_available}</td>
                  <td>{item.reorder_level}</td>
                  <td><span className={`status-badge status-badge--${item.is_low_stock ? "inactive" : "active"}`}>{item.is_low_stock ? "Low stock" : item.is_available ? "Available" : "Unavailable"}</span>{!item.variant_is_active ? <small>Variant inactive</small> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
