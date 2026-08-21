export class ApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
        super(message);
        this.status = status;
        this.name = "ApiError";
    }
}

export async function parseApiError(response: Response): Promise<ApiError> {
    const body = await response.json().catch(() => ({}));

    if (typeof body.detail === "string") {
        return new ApiError(response.status, body.detail);
    }

    if (Array.isArray(body.detail) && body.detail.length > 0) {
        const error = body.detail[0];

        const field = error.loc?.[1];

        const fieldName =
            typeof field === "string"
                ? field.charAt(0).toUpperCase() + field.slice(1)
                : "";

        const message =
            typeof error.msg === "string"
                ? error.msg.replace(/^Value error,\s*/, "")
                : "Something went wrong. Please try again.";

        const finalMessage =
            fieldName && !message.toLowerCase().startsWith(fieldName.toLowerCase())
                ? `${fieldName} ${message}`
                : message;

        return new ApiError(response.status, finalMessage);
    }

    return new ApiError(
        response.status,
        "Something went wrong. Please try again."
    );
}