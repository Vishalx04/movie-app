import { ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "solid" | "outline" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantStyles: Record<ButtonVariant, string> = {
  solid:
    "bg-ink text-paper hover:bg-ink/90 shadow-raised active:scale-[0.98]",
  outline:
    "bg-panel border border-ash/25 text-ink hover:border-signal hover:text-signal shadow-raised active:scale-[0.98]",
  ghost:
    "bg-transparent text-ash hover:text-signal",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "solid", className = "", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 font-sans text-sm font-medium rounded-lg px-4 py-2.5 transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";