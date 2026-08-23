import { Rating } from "@/types/ratings"
import { apifetch } from "../api-client"

export const ratingApi = {
    rate : (movie_id:number, rating: number, accessToken : string)=>{
        return apifetch<Rating>("/ratings/", {
            method : "POST", body : JSON.stringify({movie_id, rating})
        }, accessToken)
    },

    getForMovie : (movie_id:number, accessToken : string)=>{
        return apifetch<Rating>(`/ratings/movie/${movie_id}`, {}, accessToken)
    },

    remove : (movie_id:number, accessToken:string)=>{
        return apifetch<void>(`/ratings/movie/${movie_id}`, {method: "DELETE"}, accessToken)
    }
}