"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { Star, Clock, Calendar, Globe, DollarSign } from "lucide-react";
import { movieApi } from "@/lib/api/movies";
import { RatingWidget } from "@/components/RatingWidget";
import { WatchlistButton } from "@/components/WatchlistButton";
import { BackButton } from "@/components/BackButton";
import type { MovieDetail } from "@/types/movie";
import { ApiError } from "@/lib/api-error";

function formatRuntime(minutes: number | null): string | null {
  if (!minutes) return null;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

function formatDate(dateStr: string | null): string | null {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function MovieDetailPage() {
  const params = useParams();
  const movieId = Number(params.id);

  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!movieId || Number.isNaN(movieId)) {
      setError("Invalid movie.");
      setIsLoading(false);
      return;
    }

    movieApi
      .getById(movieId)
      .then(setMovie)
      .catch((err) => {
        const message =
          err instanceof ApiError && err.status === 404
            ? "This movie couldn't be found."
            : "Couldn't load this movie. Please try again.";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, [movieId]);

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 w-full">
        <div className="h-56 md:h-96 rounded-xl skeleton mb-10" />
        <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-10">
          <div className="aspect-2/3 rounded-xl skeleton" />
          <div className="space-y-4 pt-4">
            <div className="h-10 w-3/4 rounded skeleton" />
            <div className="h-4 w-1/2 rounded skeleton" />
            <div className="h-4 w-1/3 rounded skeleton" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-24 text-center w-full">
        <div className="mb-6 text-left">
          <BackButton />
        </div>
        <h1 className="font-display text-2xl text-ink mb-2">{error ?? "Movie not found."}</h1>
        <p className="font-sans text-sm text-ash">Try heading back and picking another film.</p>
      </div>
    );
  }

  const year = movie.released_on ? new Date(movie.released_on).getFullYear() : null;
  const runtime = formatRuntime(movie.runtime);
  const releaseDate = formatDate(movie.released_on);

  return (
    <div className="animate-fade-in">
      <div className="relative w-full h-[42vh] min-h-72 max-h-130 bg-ink overflow-hidden">
        {movie.backdrop_url ? (
          <>
            <Image
              src={movie.backdrop_url}
              alt=""
              fill
              priority
              className="object-cover opacity-55"
            />
            <div className="absolute inset-0 bg-linear-to-t from-paper via-ink/25 to-ink/50" />
          </>
        ) : (
          <div className="absolute inset-0 bg-linear-to-b from-ink to-ink/80" />
        )}

        <div className="absolute top-5 left-5 md:top-6 md:left-10">
          <div className="inline-flex bg-panel/85 backdrop-blur-sm rounded-full shadow-card">
            <BackButton />
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-5 md:px-10 -mt-28 md:-mt-36 relative">
        <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-8 md:gap-10">
          <div className="relative aspect-2/3 w-40 sm:w-56 md:w-full rounded-xl overflow-hidden bg-panel shadow-card-hover mx-auto md:mx-0 ring-1 ring-ink/5">
            {movie.poster_url ? (
              <Image
                src={movie.poster_url}
                alt={movie.title}
                fill
                sizes="(min-width: 768px) 260px, 224px"
                className="object-cover"
                priority
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center p-6">
                <span className="font-display text-lg text-ash text-center">{movie.title}</span>
              </div>
            )}
          </div>

          <div className="pt-2 md:pt-24 text-center md:text-left">
            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl text-ink leading-[1.05] tracking-[-0.02em]">
              {movie.title}
            </h1>

            {movie.tagline && (
              <p className="font-sans italic text-ash text-lg mt-3">{movie.tagline}</p>
            )}

            <p className="font-mono text-sm text-ash mt-5">
              {[year, runtime, movie.status].filter(Boolean).join("  ·  ")}
            </p>

            {movie.tmdb_vote_average != null && (
              <div className="flex items-center justify-center md:justify-start gap-1.5 mt-4 font-mono text-base text-signal">
                <Star className="h-5 w-5 fill-current" />
                {movie.tmdb_vote_average.toFixed(1)}
                {movie.tmdb_vote_count != null && (
                  <span className="text-ash text-sm ml-1">
                    ({movie.tmdb_vote_count.toLocaleString()} votes)
                  </span>
                )}
              </div>
            )}

            {movie.genres.length > 0 && (
              <div className="flex flex-wrap justify-center md:justify-start gap-2 mt-5">
                {movie.genres.map((genre) => (
                  <span
                    key={genre.id}
                    className="font-sans text-xs text-ink bg-panel shadow-card px-3 py-1.5 rounded-full"
                  >
                    {genre.name}
                  </span>
                ))}
              </div>
            )}

            <div className="flex flex-wrap items-center justify-center md:justify-start gap-6 mt-8">
              <RatingWidget movieId={movie.id} />
              <WatchlistButton movieId={movie.id} />
            </div>
          </div>
        </div>

        {movie.description && (
          <div className="max-w-3xl mt-14 pt-10 border-t border-ash/15">
            <h2 className="font-display text-xl text-ink mb-4">Overview</h2>
            <p className="font-sans text-ink/80 leading-relaxed text-base">
              {movie.description}
            </p>
          </div>
        )}

        <div className="max-w-3xl mt-10 pb-16 flex flex-wrap gap-x-10 gap-y-3 font-mono text-xs text-ash">
          {releaseDate && (
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" /> Released {releaseDate}
            </span>
          )}
          {movie.original_language && (
            <span className="inline-flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5" /> {movie.original_language.toUpperCase()}
            </span>
          )}
          {runtime && (
            <span className="inline-flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" /> {runtime}
            </span>
          )}
          {movie.budget ? (
            <span className="inline-flex items-center gap-1.5">
              <DollarSign className="h-3.5 w-3.5" /> Budget ${movie.budget.toLocaleString()}
            </span>
          ) : null}
          {movie.revenue ? (
            <span className="inline-flex items-center gap-1.5">
              <DollarSign className="h-3.5 w-3.5" /> Revenue ${movie.revenue.toLocaleString()}
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}