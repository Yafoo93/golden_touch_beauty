import { PortalNavigation } from "@/components/management/portal-navigation";
import { requirePortalAccess } from "@/lib/server-auth";

export default async function ManagementLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await requirePortalAccess("management", "/management");
  return (
    <>
      <PortalNavigation portalAccess={user.portal_access} />
      {children}
    </>
  );
}
