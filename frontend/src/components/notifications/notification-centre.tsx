"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CartItemCount } from "@/components/cart/cart-item-count";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import {
  notificationRelativeTime,
  type CustomerNotification,
  type NotificationListResponse,
} from "@/lib/notifications";

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </svg>
  );
}

export function NotificationCentre({ enabled }: { enabled: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<CustomerNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  async function loadNotifications(showLoading = false) {
    if (!enabled) return;
    if (showLoading) setLoading(true);
    try {
      const result = await apiFetch<NotificationListResponse>("notifications/?limit=8");
      setItems(result.notifications);
      setUnreadCount(result.unread_count);
      setError("");
    } catch (requestError) {
      if (
        !(requestError instanceof ApiError) ||
        ![401, 403].includes(requestError.status)
      ) {
        setError("Notifications could not be loaded.");
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  }

  useEffect(() => {
    if (!enabled) {
      setItems([]);
      setUnreadCount(0);
      setOpen(false);
      return;
    }
    void loadNotifications();
    const timer = window.setInterval(() => void loadNotifications(), 60_000);
    const refresh = () => void loadNotifications();
    window.addEventListener("golden-touch:notifications-changed", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("golden-touch:notifications-changed", refresh);
    };
  }, [enabled, pathname]);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", close);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", close);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  async function markRead(notification: CustomerNotification) {
    if (notification.is_read) return;
    setItems((current) =>
      current.map((item) =>
        item.id === notification.id ? { ...item, is_read: true } : item,
      ),
    );
    setUnreadCount((current) => Math.max(0, current - 1));
    try {
      await ensureCsrfCookie();
      await apiFetch(`notifications/${notification.id}/read/`, {
        method: "POST",
      });
    } catch {
      void loadNotifications();
    }
  }

  async function markAllRead() {
    const previousItems = items;
    const previousCount = unreadCount;
    setItems((current) => current.map((item) => ({ ...item, is_read: true })));
    setUnreadCount(0);
    try {
      await ensureCsrfCookie();
      await apiFetch("notifications/read-all/", { method: "POST" });
    } catch {
      setItems(previousItems);
      setUnreadCount(previousCount);
      setError("Notifications could not be updated.");
    }
  }

  return (
    <div className="notification-centre" ref={containerRef}>
      <button
        className="notification-centre__trigger"
        type="button"
        aria-label={`Notifications, ${unreadCount} unread`}
        aria-haspopup="dialog"
        aria-expanded={open}
        data-unread={unreadCount > 0 || undefined}
        title="Notifications"
        onClick={() => {
          if (!enabled) {
            window.location.assign(
              `/login?next=${encodeURIComponent("/account/notifications")}`,
            );
            return;
          }
          const nextOpen = !open;
          setOpen(nextOpen);
          if (nextOpen) void loadNotifications(true);
        }}
      >
        <BellIcon />
        <CartItemCount count={unreadCount} className="notification-centre__count" />
      </button>

      {open ? (
        <section className="notification-centre__panel" aria-label="Recent notifications">
          <header>
            <div>
              <strong>Notifications</strong>
              <span>{unreadCount} unread</span>
            </div>
            {unreadCount > 0 ? (
              <button type="button" onClick={() => void markAllRead()}>
                Mark all read
              </button>
            ) : null}
          </header>
          {loading && items.length === 0 ? (
            <p className="notification-centre__state">Loading notifications…</p>
          ) : error && items.length === 0 ? (
            <p className="notification-centre__state" role="alert">{error}</p>
          ) : items.length === 0 ? (
            <p className="notification-centre__state">You have no notifications yet.</p>
          ) : (
            <ul>
              {items.map((notification) => (
                <li key={notification.id} data-unread={!notification.is_read || undefined}>
                  <Link
                    href={notification.action_url || "/account"}
                    onClick={() => {
                      void markRead(notification);
                      setOpen(false);
                    }}
                  >
                    <span className="notification-centre__category">
                      {notification.category}
                    </span>
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <time dateTime={notification.created_at}>
                      {notificationRelativeTime(notification.created_at)}
                    </time>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <footer>
            <Link href="/account/notifications" onClick={() => setOpen(false)}>
              View all notifications
            </Link>
          </footer>
        </section>
      ) : null}
    </div>
  );
}
