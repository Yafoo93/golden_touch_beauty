"use client";

import { Button } from "@/components/ui/button";


export function PrintReceiptButton() {
  return <Button onClick={() => window.print()} aria-label="Print receipt or save it as a PDF">Print / save as PDF</Button>;
}
