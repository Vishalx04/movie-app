"use client"

import { LoginPayload, SignupPayload, User } from "@/types/user"
import { createContext, ReactNode, useState } from "react"

interface AuthContextValue{
    user : User
    access_token : string
    isLoading : boolean
    login:(payload: LoginPayload) => Promise<void>;
    signup:(payload : SignupPayload) => Promise<void>;
}

const authContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({children}:  {children : ReactNode}){
    const [user,setUser] = useState<User | null>(null);
    const [accessToken, setAccessToken] = useState<string|null>(null);
    const [isLoading, setIsLoading] = useState(true);

    
}