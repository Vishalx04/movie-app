import { apifetch } from "../api-client";
import { User, SignupPayload, LoginPayload, TokenResponse } from "@/types/user";

export const authApi = {
    signup : (payload : SignupPayload) =>{
        return apifetch<User>("/auth/signup", {
            method : "POST",
            body : JSON.stringify(payload)
        })
    },

    login : (payload : LoginPayload)=>{
        return apifetch<TokenResponse>("/auth/login", {
            method : "POST",
            body : JSON.stringify(payload)
        })
    },

    refresh : () =>{
        return apifetch<TokenResponse>("/auth/refresh", {
            method : "POST"
        })
    },
    
    logout : ()=>{
        apifetch<void>("/auth/logout", {
            method : "POST"
        })
    },

    me : (accessToken : string)=>{
        return apifetch<User>("/auth/me", {}, accessToken)
    } 

}