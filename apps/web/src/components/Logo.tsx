import Link from "next/link";

export function Logo() {
  return (
    <Link
      href="/"
      className="font-display italic text-xl text-ink tracking-tight"
    >
      movie<span className="text-signal not-italic">—</span>app
    </Link>
  );
}