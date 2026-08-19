export class ApiError extends Error {
    status: number;
    constructor(status: number, message : string){
        super(message);
        this.status = status
        this.name = "ApiError"
    }
}

export async function parseApiError(response : Response): Promise<ApiError> {

    const body = await response.json().catch(()=>({}))
    const message = (typeof body.detail === "string")? body.detail: "Something went wrong. Please try again.";
    return new ApiError(response.status, message);
}