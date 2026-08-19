import { parseApiError } from "./api-error";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function apifetch<T>(
    path : string,
    options : RequestInit = {},
    accessToken? :string
) : Promise<T> {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");

    if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
    }

    const response = await fetch(`${API_BASE_URL} ${path}`,
        {
            ...options,
            headers,
            credentials: "include"
        }
    );

    if(!response.ok){
        throw await parseApiError(response);
    }

    if(response.status===204){
        return undefined as T
    }

    return response.json();
}