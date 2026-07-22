import type { PublicBranch } from "@/lib/branches";

export type BranchManager = { id: string; full_name: string; email: string };
export type BranchManagerOption = BranchManager;
export type ManagementBranch = PublicBranch & {
  assigned_manager: BranchManager | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
