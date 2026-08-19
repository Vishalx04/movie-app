"use client";

import { useState } from "react";

type FieldProps = {
  label: string;
  type: string;
  name: string;
  autoComplete?: string;
};

function Field({ label, type, name, autoComplete }: FieldProps) {
  return (
    <label className="block">
      <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-ash">
        {label}
      </span>

      <input
        type={type}
        name={name}
        required
        autoComplete={autoComplete}
        className="mt-2 w-full border-0 border-b border-ink/15 bg-transparent py-2.5 font-sans text-[15px] text-ink outline-none transition-colors placeholder:text-ash/50 focus:border-signal"
      />
    </label>
  );
}

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Connect to auth API here.
  };

  return (
    <main className="min-h-screen bg-paper">
      <div className="mx-auto flex min-h-screen max-w-6xl">
        {/* Left */}
        <section className="hidden flex-1 flex-col justify-between px-12 py-12 lg:flex">
          <div>
            <span className="font-mono text-sm tracking-[0.08em] text-ink">
              MOVIES
            </span>
          </div>

          <div className="max-w-lg">
            <p className="mb-4 font-mono text-xs uppercase tracking-[0.12em] text-signal">
              Your watchlist, ratings & recommendations
            </p>

            <h1 className="font-display text-6xl leading-[0.95] text-ink">
              Find your
              <br />
              next favorite.
            </h1>

            <p className="mt-6 max-w-md font-sans text-[15px] leading-7 text-ash">
              Keep track of the movies you love and discover something new
              based on your taste.
            </p>
          </div>

          <p className="font-mono text-[11px] text-ash">
            Discover · Rate · Watch
          </p>
        </section>

        {/* Form */}
        <section className="flex w-full items-center justify-center px-6 py-12 sm:px-10 lg:w-[440px] lg:border-l lg:border-ink/10 lg:px-14">
          <div className="w-full max-w-sm">
            <div className="mb-10 lg:hidden">
              <span className="font-mono text-sm tracking-[0.08em] text-ink">
                MOVIES
              </span>
            </div>

            <div className="mb-8">
              <h2 className="font-display text-3xl text-ink">
                {mode === "login" ? "Welcome back" : "Create your account"}
              </h2>

              <p className="mt-2 font-sans text-sm text-ash">
                {mode === "login"
                  ? "Sign in to continue."
                  : "Start building your movie profile."}
              </p>
            </div>

            <div className="mb-9 flex gap-6 border-b border-ink/10">
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`relative pb-3 font-mono text-xs uppercase tracking-[0.1em] transition-colors ${
                  mode === "login"
                    ? "text-ink"
                    : "text-ash hover:text-ink"
                }`}
              >
                Log in

                {mode === "login" && (
                  <span className="absolute inset-x-0 -bottom-px h-px bg-signal" />
                )}
              </button>

              <button
                type="button"
                onClick={() => setMode("register")}
                className={`relative pb-3 font-mono text-xs uppercase tracking-[0.1em] transition-colors ${
                  mode === "register"
                    ? "text-ink"
                    : "text-ash hover:text-ink"
                }`}
              >
                Sign up

                {mode === "register" && (
                  <span className="absolute inset-x-0 -bottom-px h-px bg-signal" />
                )}
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-7">
              {mode === "register" && (
                <Field
                  label="Name"
                  type="text"
                  name="name"
                  autoComplete="name"
                />
              )}

              <Field
                label="Email"
                type="email"
                name="email"
                autoComplete="email"
              />

              <Field
                label="Password"
                type="password"
                name="password"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
              />

              {mode === "login" && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="font-sans text-sm text-ash underline decoration-ink/20 underline-offset-4 transition-colors hover:text-signal"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-ink py-3.5 font-sans text-sm font-medium text-paper transition-colors hover:bg-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
              >
                {mode === "login" ? "Log in" : "Create account"}
              </button>
            </form>

            <p className="mt-7 font-sans text-sm text-ash">
              {mode === "login" ? (
                <>
                  Don't have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setMode("register")}
                    className="text-ink underline decoration-ink/20 underline-offset-4 hover:text-signal"
                  >
                    Sign up
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setMode("login")}
                    className="text-ink underline decoration-ink/20 underline-offset-4 hover:text-signal"
                  >
                    Log in
                  </button>
                </>
              )}
            </p>

            <p className="mt-12 font-mono text-[10px] leading-relaxed text-ash">
              By continuing, you agree to the Terms and Privacy Policy.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}