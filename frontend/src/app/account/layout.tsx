import { requireAuthenticated } from "@/lib/server-auth";

export default async function AccountLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  await requireAuthenticated("/account");
  return children;
}
