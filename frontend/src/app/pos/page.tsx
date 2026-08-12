import type { Metadata } from "next";

import { POSWorkspace } from "@/components/pos/pos-workspace";

export const metadata: Metadata = { title: "Point of Sale" };

export default function PosPage() {
  return <POSWorkspace />;
}
