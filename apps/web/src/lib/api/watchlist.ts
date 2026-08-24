import type { WatchlistItem, WatchlistStatus } from "@/types/watchlist";
import { apifetch } from "../api-client";

export const watchlistApi = {
  add: (movieId: number, accessToken: string) =>
    apifetch<WatchlistItem>(
      "/watchlist/",
      { method: "POST", body: JSON.stringify({ movie_id: movieId }) },
      accessToken
    ),

  getForMovie: (movieId: number, accessToken: string) =>
    apifetch<WatchlistItem>(`/watchlist/movie/${movieId}`, {}, accessToken),

  updateStatus: (movieId: number, status: WatchlistStatus, accessToken: string) =>
    apifetch<WatchlistItem>(
      `/watchlist/movie/${movieId}`,
      { method: "PATCH", body: JSON.stringify({ status }) },
      accessToken
    ),

  remove: (movieId: number, accessToken: string) =>
    apifetch<void>(`/watchlist/movie/${movieId}`, { method: "DELETE" }, accessToken),
};