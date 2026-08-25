"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "./Logo";
import { Button } from "./Button";

export function Navbar() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    setMenuOpen(false);
    await logout();
    router.push("/login");
  }

  const navLinkClass = (href: string) =>
    `relative font-sans text-sm transition-colors after:absolute after:left-0 after:-bottom-1 after:h-px after:bg-signal after:transition-all ${
      pathname === href
        ? "text-ink after:w-full"
        : "text-ash hover:text-ink after:w-0 hover:after:w-full"
    }`;

  return (
    <header className="border-b border-ash/15 bg-paper/90 backdrop-blur-md sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-5 md:px-10 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Logo />
        </div>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-3">
          {isLoading ? (
            <div className="h-9 w-20 rounded-md skeleton" />
          ) : user ? (
            <>
              <Link href="/watchlist" className={navLinkClass("/watchlist")}>
                Watchlist
              </Link>
              <span className="font-sans text-sm text-ash">{user.username}</span>
              <Button variant="ghost" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="font-sans text-sm text-ink hover:text-signal transition-colors"
              >
                Sign in
              </Link>
              <Button variant="solid" onClick={() => router.push("/signup")}>
                Sign up
              </Button>
            </>
          )}
        </nav>

        {/* Mobile toggle */}
        <button
          type="button"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((v) => !v)}
          className="sm:hidden flex items-center justify-center h-9 w-9 rounded-md text-ink hover:bg-ink/5 transition-colors"
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      <div
        className={`sm:hidden overflow-hidden border-t border-ash/15 bg-paper transition-[max-height,opacity] duration-300 ease-out ${
          menuOpen ? "max-h-64 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <nav className="px-5 py-4 flex flex-col gap-4">
          {isLoading ? null : user ? (
            <>
              <Link
                href="/watchlist"
                onClick={() => setMenuOpen(false)}
                className="font-sans text-sm text-ink"
              >
                Watchlist
              </Link>
              <div className="flex items-center justify-between">
                <span className="font-sans text-sm text-ash">{user.username}</span>
                <Button variant="ghost" onClick={handleLogout}>
                  Log out
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="font-sans text-sm text-ink"
              >
                Sign in
              </Link>
              <Button
                variant="solid"
                onClick={() => {
                  setMenuOpen(false);
                  router.push("/signup");
                }}
              >
                Sign up
              </Button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
