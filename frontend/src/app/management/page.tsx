import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { getCurrentUser } from "@/lib/server-auth";

export const metadata: Metadata = { title: "Management" };

type ManagementOverview = {
  staff: {
    full_name: string;
    is_owner: boolean;
    scope_label: string;
  };
  branches: {
    id: string;
    code: string;
    name: string;
    is_active: boolean;
    roles: string[];
  }[];
  filter_options: {
    branches: { id: string; code: string; name: string }[];
    product_categories: { id: string; name: string }[];
    service_categories: { id: string; name: string }[];
    payment_methods: { value: string; label: string }[];
    booking_statuses: { value: string; label: string }[];
    order_statuses: { value: string; label: string }[];
  };
  branch_comparison: { id: string; code: string; name: string; appointments: number; sales: string; pending_orders: number; low_stock: number }[];
  summary: {
    today_appointments: number;
    pending_booking_requests: number;
    proposed_changes_awaiting_acceptance: number;
    today_sales: string;
    product_revenue: string;
    service_revenue: string;
    outstanding_balances: string;
    pending_online_orders: number;
    low_stock_products: number;
  };
};

type ManagementFilters = {
  date_from?: string;
  date_to?: string;
  branch?: string;
  product_category?: string;
  service_category?: string;
  payment_method?: string;
  booking_status?: string;
  order_status?: string;
};

async function loadOverview(filters: ManagementFilters): Promise<ManagementOverview | null> {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  try {
    const response = await fetch(
      `${base}/api/v1/branches/management/overview/?${query.toString()}`,
      {
        cache: "no-store",
        headers: {
          Accept: "application/json",
          Cookie: (await cookies()).toString(),
        },
        signal: AbortSignal.timeout(20_000),
      },
    );
    return response.ok ? ((await response.json()) as ManagementOverview) : null;
  } catch {
    return null;
  }
}

function roleLabel(role: string) {
  return role.replaceAll("_", " ");
}

export default async function ManagementPage({
  searchParams,
}: {
  searchParams: Promise<ManagementFilters>;
}) {
  const filters = await searchParams;
  const user = await getCurrentUser();
  if (user && !user.management_modules.includes("dashboard")) {
    redirect(user.management_modules.includes("inventory") ? "/management/inventory" : (user.post_login_path ?? "/"));
  }
  const overview = await loadOverview(filters);
  const hasFilters = Object.values(filters).some(Boolean);
  const dateFiltered = Boolean(filters.date_from || filters.date_to);

  if (!overview) {
    return (
      <main className="portal-landing">
        <EmptyState
          title="Management overview unavailable"
          description="The management data could not be loaded. Please try again."
          action={<ButtonLink href="/management">Try again</ButtonLink>}
        />
      </main>
    );
  }

  return (
    <main className="management-overview">
      <header className="management-overview__header">
        <div>
          <p>{overview.staff.is_owner ? "Owner portal" : "Management portal"}</p>
          <h1>Welcome, {overview.staff.full_name.split(" ")[0]}</h1>
          <span>
            Review and manage the Golden Touch operation within your authorized scope.
          </span>
        </div>
        <div className="management-overview__scope">
          <span>Operating scope</span>
          <strong>{overview.staff.scope_label}</strong>
          <small>{overview.staff.is_owner ? "Business owner access" : "Assignment-based access"}</small>
        </div>
      </header>

      <section className="management-overview__filters" aria-labelledby="management-filters-title">
        <header>
          <div>
            <p>Refine dashboard</p>
            <h2 id="management-filters-title">Filters</h2>
          </div>
          {hasFilters ? (
            <ButtonLink href="/management" variant="outline" size="small">
              Clear all
            </ButtonLink>
          ) : null}
        </header>
        <form>
          <label>
            From date
            <input type="date" name="date_from" defaultValue={filters.date_from ?? ""} />
          </label>
          <label>
            To date
            <input type="date" name="date_to" defaultValue={filters.date_to ?? ""} />
          </label>
          <label>
            Branch
            <select name="branch" defaultValue={filters.branch ?? ""}>
              <option value="">All accessible branches</option>
              {overview.filter_options.branches.map((branch) => (
                <option value={branch.id} key={branch.id}>{branch.name}</option>
              ))}
            </select>
          </label>
          <label>
            Product category
            <select name="product_category" defaultValue={filters.product_category ?? ""}>
              <option value="">All product categories</option>
              {overview.filter_options.product_categories.map((category) => (
                <option value={category.id} key={category.id}>{category.name}</option>
              ))}
            </select>
          </label>
          <label>
            Service category
            <select name="service_category" defaultValue={filters.service_category ?? ""}>
              <option value="">All service categories</option>
              {overview.filter_options.service_categories.map((category) => (
                <option value={category.id} key={category.id}>{category.name}</option>
              ))}
            </select>
          </label>
          <label>
            Payment method
            <select name="payment_method" defaultValue={filters.payment_method ?? ""}>
              <option value="">All payment methods</option>
              {overview.filter_options.payment_methods.map((method) => (
                <option value={method.value} key={method.value}>{method.label}</option>
              ))}
            </select>
          </label>
          <label>
            Booking status
            <select name="booking_status" defaultValue={filters.booking_status ?? ""}>
              <option value="">All booking statuses</option>
              {overview.filter_options.booking_statuses.map((item) => (
                <option value={item.value} key={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label>
            Order status
            <select name="order_status" defaultValue={filters.order_status ?? ""}>
              <option value="">All order statuses</option>
              {overview.filter_options.order_statuses.map((item) => (
                <option value={item.value} key={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <button type="submit">Apply filters</button>
        </form>
      </section>

      <section className="management-overview__metrics" aria-label="Management summary">
        <article>
          <div>
            <span>{dateFiltered ? "Appointments in period" : "Today&apos;s appointments"}</span>
            <strong>{overview.summary.today_appointments}</strong>
          </div>
          <p>Active appointments scheduled today across your authorized branches.</p>
          <ButtonLink href="/management/bookings" variant="outline" size="small">
            View bookings
          </ButtonLink>
        </article>
        <article>
          <div>
            <span>Pending booking requests</span>
            <strong>{overview.summary.pending_booking_requests}</strong>
          </div>
          <p>Customer booking requests that are waiting for management review.</p>
          <ButtonLink href="/management/bookings?status=pending" variant="outline" size="small">
            Review requests
          </ButtonLink>
        </article>
        <article>
          <div>
            <span>Proposed changes awaiting acceptance</span>
            <strong>{overview.summary.proposed_changes_awaiting_acceptance}</strong>
          </div>
          <p>Active appointment-time proposals waiting for the customer&apos;s response.</p>
          <ButtonLink href="/management/bookings?status=proposed" variant="outline" size="small">
            View proposals
          </ButtonLink>
        </article>
        <article>
          <div>
            <span>{dateFiltered ? "Sales in period" : "Today&apos;s sales"}</span>
            <strong>{formatGhanaCedis(overview.summary.today_sales)}</strong>
          </div>
          <p>Successful GHS payments received today across your authorized branches.</p>
          <small className="management-overview__metric-note">Verified payments only</small>
        </article>
        <article>
          <div>
            <span>Product revenue</span>
            <strong>{formatGhanaCedis(overview.summary.product_revenue)}</strong>
          </div>
          <p>All-time successful payments allocated to product orders in your branch scope.</p>
          <small className="management-overview__metric-note">Paid product orders</small>
        </article>
        <article>
          <div>
            <span>Service revenue</span>
            <strong>{formatGhanaCedis(overview.summary.service_revenue)}</strong>
          </div>
          <p>All-time successful payments allocated to service bookings in your branch scope.</p>
          <small className="management-overview__metric-note">Paid appointments</small>
        </article>
        <article>
          <div>
            <span>Outstanding balances</span>
            <strong>{formatGhanaCedis(overview.summary.outstanding_balances)}</strong>
          </div>
          <p>Amounts still due on open customer invoices in your authorized branches.</p>
          <small className="management-overview__metric-note">Open invoices only</small>
        </article>
        <article>
          <div>
            <span>Pending online orders</span>
            <strong>{overview.summary.pending_online_orders}</strong>
          </div>
          <p>Website orders still awaiting payment, review, preparation, pickup, or delivery.</p>
          <small className="management-overview__metric-note">Active fulfilment pipeline</small>
        </article>
        <article>
          <div>
            <span>Low-stock products</span>
            <strong>{overview.summary.low_stock_products}</strong>
          </div>
          <p>Branch stock records whose available quantity is at or below the reorder level.</p>
          <ButtonLink href="/management/inventory?low_stock=true" variant="outline" size="small">
            Review stock
          </ButtonLink>
        </article>
      </section>

      <section className="management-overview__branches" aria-labelledby="management-branches-title">
        <header>
          <div><p>Locations</p><h2 id="management-branches-title">Your branches</h2></div>
          {overview.staff.is_owner ? <ButtonLink href="/management/branches" variant="outline" size="small">Manage branches</ButtonLink> : null}
        </header>
        <div>
          {overview.branches.map((branch) => (
            <article key={branch.id}>
              <div><h3>{branch.name}</h3><span>{branch.code}</span></div>
              <p>{branch.roles.map(roleLabel).join(" · ")}</p>
              <small className={branch.is_active ? "status-dot status-dot--active" : "status-dot"}>{branch.is_active ? "Active" : "Inactive"}</small>
            </article>
          ))}
        </div>
      </section>

      {overview.staff.is_owner && overview.branch_comparison.length > 1 ? (
        <section className="management-overview__branches" aria-labelledby="branch-comparison-title">
          <header><div><p>Owner view</p><h2 id="branch-comparison-title">Branch comparison</h2></div></header>
          <div>
            {overview.branch_comparison.map((branch) => (
              <article key={branch.id}>
                <div><h3>{branch.name}</h3><span>{branch.code}</span></div>
                <p>{branch.appointments} appointments · {formatGhanaCedis(branch.sales)} sales</p>
                <small>{branch.pending_orders} pending orders · {branch.low_stock} low-stock records</small>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="portal-landing__panel management-overview__workspace">
        <h2>Management workspace</h2>
        <p>Open the operational area you need. Access inside each module remains limited by your branch assignments and permissions.</p>
        <div><ButtonLink href="/management/bookings">Bookings</ButtonLink><ButtonLink href="/management/bookings/new">Assisted booking</ButtonLink><ButtonLink href="/management/booking-blocks">Booking blocks</ButtonLink><ButtonLink href="/management/services">Services</ButtonLink><ButtonLink href="/management/products">Products</ButtonLink><ButtonLink href="/management/inventory">Inventory</ButtonLink><ButtonLink href="/management/service-categories">Service categories</ButtonLink><ButtonLink href="/management/product-categories">Product categories</ButtonLink><ButtonLink href="/management/content">Website content</ButtonLink><ButtonLink href="/management/gallery">Gallery</ButtonLink><ButtonLink href="/management/testimonials">Testimonials</ButtonLink><ButtonLink href="/logout" variant="black">Sign out</ButtonLink></div>
      </section>
    </main>
  );
}
