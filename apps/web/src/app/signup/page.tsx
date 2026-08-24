"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, User, IdCard, Lock, Eye, EyeOff } from "lucide-react";
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
    const [showPassword, setShowPassword] = useState(false);
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
        <div className="flex-1 flex items-center justify-center bg-paper px-4 py-16">
            <div className="w-full max-w-sm animate-fade-in-up">
                <div className="bg-panel border border-ash/12 rounded-2xl shadow-card px-7 py-9 sm:px-9 sm:py-10">
                    <h1 className="font-display text-3xl text-ink mb-1.5">Create an account</h1>
                    <p className="font-sans text-ash text-sm mb-8">Start tracking movies you love</p>

                    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                        <div>
                            <label htmlFor="email" className="font-sans text-sm text-ink block mb-1.5">
                                Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ash pointer-events-none" />
                                <input
                                    id="email"
                                    type="email"
                                    required
                                    autoComplete="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full h-11 bg-paper border border-ash/25 rounded-lg pl-10 pr-3 font-sans text-sm text-ink outline-none transition-colors focus:border-signal"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="username" className="font-sans text-sm text-ink block mb-1.5">
                                Username
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ash pointer-events-none" />
                                <input
                                    id="username"
                                    type="text"
                                    required
                                    minLength={3}
                                    autoComplete="username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full h-11 bg-paper border border-ash/25 rounded-lg pl-10 pr-3 font-sans text-sm text-ink outline-none transition-colors focus:border-signal"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="name" className="font-sans text-sm text-ink block mb-1.5">
                                Name <span className="text-ash">(optional)</span>
                            </label>
                            <div className="relative">
                                <IdCard className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ash pointer-events-none" />
                                <input
                                    id="name"
                                    type="text"
                                    autoComplete="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full h-11 bg-paper border border-ash/25 rounded-lg pl-10 pr-3 font-sans text-sm text-ink outline-none transition-colors focus:border-signal"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="font-sans text-sm text-ink block mb-1.5">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ash pointer-events-none" />
                                <input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    minLength={8}
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full h-11 bg-paper border border-ash/25 rounded-lg pl-10 pr-10 font-sans text-sm text-ink outline-none transition-colors focus:border-signal"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((v) => !v)}
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ash hover:text-ink transition-colors"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            <p className="font-sans text-xs text-ash mt-1.5">At least 8 characters.</p>
                        </div>

                        {error && (
                            <p className="font-sans text-sm text-signal bg-signal/8 border border-signal/20 rounded-lg px-3 py-2">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full h-11 bg-ink text-paper rounded-lg font-sans font-medium text-sm transition-all hover:bg-ink/90 active:scale-[0.99] disabled:opacity-50 disabled:active:scale-100"
                        >
                            {isSubmitting ? "Creating account..." : "Create account"}
                        </button>
                    </form>
                </div>

                <p className="font-sans text-sm text-ash mt-6 text-center">
                    Already have an account?{" "}
                    <Link href="/login" className="text-signal hover:text-signal-hover underline underline-offset-2">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}