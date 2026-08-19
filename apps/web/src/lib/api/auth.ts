import { apifetch } from "../api-client";
import { User, SignupPayload, LoginPayload, TokenResponse } from "@/types/user";

export const authApi = {
    signup : (payload : SignupPayload) =>{
        apifetch<User>("/auth/signup", {
            method : "POST",
            body : JSON.stringify(payload)
        })
    },

    login : (payload : LoginPayload)=>{
        apifetch<TokenResponse>("/auth/login", {
            method : "POST",
            body : JSON.stringify(payload)
        })
    },

    refresh : () =>{
        apifetch<TokenResponse>("/auth/refresh", {
            method : "POST"
        })
    },
    
    logout : ()=>{
        apifetch<void>("/auth/logout", {
            method : "POST"
        })
    },

    me : (accessToken : string)=>{
        apifetch<User>("/auth/me", {}, accessToken)
    } 

}