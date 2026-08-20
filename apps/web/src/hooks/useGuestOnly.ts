import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";


export function useGuestOnly(redirectTo : string = "/"){

    const {user, isLoading} = useAuth();
    const router = useRouter();

    useEffect(()=>{
        if(user && !isLoading)router.replace(redirectTo)
    },[isLoading, user, router, redirectTo]);

    const isCheking = isLoading || !!user;
    return isCheking;
}