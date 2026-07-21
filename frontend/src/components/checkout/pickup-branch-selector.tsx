"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { PublicBranch } from "@/lib/branches";


export type PickupBranchOption = {
  branch: PublicBranch;
  eligible: boolean;
  unavailable_items: Array<{
    variant_id: string;
    sku: string;
    name: string;
    reason: string;
  }>;
};

export function PickupBranchSelector({
  options,
  initialBranchCode,
}: {
  options: PickupBranchOption[];
  initialBranchCode?: string;
}) {
  const validInitial = options.some(
    (option) =>
      option.eligible && option.branch.code === initialBranchCode,
  )
    ? initialBranchCode
    : "";
  const [selectedCode, setSelectedCode] = useState(validInitial ?? "");
  const router = useRouter();
  const searchParams = useSearchParams();

  function selectBranch(code: string) {
    setSelectedCode(code);
    const params = new URLSearchParams(searchParams.toString());
    params.set("fulfillment", "pickup");
    params.set("pickup_branch", code);
    router.replace(`/checkout?${params.toString()}`, { scroll: false });
  }

  function continueCheckout() {
    if (!selectedCode) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set("fulfillment", "pickup");
    params.set("pickup_branch", selectedCode);
    params.set("step", "details");
    router.push(`/checkout?${params.toString()}`);
  }

  return (
    <div className="pickup-selector">
      <fieldset>
        <legend>Choose your pickup branch</legend>
        <p className="pickup-selector__help">
          A branch is selectable only when it can fulfil every item in your basket.
        </p>
        <div className="pickup-selector__options">
          {options.map(({ branch, eligible, unavailable_items }) => {
            const selected = branch.code === selectedCode;
            const reason = unavailable_items[0]?.reason;
            return (
              <label
                className="pickup-option"
                data-selected={selected || undefined}
                data-unavailable={!eligible || undefined}
                key={branch.id}
              >
                <input
                  type="radio"
                  name="pickup_branch"
                  value={branch.code}
                  checked={selected}
                  disabled={!eligible}
                  onChange={() => selectBranch(branch.code)}
                />
                <span className="pickup-option__marker" aria-hidden="true" />
                <span className="pickup-option__content">
                  <span className="pickup-option__title">
                    <strong>{branch.name}</strong>
                    <span className={eligible ? "pickup-status pickup-status--ready" : "pickup-status pickup-status--unavailable"}>
                      {eligible ? "Available" : "Unavailable"}
                    </span>
                  </span>
                  <span>{branch.address}</span>
                  <span>{branch.telephone_number}</span>
                  {!eligible ? <span className="pickup-option__reason">{reason}</span> : null}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>
      <div className="pickup-selector__footer">
        <span>{selectedCode ? `${options.find((option) => option.branch.code === selectedCode)?.branch.name} selected for pickup` : "Select an available pickup branch"}</span>
        <Button disabled={!selectedCode} onClick={continueCheckout}>Continue checkout</Button>
      </div>
    </div>
  );
}
