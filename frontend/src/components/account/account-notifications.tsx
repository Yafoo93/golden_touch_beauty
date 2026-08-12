"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import {
  announceNotificationChange,
  notificationRelativeTime,
  type CustomerNotification,
  type NotificationCategory,
  type NotificationListResponse,
} from "@/lib/notifications";

type ReadFilter = "all" | "unread" | "read";
type CategoryFilter = "all" | NotificationCategory;
const PAGE_SIZE = 12;

export function AccountNotifications() {
  const [items, setItems] = useState<CustomerNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [readFilter, setReadFilter] = useState<ReadFilter>("all");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (offset = 0) => {
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
    });
    if (readFilter !== "all") params.set("read", readFilter);
    if (category !== "all") params.set("category", category);
    const response = await apiFetch<NotificationListResponse>(
      `notifications/?${params.toString()}`,
    );
    setItems((current) =>
      offset === 0 ? response.notifications : [...current, ...response.notifications],
    );
    setUnreadCount(response.unread_count);
    setTotal(response.total);
    setHasMore(response.has_more);
  }, [category, readFilter]);

  useEffect(() => {
    setLoading(true);
    setError("");
    void load()
      .catch((requestError) => {
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : "Notifications could not be loaded.",
        );
      })
      .finally(() => setLoading(false));
  }, [load]);

  async function markRead(notification: CustomerNotification) {
    if (notification.is_read) return;
    setItems((current) => current.map((item) =>
      item.id === notification.id ? { ...item, is_read: true } : item,
    ));
    setUnreadCount((current) => Math.max(0, current - 1));
    try {
      await ensureCsrfCookie();
      await apiFetch(`notifications/${notification.id}/read/`, { method: "POST" });
      announceNotificationChange();
      if (readFilter === "unread") await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Notification could not be updated.");
      await load();
    }
  }

  async function markAllRead() {
    setError("");
    try {
      await ensureCsrfCookie();
      await apiFetch("notifications/read-all/", { method: "POST" });
      announceNotificationChange();
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Notifications could not be updated.");
    }
  }

  async function loadMore() {
    setLoadingMore(true);
    setError("");
    try {
      await load(items.length);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "More notifications could not be loaded.");
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <section className="account-notifications" aria-labelledby="notifications-title">
      <header>
        <div>
          <p>Customer account</p>
          <h1 id="notifications-title">Notifications</h1>
          <span>{unreadCount} unread notification{unreadCount === 1 ? "" : "s"}</span>
        </div>
        <div className="account-notifications__header-actions">
          <Link href="/account">Back to account</Link>
          {unreadCount > 0 ? <Button type="button" size="small" onClick={() => void markAllRead()}>Mark all read</Button> : null}
        </div>
      </header>

      <div className="account-notifications__filters" aria-label="Notification filters">
        <label>
          <span>Status</span>
          <select value={readFilter} onChange={(event) => setReadFilter(event.target.value as ReadFilter)}>
            <option value="all">All</option>
            <option value="unread">Unread</option>
            <option value="read">Read</option>
          </select>
        </label>
        <label>
          <span>Category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value as CategoryFilter)}>
            <option value="all">All categories</option>
            <option value="booking">Bookings</option>
            <option value="order">Orders</option>
            <option value="payment">Payments</option>
            <option value="system">System</option>
          </select>
        </label>
        <span>{total} result{total === 1 ? "" : "s"}</span>
      </div>

      {error ? <p className="form-alert form-alert--error" role="alert">{error}</p> : null}
      {loading ? (
        <p className="account-section-status">Loading notifications...</p>
      ) : items.length === 0 ? (
        <div className="account-notifications__empty">
          <h2>No notifications found</h2>
          <p>New booking, order, and payment updates will appear here.</p>
        </div>
      ) : (
        <ul className="account-notifications__list">
          {items.map((notification) => (
            <li key={notification.id} data-unread={!notification.is_read || undefined}>
              <div>
                <span>{notification.category}</span>
                <strong>{notification.title}</strong>
                <p>{notification.message}</p>
                <time dateTime={notification.created_at}>{notificationRelativeTime(notification.created_at)}</time>
              </div>
              <div>
                {!notification.is_read ? <button type="button" onClick={() => void markRead(notification)}>Mark read</button> : <span>Read</span>}
                <Link href={notification.action_url || "/account"} onClick={() => void markRead(notification)}>View details</Link>
              </div>
            </li>
          ))}
        </ul>
      )}
      {hasMore ? <div className="account-notifications__more"><Button type="button" variant="outline" disabled={loadingMore} onClick={() => void loadMore()}>{loadingMore ? "Loading..." : "Load more"}</Button></div> : null}
    </section>
  );
}
