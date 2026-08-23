export type WatchlistStatus = "want_to_watch" | "watched" | "abandoned";

export interface WatchlistItem {
  id: number;
  movie_id: number;
  status: WatchlistStatus;
  added_at: string;
  watched_at: string | null;
}