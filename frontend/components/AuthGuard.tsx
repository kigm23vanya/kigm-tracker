"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { isLoggedIn } from "@/lib/api";

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      setAllowed(true);
      return;
    }
    router.replace("/login");
  }, [router]);

  if (!allowed) {
    return (
      <section className="auth-loading" aria-live="polite">
        <p>Проверка доступа...</p>
      </section>
    );
  }

  return <>{children}</>;
}
