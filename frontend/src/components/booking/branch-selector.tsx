"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { formatBranchTime, formatOpeningDays } from "@/lib/branch-formatters";
import type { PublicBranch } from "@/lib/branches";

export function BranchSelector({
  branches,
  initialBranchCode,
}: {
  branches: PublicBranch[];
  initialBranchCode?: string;
}) {
  const validInitialCode = branches.some(
    (branch) => branch.code === initialBranchCode,
  )
    ? initialBranchCode
    : undefined;
  const [selectedCode, setSelectedCode] = useState(validInitialCode ?? "");
  const [isNavigating, startTransition] = useTransition();
  const router = useRouter();
  const searchParams = useSearchParams();

  function selectBranch(code: string) {
    setSelectedCode(code);
    const params = new URLSearchParams(searchParams.toString());
    params.set("step", "branch");
    params.set("branch", code);
    startTransition(() => router.replace(`/book?${params.toString()}`, { scroll: false }));
  }

  function continueToServices() {
    if (!selectedCode) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set("step", "service");
    params.set("branch", selectedCode);
    startTransition(() => router.push(`/book?${params.toString()}`));
  }

  return (
    <div className="branch-selector">
      <fieldset>
        <legend>Choose your preferred branch</legend>
        <p className="branch-selector__help">
          Available services and appointment times will be based on this branch.
        </p>
        <div className="branch-selector__options">
          {branches.map((branch) => {
            const isSelected = branch.code === selectedCode;
            return (
              <label
                className="branch-option"
                data-selected={isSelected || undefined}
                key={branch.id}
              >
                <input
                  type="radio"
                  name="branch"
                  value={branch.code}
                  checked={isSelected}
                  onChange={() => selectBranch(branch.code)}
                />
                <span className="branch-option__check" aria-hidden="true" />
                <span className="branch-option__content">
                  <strong>{branch.name}</strong>
                  <span>{branch.address}</span>
                  <span>
                    {formatOpeningDays(branch.opening_days)}, {formatBranchTime(branch.opening_time)} - {formatBranchTime(branch.closing_time)}
                  </span>
                  <span>{branch.telephone_number}</span>
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <div className="branch-selector__footer">
        {isNavigating ? (
          <LoadingIndicator label="Updating your branch" size="small" />
        ) : (
          <span>
            {selectedCode
              ? `${branches.find((branch) => branch.code === selectedCode)?.name} selected`
              : "Select a branch to continue"}
          </span>
        )}
        <Button
          onClick={continueToServices}
          disabled={!selectedCode || isNavigating}
          loading={isNavigating}
          loadingLabel="Continuing"
        >
          Continue to services
        </Button>
      </div>
    </div>
  );
}
