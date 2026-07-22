import type { Metadata } from "next";
import { BranchCreateForm } from "@/components/management/branch-create-form";

export const metadata: Metadata = { title: "Create Branch" };

export default function NewBranchPage() {
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header">
        <div>
          <p>Management · Locations</p>
          <h1>Create a branch</h1>
          <span>Add a Golden Touch location and its operational contact information.</span>
        </div>
      </header>
      <BranchCreateForm />
    </main>
  );
}
