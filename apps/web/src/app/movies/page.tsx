"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { movieApi } from "@/lib/api/movies";
import { MovieCard } from "@/components/MovieCard";
import type { MovieListItem } from "@/types/movie";
import type { Genre } from "@/types/genre";
import { ApiError } from "@/lib/api-error";
import { genreApi } from "@/lib/api/genre";

const PAGE_SIZE = 20;

export default function MoviesPage() {
  const [movies, setMovies] = useState<MovieListItem[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [query, setQuery] = useState("");
  const [selectedGenreId, setSelectedGenreId] = useState<number | undefined>(undefined);

  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const generationRef = useRef(0);
  const skipRef = useRef(0);
  const hasMoreRef = useRef(true);
  const isLoadingMoreRef = useRef(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    genreApi.list().then(setGenres).catch(() => {});
  }, []);

  const loadFirstPage = useCallback(async (q: string, genreId: number | undefined) => {
    const myGeneration = ++generationRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const results = await movieApi.list({ q: q || undefined, genre_id: genreId, skip: 0, limit: PAGE_SIZE });
      if (myGeneration !== generationRef.current) return;

      setMovies(results);
      const more = results.length === PAGE_SIZE;
      hasMoreRef.current = more;
      setHasMore(more);
      skipRef.current = results.length;
      setIsLoading(false);
    } catch (err) {
      if (myGeneration !== generationRef.current) return;
      const message = err instanceof ApiError ? err.message : "Couldn't load movies. Please try again.";
      setError(message);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => loadFirstPage(query, selectedGenreId), 300);
    return () => clearTimeout(timeout);
  }, [query, selectedGenreId, loadFirstPage]);

  const loadMore = useCallback(async () => {
    if (isLoadingMoreRef.current || !hasMoreRef.current) return;

    const myGeneration = generationRef.current;
    isLoadingMoreRef.current = true;
    setIsLoadingMore(true);

    try {
      const results = await movieApi.list({
        q: query || undefined,
        genre_id: selectedGenreId,
        skip: skipRef.current,
        limit: PAGE_SIZE,
      });

      if (myGeneration !== generationRef.current) return;

      setMovies((prev) => [...prev, ...results]);
      const more = results.length === PAGE_SIZE;
      hasMoreRef.current = more;
      setHasMore(more);
      skipRef.current += results.length;
    } catch {
      if (myGeneration === generationRef.current) {
        hasMoreRef.current = false;
        setHasMore(false);
      }
    } finally {
      isLoadingMoreRef.current = false;
      setIsLoadingMore(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, selectedGenreId]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore();
      },
      { rootMargin: "600px" }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  const clearSearch = () => setQuery("");

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="max-w-7xl mx-auto px-5 md:px-10">
        <section className="pt-14 pb-16 md:pt-20 md:pb-20">
          <div className="max-w-3xl">
            <p className="font-sans text-xs uppercase tracking-[0.22em] text-signal mb-5">
              Your next favorite film
            </p>
            <h1 className="font-display text-5xl md:text-7xl leading-[0.95] tracking-[-0.04em] text-ink">
              Stories worth
              <br />
              <span className="text-ash">staying for.</span>
            </h1>
            <p className="mt-7 max-w-xl font-sans text-base md:text-lg leading-7 text-ash">
              Explore movies from every genre, era and mood. Find something worth watching tonight.
            </p>
          </div>
        </section>

        <section className="border-y border-ash/20">
          <div className="py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative w-full sm:max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ash" />
              <input
                type="text"
                placeholder="Search films..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full h-10 rounded-md border border-ash/25 bg-panel pl-10 pr-9 font-sans text-sm text-ink outline-none placeholder:text-ash focus:border-signal transition-colors"
              />
              {query && (
                <button
                  onClick={clearSearch}
                  aria-label="Clear search"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ash hover:text-ink transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-3">
              <SlidersHorizontal className="h-4 w-4 text-ash" />
              <select
                value={selectedGenreId ?? ""}
                onChange={(e) => setSelectedGenreId(e.target.value ? Number(e.target.value) : undefined)}
                className="h-10 min-w-44 rounded-md border border-ash/25 bg-panel px-3 font-sans text-sm text-ink outline-none focus:border-signal"
              >
                <option value="">All genres</option>
                {genres.map((genre) => (
                  <option key={genre.id} value={genre.id}>{genre.name}</option>
                ))}
              </select>
              {/* <span className="hidden sm:inline font-mono text-xs text-ash whitespace-nowrap">
                {movies.length} films
              </span> */}
            </div>
          </div>
        </section>

        {error && (
          <div className="py-5">
            <p className="font-sans text-sm text-signal">{error}</p>
          </div>
        )}

        {isLoading && movies.length === 0 ? (
          <div className="py-20">
            <p className="font-sans text-sm text-ash">Finding movies...</p>
          </div>
        ) : movies.length === 0 ? (
          <div className="py-24 text-center">
            <h2 className="font-display text-2xl text-ink mb-2">No films found.</h2>
            <p className="font-sans text-sm text-ash">Try another search or genre.</p>
          </div>
        ) : (
          <section className={`transition-opacity ${isLoading ? "opacity-50" : "opacity-100"}`}>
            <div className="flex items-end justify-between pt-10 pb-7">
              <div>
                <p className="font-sans text-xs uppercase tracking-[0.16em] text-ash mb-2">
                  {query ? "Search results" : "Browse"}
                </p>
                <h2 className="font-display text-2xl md:text-3xl text-ink">
                  {query ? `"${query}"` : "All films"}
                </h2>
              </div>
              <span className="font-mono text-xs text-ash">
                {movies.length} {movies.length === 1 ? "film" : "films"}
              </span>
            </div>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-x-5 gap-y-12 md:gap-x-7 md:gap-y-14">
              {movies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>

            <div ref={sentinelRef} className="flex min-h-28 items-center justify-center">
              {isLoadingMore && (
                <div className="flex items-center gap-3">
                  <div className="h-4 w-4 rounded-full border-2 border-ash/30 border-t-ink animate-spin" />
                  <span className="font-sans text-xs text-ash">Loading more films...</span>
                </div>
              )}
            </div>

            {!hasMore && (
              <div className="py-16 text-center">
                <div className="w-8 h-px bg-ash/30 mx-auto mb-5" />
                <p className="font-sans text-xs text-ash">You&apos;ve reached the end.</p>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}