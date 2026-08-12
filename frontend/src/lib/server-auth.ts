import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export type PortalAccess = "management" | "pos";
export type ManagementModule = "dashboard" | "branches" | "services" | "products" | "inventory" | "bookings" | "customers" | "orders" | "payments" | "reports" | "staff_access" | "audit_log" | "content";

export type CurrentUser = {
  id: string;
  full_name: string;
  email: string;
  phone_number: string;
  date_of_birth: string | null;
  gender: "female" | "male" | "other" | "prefer_not_to_say" | "";
  portal_access: PortalAccess[];
  management_modules: ManagementModule[];
  post_login_path: string | null;
  is_staff: boolean;
  is_superuser: boolean;
};

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const backendUrl = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const cookieHeader = (await cookies()).toString();

  if (!cookieHeader.includes("sessionid=")) return null;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(`${backendUrl}/api/v1/auth/me/`, {
        cache: "no-store",
        headers: {
          Accept: "application/json",
          Cookie: cookieHeader,
        },
        signal: AbortSignal.timeout(20_000),
      });
      if (response.status === 401 || response.status === 403) return null;
      if (response.ok) {
        return ((await response.json()) as { user: CurrentUser }).user;
      }
    } catch {
      // A sleeping development backend is retried before treating the session
      // as unavailable.
    }
    if (attempt < 2) {
      await new Promise((resolve) => setTimeout(resolve, 1_000 * (attempt + 1)));
    }
  }
  return null;
}

export async function requireAuthenticated(returnTo: string) {
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(returnTo)}`);
  return user;
}

export async function requirePortalAccess(
  portal: PortalAccess,
  returnTo: string,
) {
  const user = await requireAuthenticated(returnTo);
  if (!user.portal_access.includes(portal)) {
    redirect(user.post_login_path ?? "/account");
  }
  return user;
}
