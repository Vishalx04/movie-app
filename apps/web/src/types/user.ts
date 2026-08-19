export interface User {
    id : number
    email: string
    name: string | null
    username: string
    created_at : string
}

export interface SignupPayload {
    email : string
    username : string
    name?: string
    password : string
}

export interface TokenResponse{
    access_token : string
    token_type : string
}

export interface LoginPayload {
    email :  string
    password : string
}
