import Link from "next/link";
import { Star, Bookmark, Compass } from "lucide-react";
import { Button } from "@/components/Button";

const pillars = [
  {
    icon: Star,
    title: "Rate",
    copy: "Score every film you finish and build a taste profile that's actually yours.",
  },
  {
    icon: Bookmark,
    title: "Track",
    copy: "Keep a running watchlist so nothing you meant to see slips through the cracks.",
  },
  {
    icon: Compass,
    title: "Discover",
    copy: "Surface films picked to match what you've already loved, not just what's trending.",
  },
];

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-5 md:px-10 w-full">
      <section className="py-24 md:py-36 grid md:grid-cols-[1.3fr_1fr] gap-12 items-end">
        <div className="animate-fade-in-up">
          <p className="font-sans text-xs uppercase tracking-[0.22em] text-signal mb-5">
            Your next favorite film
          </p>
          <h1 className="font-display text-5xl md:text-7xl leading-[0.95] tracking-[-0.03em] text-ink max-w-2xl">
            Stories worth
            <br />
            <span className="text-ash">staying for.</span>
          </h1>
          <p className="mt-7 max-w-lg font-sans text-base md:text-lg leading-7 text-ash">
            Rate what you&apos;ve seen, track what you want to watch, and discover
            films picked for your taste.
          </p>
          <div className="mt-9">
            <Link href="/movies">
              <Button variant="solid" className="text-base px-6 py-3">
                Browse films
              </Button>
            </Link>
          </div>
        </div>

        {/* Signature: a stacked, tilted "ticket stub" — nods to a real cinema artifact rather than a generic stat card */}
        <div
          className="hidden md:flex justify-end animate-fade-in-up"
          style={{ animationDelay: "120ms" }}
          aria-hidden="true"
        >
          <div className="relative w-56 rotate-3 rounded-xl bg-panel shadow-card-hover border border-ash/10 px-5 py-6">
            <div className="absolute -left-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-paper border border-ash/15" />
            <div className="absolute -right-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-paper border border-ash/15" />
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-ash">
              Admit one
            </p>
            <p className="font-display text-xl text-ink mt-2 leading-tight">
              Tonight&apos;s
              <br />
              screening
            </p>
            <div className="mt-5 border-t border-dashed border-ash/25 pt-3 flex items-center gap-1.5 font-mono text-sm text-signal">
              <Star className="h-4 w-4 fill-current" />
              your pick
            </div>
          </div>
        </div>
      </section>

      <section className="pb-24 md:pb-32 grid sm:grid-cols-3 gap-6 md:gap-8 border-t border-ash/15 pt-14">
        {pillars.map(({ icon: Icon, title, copy }, i) => (
          <div
            key={title}
            className="animate-fade-in-up"
            style={{ animationDelay: `${i * 90}ms` }}
          >
            <Icon className="h-5 w-5 text-signal" strokeWidth={1.75} />
            <h2 className="font-display text-xl text-ink mt-4">{title}</h2>
            <p className="font-sans text-sm text-ash leading-6 mt-2">{copy}</p>
          </div>
        ))}
      </section>
    </div>
  );
}