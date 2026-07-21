import Link from "next/link";
import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from "react";


export type ButtonVariant = "gold" | "black" | "outline";
export type ButtonSize = "small" | "medium" | "large";

type SharedButtonProps = {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  className?: string;
};

function buttonClassName({
  variant = "gold",
  size = "medium",
  fullWidth = false,
  className,
}: Omit<SharedButtonProps, "children">) {
  return [
    "button",
    `button--${variant}`,
    `button--${size}`,
    fullWidth ? "button--full-width" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");
}

export type ButtonProps = SharedButtonProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    loading?: boolean;
    loadingLabel?: string;
  };

export function Button({
  children,
  variant = "gold",
  size = "medium",
  fullWidth = false,
  loading = false,
  loadingLabel = "Please wait",
  className,
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      className={buttonClassName({ variant, size, fullWidth, className })}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading ? <span className="button__spinner" aria-hidden="true" /> : null}
      <span>{loading ? loadingLabel : children}</span>
    </button>
  );
}

export type ButtonLinkProps = SharedButtonProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
    href: string;
  };

export function ButtonLink({
  children,
  href,
  variant = "gold",
  size = "medium",
  fullWidth = false,
  className,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      {...props}
      href={href}
      className={buttonClassName({ variant, size, fullWidth, className })}
    >
      <span>{children}</span>
    </Link>
  );
}
