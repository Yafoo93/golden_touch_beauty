import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import type { AccountOverview as AccountOverviewData } from "@/lib/account-overview";
import { formatGhanaCedis } from "@/lib/formatters";


export function AccountOverview({ data }: { data: AccountOverviewData }) {
  const cards = [
    ["Upcoming", data.summary.upcoming_appointments, "appointments"],
    ["Completed", data.summary.completed_services, "services"],
    ["Orders", data.summary.orders, "purchases"],
    ["Balance due", formatGhanaCedis(data.summary.outstanding_balance), "outstanding"],
  ];

  return (
    <section className="account-overview" aria-labelledby="account-overview-title">
      <header>
        <div><p>Overview</p><h2 id="account-overview-title">At a glance</h2></div>
        <span>Live information from your Golden Touch account.</span>
      </header>
      <div className="account-overview__cards">
        {cards.map(([label, value, detail]) => (
          <article key={label}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>
        ))}
      </div>
      <div className="account-overview__columns">
        <section>
          <header><h3>Upcoming appointments</h3><ButtonLink href="/account/appointments" size="small">View all</ButtonLink></header>
          {data.upcoming_appointments.length ? data.upcoming_appointments.map((booking) => (
            <Link href={`/account/appointments/${booking.reference}`} key={booking.reference} className="account-overview__record">
              <div><strong>{booking.services.join(", ") || "Service appointment"}</strong><span>{booking.branch_name} · {new Date(booking.preferred_start).toLocaleString()}</span></div>
              <span className={`booking-status booking-status--${booking.status}`}>{booking.status.replaceAll("_", " ")}</span>
            </Link>
          )) : <p>No upcoming appointments. Your next booking will appear here.</p>}
        </section>
        <section>
          <header><h3>Recent orders</h3><ButtonLink href="/account/orders" size="small" variant="outline">View all</ButtonLink></header>
          {data.recent_orders.length ? data.recent_orders.map((order) => (
            <Link href={`/account/orders/${encodeURIComponent(order.reference)}`} key={order.reference} className="account-overview__record">
              <div><strong>{order.reference}</strong><span>{order.item_count} item{order.item_count === 1 ? "" : "s"} · {order.branch_name}</span></div>
              <div><b>{formatGhanaCedis(order.total_amount)}</b><span>{order.status.replaceAll("_", " ")}</span></div>
            </Link>
          )) : <p>No product orders yet. Your latest purchases will appear here.</p>}
        </section>
      </div>
      <section className="account-overview__activity">
        <header><h3>Recent activity</h3><ButtonLink href="/account/notifications" size="small" variant="outline">Notifications</ButtonLink></header>
        {data.recent_activity.length ? (
          <ol>{data.recent_activity.map((activity) => (
            <li key={activity.id}><span aria-hidden="true" /><div><strong>{activity.title}</strong><p>{activity.description}</p><small>{activity.reference} · {new Date(activity.timestamp).toLocaleString()}</small></div><Link href={activity.action_url}>{activity.status.replaceAll("_", " ")}</Link></li>
          ))}</ol>
        ) : <p>No recent account activity yet.</p>}
      </section>
    </section>
  );
}
