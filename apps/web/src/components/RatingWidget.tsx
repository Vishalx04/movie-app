"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Star, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ratingApi } from "@/lib/api/ratings";
import { ApiError } from "@/lib/api-error";

export function RatingWidget({ movieId }: { movieId: number }) {
  const { user, access_token } = useAuth();
  const router = useRouter();

  const [rating, setRating] = useState<number | null>(null);
  const [hoverValue, setHoverValue] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !access_token) {
      setIsLoading(false);
      return;
    }

    ratingApi
      .getForMovie(movieId, access_token)
      .then((r) => setRating(r.rating))
      .catch((err) => {
        // A 404 just means "you haven't rated this yet" — not a real error.
        if (!(err instanceof ApiError && err.status === 404)) {
          console.error(err);
        }
      })
      .finally(() => setIsLoading(false));
  }, [movieId, user, access_token]);

  const submitRating = useCallback(
    async (value: number) => {
      if (!access_token) return;

      const previous = rating;
      setRating(value); // optimistic
      setIsSaving(true);
      setError(null);

      try {
        await ratingApi.rate(movieId, value, access_token);
      } catch (err) {
        setRating(previous); // roll back on failure
        const message = err instanceof ApiError ? err.message : "Couldn't save your rating.";
        setError(message);
      } finally {
        setIsSaving(false);
      }
    },
    [movieId, access_token, rating]
  );

  const clearRating = useCallback(async () => {
    if (!access_token) return;

    const previous = rating;
    setRating(null);
    setIsSaving(true);
    setError(null);

    try {
      await ratingApi.remove(movieId, access_token);
    } catch (err) {
      setRating(previous);
      const message = err instanceof ApiError ? err.message : "Couldn't remove your rating.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }, [movieId, access_token, rating]);

  function handleStarClick(starIndex: number, event: React.MouseEvent<HTMLButtonElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const clickedLeftHalf = event.clientX - rect.left < rect.width / 2;
    const value = starIndex + (clickedLeftHalf ? 0.5 : 1);
    submitRating(value);
  }

  function handleStarHover(starIndex: number, event: React.MouseEvent<HTMLButtonElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const hoveredLeftHalf = event.clientX - rect.left < rect.width / 2;
    setHoverValue(starIndex + (hoveredLeftHalf ? 0.5 : 1));
  }

  if (!user) {
    return (
      <button
        onClick={() => router.push("/login")}
        className="font-sans text-sm text-ash hover:text-signal underline"
      >
        Sign in to rate this movie
      </button>
    );
  }

  if (isLoading) {
    return <div className="h-8 w-40 bg-panel rounded animate-pulse" />;
  }

  const displayValue = hoverValue ?? rating ?? 0;

  return (
    <div>
      <div className="flex items-center gap-1" onMouseLeave={() => setHoverValue(null)}>
        {[0, 1, 2, 3, 4].map((starIndex) => {
          const fillAmount = Math.max(0, Math.min(1, displayValue - starIndex));

          return (
            <button
              key={starIndex}
              type="button"
              disabled={isSaving}
              onClick={(e) => handleStarClick(starIndex, e)}
              onMouseMove={(e) => handleStarHover(starIndex, e)}
              className="relative disabled:opacity-50"
              aria-label={`Rate ${starIndex + 1} stars`}
            >
              <Star className="h-7 w-7 text-ash/40" />
              <div
                className="absolute inset-0 overflow-hidden"
                style={{ width: `${fillAmount * 100}%` }}
              >
                <Star className="h-7 w-7 fill-signal text-signal" />
              </div>
            </button>
          );
        })}

        {rating !== null && (
          <button
            onClick={clearRating}
            disabled={isSaving}
            aria-label="Clear rating"
            className="ml-2 text-ash hover:text-signal disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {rating !== null && (
          <span className="ml-1 font-mono text-sm text-ash">{rating.toFixed(1)}</span>
        )}
      </div>

      {error && <p className="font-sans text-xs text-signal mt-1">{error}</p>}
    </div>
  );
}