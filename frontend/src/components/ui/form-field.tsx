import { useId, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";

type FieldShellProps = { id: string; label: string; required?: boolean; hint?: string; error?: string; children: ReactNode };

function FieldShell({ id, label, required, hint, error, children }: FieldShellProps) {
  return <div className="form-field"><label className="form-field__label" htmlFor={id}>{label}{required ? <span aria-hidden="true"> *</span> : null}</label>{children}{error ? <ValidationMessage id={`${id}-error`}>{error}</ValidationMessage> : hint ? <p className="form-field__hint" id={`${id}-hint`}>{hint}</p> : null}</div>;
}

function describedBy(id: string, error?: string, hint?: string) { return error ? `${id}-error` : hint ? `${id}-hint` : undefined; }

export type FormFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & { id?: string; label: string; hint?: string; error?: string };

export function FormField({ id: providedId, label, hint, error, required, className, ...props }: FormFieldProps) {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  return <FieldShell id={id} label={label} hint={hint} error={error} required={required}><input {...props} id={id} required={required} className={["form-field__control", className].filter(Boolean).join(" ")} aria-invalid={error ? true : undefined} aria-describedby={describedBy(id, error, hint)} /></FieldShell>;
}

export type TextAreaFieldProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> & { id?: string; label: string; hint?: string; error?: string };

export function TextAreaField({ id: providedId, label, hint, error, required, className, ...props }: TextAreaFieldProps) {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  return <FieldShell id={id} label={label} hint={hint} error={error} required={required}><textarea {...props} id={id} required={required} className={["form-field__control", className].filter(Boolean).join(" ")} aria-invalid={error ? true : undefined} aria-describedby={describedBy(id, error, hint)} /></FieldShell>;
}

export function ValidationMessage({ id, children }: { id?: string; children: ReactNode }) {
  return <p className="validation-message" id={id} role="alert"><span aria-hidden="true">!</span>{children}</p>;
}

export function ValidationSummary({ title = "Please correct the following:", errors }: { title?: string; errors: string[] }) {
  if (errors.length === 0) return null;
  return <section className="validation-summary" role="alert" tabIndex={-1}><h2>{title}</h2><ul>{errors.map((error) => <li key={error}>{error}</li>)}</ul></section>;
}
