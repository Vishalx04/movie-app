"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "./Logo";

export function Navbar() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="border-b border-ash/20 bg-paper">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <Logo />

        <nav className="font-sans text-sm flex items-center gap-4">
          {isLoading ? null : user ? (
            <>
              <span className="text-ash">{user.username}</span>
              <button onClick={handleLogout} className="text-ink hover:text-signal">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-ink hover:text-signal">
                Sign in
              </Link>
              <Link
                href="/signup"
                className="bg-ink text-paper rounded-md px-3 py-1.5 hover:opacity-90"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}