"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useGuestOnly } from "@/hooks/useGuestOnly";
import { ApiError } from "@/lib/api-error";

export default function SignupPage() {
    const router = useRouter();
    const { signup } = useAuth();
    const isChecking = useGuestOnly();

    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            await signup({ email, username, password, name: name || undefined });
            router.push("/");
        } catch (err) {
            const message =
                err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
            setError(message);
        } finally {
            setIsSubmitting(false);
        }
    }

    if (isChecking) {
        return <div className="flex-1" />;
    }

    return (
        <div className="flex-1 flex items-center justify-center bg-paper px-4">
            <div className="w-full max-w-sm">
                <h1 className="font-display text-3xl text-ink mb-1">Create an account</h1>
                <p className="font-sans text-ash text-sm mb-8">Start tracking movies you love</p>

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
                        <label htmlFor="username" className="font-sans text-sm text-ink block mb-1">
                            Username
                        </label>
                        <input
                            id="username"
                            type="text"
                            required
                            minLength={3}
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-panel border border-ash/30 rounded-md px-3 py-2 font-sans text-ink focus:outline-none focus:border-signal"
                        />
                    </div>

                    <div>
                        <label htmlFor="name" className="font-sans text-sm text-ink block mb-1">
                            Name <span className="text-ash">(optional)</span>
                        </label>
                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
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
                            minLength={8}
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
                        {isSubmitting ? "Creating account..." : "Create account"}
                    </button>
                </form>

                <p className="font-sans text-sm text-ash mt-6 text-center">
                    Already have an account?{" "}
                    <Link href="/login" className="text-signal underline">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}