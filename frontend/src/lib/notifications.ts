export type NotificationCategory = "booking" | "order" | "payment" | "system";

export type CustomerNotification = {
  id: string;
  category: NotificationCategory;
  title: string;
  message: string;
  action_url: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  notifications: CustomerNotification[];
  unread_count: number;
  total: number;
  offset: number;
  limit: number;
  has_more: boolean;
};

export function notificationRelativeTime(value: string) {
  const elapsed = Date.now() - new Date(value).getTime();
  const minutes = Math.max(0, Math.floor(elapsed / 60_000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days < 7
    ? `${days}d ago`
    : new Intl.DateTimeFormat("en-GH", { dateStyle: "medium" }).format(
        new Date(value),
      );
}

export function announceNotificationChange() {
  window.dispatchEvent(new Event("golden-touch:notifications-changed"));
}
