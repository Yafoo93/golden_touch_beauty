"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";
import type { BookingBlock } from "@/lib/management-bookings";

type Options = { branches: { id: string; code: string; name: string }[] };

export function BookingBlockManager() {
  const [blocks, setBlocks] = useState<BookingBlock[]>([]);
  const [options, setOptions] = useState<Options>({ branches: [] });
  const [branch, setBranch] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  async function refresh() {
    const [nextBlocks, nextOptions] = await Promise.all([
      apiFetch<BookingBlock[]>("bookings/management/blocks/"),
      apiFetch<Options>("bookings/management/options/"),
    ]);
    setBlocks(nextBlocks);
    setOptions(nextOptions);
    setBranch((current) => current || nextOptions.branches[0]?.code || "");
  }
  useEffect(() => { void refresh().catch((error) => setMessage(error.message)); }, []);

  async function create() {
    setMessage("");
    try {
      await ensureCsrfCookie();
      await apiFetch("bookings/management/blocks/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ branch_code: branch, starts_at: new Date(startsAt).toISOString(), ends_at: new Date(endsAt).toISOString(), block_type: "unavailable", reason, is_active: true }),
      });
      setStartsAt(""); setEndsAt(""); setReason("");
      await refresh();
      setMessage("Unavailable period added.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Block could not be added."); }
  }

  async function remove(id: string) {
    await ensureCsrfCookie();
    await apiFetch(`bookings/management/blocks/${id}/`, { method: "DELETE" });
    await refresh();
  }

  return <div className="management-blocks">
    <section><h2>Add unavailable time</h2>
      <label>Branch<select value={branch} onChange={(event) => setBranch(event.target.value)}>{options.branches.map((item) => <option value={item.code} key={item.id}>{item.name}</option>)}</select></label>
      <label>Starts<input type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} /></label>
      <label>Ends<input type="datetime-local" value={endsAt} onChange={(event) => setEndsAt(event.target.value)} /></label>
      <label>Reason<input value={reason} onChange={(event) => setReason(event.target.value)} /></label>
      <Button onClick={() => void create()} disabled={!branch || !startsAt || !endsAt || !reason}>Add block</Button>
      {message ? <p>{message}</p> : null}
    </section>
    <section><h2>Current booking blocks</h2>{blocks.map((block) => <article key={block.id}><div><strong>{block.branch_name}</strong><p>{new Date(block.starts_at).toLocaleString()} — {new Date(block.ends_at).toLocaleString()}</p><span>{block.reason}</span></div><Button size="small" variant="outline" onClick={() => void remove(block.id)}>Remove</Button></article>)}</section>
  </div>;
}
