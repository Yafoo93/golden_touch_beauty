"use client";

import { Button } from "@/components/ui/button";


export function PrintReceiptButton() {
  return <Button onClick={() => window.print()}>Print / save as PDF</Button>;
}
