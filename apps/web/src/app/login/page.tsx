"use client";

import { useState, type SubmitEventHandler } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api-error";
import { useGuestOnly } from "@/hooks/useGuestOnly";

export default function LoginPage() {
    const router = useRouter();
    const { login } = useAuth();
    const  isChecking  = useGuestOnly();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();

        setError(null);
        setIsSubmitting(true);

        try {
            await login({ email, password });
            router.push("/");
        } catch (err) {
            const message =
                err instanceof ApiError
                    ? err.message
                    : "Something went wrong. Please try again.";

            setError(message);
        } finally {
            setIsSubmitting(false);
        }
    };
    if (isChecking) {
        return <div className="flex-1" />;
    }

    return (
        <div className="flex-1 flex items-center justify-center bg-paper px-4">
            <div className="w-full max-w-sm">
                <h1 className="font-display text-3xl text-ink mb-1">Welcome back</h1>
                <p className="font-sans text-ash text-sm mb-8">Sign in to your account</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="email" className="font-sans text-sm text-ink block mb-1">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-panel border border-ash/30 rounded-md px-3 py-2 font-sans text-ink focus:outline-none focus:border-signal"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="font-sans text-sm text-ink block mb-1">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-panel border border-ash/30 rounded-md px-3 py-2 font-sans text-ink focus:outline-none focus:border-signal"
                        />
                    </div>

                    {error && <p className="font-sans text-sm text-signal">{error}</p>}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full bg-ink text-paper rounded-md py-2 font-sans font-medium disabled:opacity-50"
                    >
                        {isSubmitting ? "Signing in..." : "Sign in"}
                    </button>
                </form>

                <p className="font-sans text-sm text-ash mt-6 text-center">
                    No account?{" "}
                    <Link href="/signup" className="text-signal underline">
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    );
}