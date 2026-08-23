import { Genre } from "@/types/genre";
import { apifetch } from "../api-client";

export const genreApi = {
    list: ()=> apifetch<Genre[]>("/genres/"),
}