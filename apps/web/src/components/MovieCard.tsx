import Image from "next/image";
import Link from "next/link";
import { Star } from "lucide-react";
import type { MovieListItem } from "@/types/movie";

export function MovieCard({ movie }: { movie: MovieListItem }) {
  const year = movie.released_on ? new Date(movie.released_on).getFullYear() : null;

  return (
    <Link href={`/movies/${movie.id}`} className="group block min-w-0">
      <div className="relative aspect-2/3 overflow-hidden rounded-md bg-panel shadow-sm">
        {movie.poster_url ? (
          <Image
            src={movie.poster_url}
            alt={`${movie.title} poster`}
            fill
            sizes="(max-width: 768px) 45vw, (max-width: 1200px) 22vw, 18vw"
            className="object-cover transition-all duration-500 group-hover:scale-105 group-hover:opacity-75"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center p-6">
            <span className="font-display text-lg text-ash text-center">{movie.title}</span>
          </div>
        )}

        <div className="pointer-events-none absolute inset-0 bg-linear-to-t from-ink/80 via-transparent to-transparent opacity-60" />

        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <span className="rounded bg-signal px-2 py-1 font-sans text-[11px] font-medium text-paper">
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
            <Star className="h-3 w-3 fill-current" />
            {movie.tmdb_vote_average.toFixed(1)}
          </span>
        )}
      </div>
    </Link>
  );
}