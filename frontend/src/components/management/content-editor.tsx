"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { TextAreaField, ValidationMessage } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { ManagementWebsiteContent } from "@/lib/website-content";

type SaveState = "idle" | "saving" | "saved" | "error";

function groupContent(items: ManagementWebsiteContent[]) {
  return items.reduce<Record<string, Record<string, ManagementWebsiteContent[]>>>(
    (groups, item) => {
      groups[item.page] ??= {};
      groups[item.page][item.section] ??= [];
      groups[item.page][item.section].push(item);
      return groups;
    },
    {},
  );
}

function ContentField({
  initial,
}: {
  initial: ManagementWebsiteContent;
}) {
  const [item, setItem] = useState(initial);
  const [state, setState] = useState<SaveState>("idle");
  const [message, setMessage] = useState("");

  async function save() {
    setState("saving");
    setMessage("");
    try {
      const updated = await apiFetch<ManagementWebsiteContent>(
        `content/management/${item.id}/`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            value: item.value,
            is_published: item.is_published,
          }),
        },
      );
      setItem(updated);
      setState("saved");
      setMessage("Saved. Published changes are now visible on the website.");
    } catch (error) {
      setState("error");
      setMessage(
        error instanceof ApiError
          ? error.message
          : "This content could not be saved. Please try again.",
      );
    }
  }

  return (
    <article className="content-editor__field">
      <TextAreaField
        id={`content-${item.id}`}
        label={item.label}
        value={item.value}
        rows={item.value.length > 100 ? 5 : 3}
        maxLength={5000}
        onChange={(event) => {
          setItem({ ...item, value: event.target.value });
          setState("idle");
          setMessage("");
        }}
        hint={`Approved key: ${item.key}`}
      />
      <div className="content-editor__controls">
        <label className="management-form__toggle">
          <input
            type="checkbox"
            checked={item.is_published}
            onChange={(event) => {
              setItem({ ...item, is_published: event.target.checked });
              setState("idle");
              setMessage("");
            }}
          />
          <span>
            <strong>Published</strong>
            <small>When off, the website uses its reviewed default text.</small>
          </span>
        </label>
        <Button
          size="small"
          onClick={save}
          loading={state === "saving"}
          loadingLabel="Saving..."
        >
          Save field
        </Button>
      </div>
      {message ? (
        state === "error" ? (
          <ValidationMessage>{message}</ValidationMessage>
        ) : (
          <p className="content-editor__success" role="status">{message}</p>
        )
      ) : null}
      {item.updated_by ? (
        <p className="content-editor__audit">
          Last saved by {item.updated_by.full_name} on{" "}
          {new Intl.DateTimeFormat("en-GH", {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(item.updated_at))}
        </p>
      ) : null}
    </article>
  );
}

export function ContentEditor({
  items,
}: {
  items: ManagementWebsiteContent[];
}) {
  const groups = groupContent(items);
  return (
    <div className="content-editor">
      {Object.entries(groups).map(([page, sections]) => (
        <section className="content-editor__page" key={page}>
          <header>
            <p>Website page</p>
            <h2>/{page === "home" ? "" : page}</h2>
          </header>
          {Object.entries(sections).map(([section, fields]) => (
            <div className="content-editor__section" key={section}>
              <h3>{section}</h3>
              <div className="content-editor__grid">
                {fields.map((item) => (
                  <ContentField initial={item} key={item.id} />
                ))}
              </div>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
