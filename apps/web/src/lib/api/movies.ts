import type { MovieListItem, MovieDetail, MovieListParams } from "@/types/movie";
import { apifetch } from "../api-client";

function buildQueryString(params: MovieListParams): string {
  const searchParams = new URLSearchParams();

  if (params.q) searchParams.set("q", params.q);
  if (params.genre_id !== undefined) searchParams.set("genre_id", String(params.genre_id));
  if (params.skip !== undefined) searchParams.set("skip", String(params.skip));
  if (params.limit !== undefined) searchParams.set("limit", String(params.limit));

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export const movieApi = {
  list: (params: MovieListParams = {}, signal?: AbortSignal) =>
    apifetch<MovieListItem[]>(`/movies/${buildQueryString(params)}`, { signal }),

  getById: (id: number) => apifetch<MovieDetail>(`/movies/${id}`),
};