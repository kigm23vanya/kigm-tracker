"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { getSession, isLoggedIn, logout } from "@/lib/api";

const LINKS = [
  { href: "/", label: "Main Menu" },
  { href: "/profile", label: "Profile" },
  { href: "/leaderboard", label: "Leaderboard" },
];

export function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    setLoggedIn(isLoggedIn());
    setDisplayName(session?.full_name ?? null);
  }, [pathname]);

  function onLogout() {
    logout();
    setLoggedIn(false);
    setDisplayName(null);
    router.push("/login");
  }

  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        <div className="brand-block">
          <span className="brand-kicker">College Performance System</span>
          <h1>Kigm Tracker</h1>
          {displayName ? <p className="auth-caption">{displayName}</p> : null}
        </div>

        <nav className="menu-links" aria-label="Main navigation">
          {!loggedIn ? (
            <Link href="/login" className={pathname === "/login" ? "menu-link active" : "menu-link"}>
              Login
            </Link>
          ) : null}
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "menu-link active" : "menu-link"}
            >
              {link.label}
            </Link>
          ))}
          {loggedIn ? (
            <button type="button" className="menu-link menu-button" onClick={onLogout}>
              Logout
            </button>
          ) : null}
        </nav>
      </div>
    </header>
  );
}
