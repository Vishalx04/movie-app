"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Bookmark, Check } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { watchlistApi } from "@/lib/api/watchlist";
import { ApiError } from "@/lib/api-error";
import type { WatchlistStatus } from "@/types/watchlist";

export function WatchlistButton({ movieId }: { movieId: number }) {
  const { user, access_token } = useAuth();
  const router = useRouter();

  const [status, setStatus] = useState<WatchlistStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !access_token) {
      setIsLoading(false);
      return;
    }

    watchlistApi
      .getForMovie(movieId, access_token)
      .then((item) => setStatus(item.status))
      .catch((err) => {
        if (!(err instanceof ApiError && err.status === 404)) {
          console.error(err);
        }
      })
      .finally(() => setIsLoading(false));
  }, [movieId, user, access_token]);

  const addToWatchlist = useCallback(async () => {
    if (!access_token) return;

    setStatus("want_to_watch"); // optimistic
    setIsSaving(true);
    setError(null);

    try {
      await watchlistApi.add(movieId, access_token);
    } catch (err) {
      setStatus(null);
      const message = err instanceof ApiError ? err.message : "Couldn't add to watchlist.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }, [movieId, access_token]);

  const markWatched = useCallback(async () => {
    if (!access_token) return;

    const previous = status;
    setStatus("watched"); // optimistic
    setIsSaving(true);
    setError(null);

    try {
      await watchlistApi.updateStatus(movieId, "watched", access_token);
    } catch (err) {
      setStatus(previous);
      const message = err instanceof ApiError ? err.message : "Couldn't update status.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }, [movieId, access_token, status]);

  const removeFromWatchlist = useCallback(async () => {
    if (!access_token) return;

    const previous = status;
    setStatus(null); // optimistic
    setIsSaving(true);
    setError(null);

    try {
      await watchlistApi.remove(movieId, access_token);
    } catch (err) {
      setStatus(previous);
      const message = err instanceof ApiError ? err.message : "Couldn't remove from watchlist.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }, [movieId, access_token, status]);

  if (!user) {
    return (
      <button
        onClick={() => router.push("/login")}
        className="flex items-center gap-2 font-sans text-sm border border-ash/30 rounded-md px-4 py-2 text-ink hover:border-signal"
      >
        <Bookmark className="h-4 w-4" />
        Sign in to save
      </button>
    );
  }

  if (isLoading) {
    return <div className="h-10 w-36 bg-panel rounded-md animate-pulse" />;
  }

  return (
    <div>
      {status === null && (
        <button
          onClick={addToWatchlist}
          disabled={isSaving}
          className="flex items-center gap-2 font-sans text-sm border border-ash/30 rounded-md px-4 py-2 text-ink hover:border-signal disabled:opacity-50"
        >
          <Bookmark className="h-4 w-4" />
          Add to Watchlist
        </button>
      )}

      {status === "want_to_watch" && (
        <div className="flex items-center gap-2">
          <button
            onClick={markWatched}
            disabled={isSaving}
            className="flex items-center gap-2 font-sans text-sm bg-signal text-paper rounded-md px-4 py-2 hover:opacity-90 disabled:opacity-50"
          >
            <Bookmark className="h-4 w-4 fill-current" />
            On Watchlist
          </button>
          <button
            onClick={removeFromWatchlist}
            disabled={isSaving}
            className="font-sans text-xs text-ash hover:text-signal underline disabled:opacity-50"
          >
            Remove
          </button>
        </div>
      )}

      {status === "watched" && (
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 font-sans text-sm text-data border border-data/40 rounded-md px-4 py-2">
            <Check className="h-4 w-4" />
            Watched
          </span>
          <button
            onClick={removeFromWatchlist}
            disabled={isSaving}
            className="font-sans text-xs text-ash hover:text-signal underline disabled:opacity-50"
          >
            Remove
          </button>
        </div>
      )}

      {error && <p className="font-sans text-xs text-signal mt-1">{error}</p>}
    </div>
  );
}