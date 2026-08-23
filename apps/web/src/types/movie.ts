import { Genre } from "./genre";

export interface MovieListItem {
  id: number;
  tmdb_id: string;
  title: string;
  poster_url: string | null;
  released_on: string | null;
  tmdb_vote_average: number | null;
}

export interface MovieDetail {
  id: number;
  tmdb_id: string;
  imdb_id: string | null;
  movielens_id: number | null;
  title: string;
  original_title: string | null;
  tagline: string | null;
  description: string | null;
  runtime: number | null;
  released_on: string | null;
  poster_url: string | null;
  backdrop_url: string | null;
  original_language: string | null;
  status: string;
  budget: number | null;
  revenue: number | null;
  adult: boolean;
  tmdb_vote_average: number | null;
  tmdb_vote_count: number | null;
  trailer_link: string | null;
  genres: Genre[];
  created_at: string;
  updated_at: string;
}

export interface MovieListParams {
  q?: string;
  genre_id?: number;
  skip?: number;
  limit?: number;
}