import { PortalNavigation } from "@/components/management/portal-navigation";
import { requirePortalAccess } from "@/lib/server-auth";

export default async function PosLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await requirePortalAccess("pos", "/pos");
  return (
    <>
      <PortalNavigation portalAccess={user.portal_access} />
      {children}
    </>
  );
}
