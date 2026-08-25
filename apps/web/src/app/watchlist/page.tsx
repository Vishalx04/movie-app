"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bookmark, Trash2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { MovieCard } from "@/components/MovieCard";
import { watchlistApi } from "@/lib/api/watchlist";
import { ApiError } from "@/lib/api-error";
import type { WatchlistItem, WatchlistStatus } from "@/types/watchlist";

type StatusFilter = "all" | WatchlistStatus;

const filters: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "want_to_watch", label: "Want to watch" },
  { value: "watched", label: "Watched" },
  { value: "abandoned", label: "Abandoned" },
];

export default function WatchlistPage() {
  const { user, access_token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingMovieId, setSavingMovieId] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.replace("/login");
    }
  }, [isAuthLoading, user, router]);

  useEffect(() => {
    if (isAuthLoading || !user || !access_token) return;

    let cancelled = false;
    watchlistApi
      .list(access_token, filter === "all" ? undefined : filter)
      .then((results) => {
        if (!cancelled) setItems(results);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Couldn't load your watchlist.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isAuthLoading, user, access_token, filter]);

  async function updateStatus(movieId: number, status: WatchlistStatus) {
    if (!access_token) return;

    setSavingMovieId(movieId);
    try {
      const updated = await watchlistApi.updateStatus(movieId, status, access_token);
      setItems((current) =>
        current.map((item) =>
          item.movie_id === movieId
            ? { ...item, status: updated.status, watched_at: updated.watched_at }
            : item,
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update this film.");
    } finally {
      setSavingMovieId(null);
    }
  }

  async function removeMovie(movieId: number) {
    if (!access_token) return;

    setSavingMovieId(movieId);
    try {
      await watchlistApi.remove(movieId, access_token);
      setItems((current) => current.filter((item) => item.movie_id !== movieId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't remove this film.");
    } finally {
      setSavingMovieId(null);
    }
  }

  if (isAuthLoading || !user) {
    return <main className="min-h-screen bg-paper" />;
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="max-w-7xl mx-auto px-5 md:px-10 py-14 md:py-20">
        <p className="font-sans text-xs uppercase tracking-[0.22em] text-signal mb-5">
          Your collection
        </p>
        <h1 className="font-display text-4xl md:text-6xl tracking-[-0.03em]">My watchlist</h1>
        <p className="mt-4 max-w-xl font-sans text-base text-ash leading-7">
          Keep track of the stories you want to return to.
        </p>

        <div className="mt-10 flex flex-wrap gap-2 border-b border-ash/15 pb-5">
          {filters.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setFilter(value);
                setIsLoading(true);
                setError(null);
              }}
              className={`rounded-full px-4 py-2 font-sans text-sm transition-colors ${
                filter === value
                  ? "bg-signal text-paper"
                  : "border border-ash/25 text-ash hover:border-signal hover:text-ink"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {error && <p className="mt-6 font-sans text-sm text-signal">{error}</p>}

        {isLoading ? (
          <div className="mt-10 grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-x-5 gap-y-12 md:gap-x-7">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="space-y-3">
                <div className="aspect-2/3 rounded-xl skeleton" />
                <div className="h-4 w-4/5 rounded skeleton" />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <section className="py-24 text-center">
            <Bookmark className="h-8 w-8 text-ash/50 mx-auto mb-4" strokeWidth={1.5} />
            <h2 className="font-display text-2xl">Nothing here yet.</h2>
            <p className="mt-2 font-sans text-sm text-ash">
              Save films from their detail page to build your watchlist.
            </p>
            <button
              type="button"
              onClick={() => router.push("/movies")}
              className="mt-6 font-sans text-sm text-signal hover:text-signal-hover"
            >
              Browse films
            </button>
          </section>
        ) : (
          <section className="mt-10 grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-x-5 gap-y-12 md:gap-x-7 md:gap-y-14">
            {items.map((item) => (
              <div key={item.id} className="min-w-0">
                <MovieCard movie={item.movie} />
                <div className="mt-3 flex items-center gap-2">
                  <select
                    aria-label={`Status for ${item.movie.title}`}
                    value={item.status}
                    disabled={savingMovieId === item.movie_id}
                    onChange={(event) =>
                      updateStatus(item.movie_id, event.target.value as WatchlistStatus)
                    }
                    className="min-w-0 flex-1 rounded-md border border-ash/25 bg-panel px-2 py-2 font-sans text-xs text-ink outline-none focus:border-signal disabled:opacity-50"
                  >
                    <option value="want_to_watch">Want to watch</option>
                    <option value="watched">Watched</option>
                    <option value="abandoned">Abandoned</option>
                  </select>
                  <button
                    type="button"
                    aria-label={`Remove ${item.movie.title} from watchlist`}
                    disabled={savingMovieId === item.movie_id}
                    onClick={() => removeMovie(item.movie_id)}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-ash hover:bg-signal/10 hover:text-signal disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
