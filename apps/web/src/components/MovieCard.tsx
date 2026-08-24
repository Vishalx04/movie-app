import Image from "next/image";
import Link from "next/link";
import type { MovieListItem } from "@/types/movie";

export function MovieCard({ movie }: { movie: MovieListItem }) {
  const year = movie.released_on ? new Date(movie.released_on).getFullYear() : null;

  return (
    <Link href={`/movies/${movie.id}`} className="group block min-w-0">
      <div className="relative aspect-2/3 overflow-hidden rounded-xl bg-panel shadow-card group-hover:shadow-card-hover transition-shadow duration-300">
        {movie.poster_url ? (
          <Image
            src={movie.poster_url}
            alt={`${movie.title} poster`}
            fill
            sizes="(max-width: 768px) 45vw, (max-width: 1200px) 22vw, 18vw"
            className="object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center p-6">
            <span className="font-display text-lg text-ash text-center">{movie.title}</span>
          </div>
        )}

        <div className="pointer-events-none absolute inset-0 bg-linear-to-t from-ink/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <span className="rounded-full bg-signal px-3 py-1 font-sans text-[11px] font-medium text-paper">
            View film
          </span>
        </div>
      </div>

      <div className="pt-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display text-base md:text-lg leading-tight text-ink truncate group-hover:text-signal transition-colors">
            {movie.title}
          </h3>
          <p className="mt-1.5 font-mono text-xs text-ash">{year ?? "—"}</p>
        </div>

        {movie.tmdb_vote_average != null && (
          <span className="flex shrink-0 items-center gap-1 font-mono text-xs font-medium text-signal">
            {movie.tmdb_vote_average.toFixed(1)}
          </span>
        )}
      </div>
    </Link>
  );
}