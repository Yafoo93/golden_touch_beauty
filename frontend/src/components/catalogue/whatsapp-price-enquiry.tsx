"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { whatsappUrl } from "@/lib/branch-formatters";

export type EnquiryBranch = { code: string; name: string; whatsapp_number: string };

export function WhatsAppPriceEnquiry({ itemType, itemName, sku, branches, compact = false }: {
  itemType: "product" | "service";
  itemName: string;
  sku?: string;
  branches: EnquiryBranch[];
  compact?: boolean;
}) {
  const usable = branches.filter((branch) => branch.whatsapp_number);
  const [code, setCode] = useState(usable[0]?.code ?? "");
  const branch = usable.find((candidate) => candidate.code === code);
  function enquire() {
    if (!branch) return;
    const page = window.location.href;
    const detail = sku ? ` (SKU: ${sku})` : "";
    const message = `Hello Golden Touch Beauty Centre. Please share the current price for ${itemName}${detail}, listed as a ${itemType}. I am enquiring through the ${branch.name} branch.\n\n${page}`;
    window.open(whatsappUrl(branch.whatsapp_number, message), "_blank", "noopener,noreferrer");
  }
  if (!usable.length) return <p>Contact the branch for the current price.</p>;
  return <div className={compact ? "price-enquiry price-enquiry--compact" : "price-enquiry"}>
    {!compact && usable.length > 1 ? <select aria-label="Branch for price enquiry" value={code} onChange={(event) => setCode(event.target.value)}>{usable.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select> : null}
    <Button type="button" size="small" onClick={enquire}>Contact for price</Button>
  </div>;
}
