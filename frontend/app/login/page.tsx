"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { CollapsibleList } from "@/components/CollapsibleList";
import { SectionCard } from "@/components/SectionCard";
import { isLoggedIn, loginWithPassword } from "@/lib/api";

interface DemoAccount {
  email: string;
  password: string;
  label: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  { email: "st.student@kigm23.ru", password: "student2026", label: "Студент (основной профиль)" },
  { email: "maria.petrova@kigm23.ru", password: "maria2026", label: "Студент (высокий рейтинг)" },
  { email: "curator.ivanova@kigm23.ru", password: "curator1", label: "Куратор группы КИГМ-201" },
  { email: "curator.petrov@kigm23.ru", password: "curator2", label: "Куратор группы КИГМ-202" },
  { email: "teacher.math@kigm23.ru", password: "teachmath2026", label: "Преподаватель математики" },
  { email: "teacher.network@kigm23.ru", password: "teachnet2026", label: "Преподаватель сетевых дисциплин" },
  { email: "admin@kigm23.ru", password: "admin2026", label: "Администратор" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("st.student@kigm23.ru");
  const [password, setPassword] = useState("student2026");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/profile");
    }
  }, [router]);

  const domainHint = useMemo(() => email.trim().toLowerCase().endsWith("@kigm23.ru"), [email]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!domainHint) {
      setError("Используй почту вида user@kigm23.ru");
      return;
    }

    setLoading(true);
    try {
      await loginWithPassword(email, password);
      router.replace("/profile");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Ошибка входа";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack-page auth-page">
      <div className="hero-banner reveal">
        <p className="kicker">Login</p>
        <h2>Вход в Kigm Tracker</h2>
        <p>Вход по логину и паролю. Разрешены только адреса домена @kigm23.ru.</p>
      </div>

      <SectionCard title="Авторизация" subtitle="Демо-вход для MVP">
        <form className="login-form" onSubmit={onSubmit}>
          <label className="field-label" htmlFor="email">
            Почта
          </label>
          <input
            id="email"
            className="text-input"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="st.student@kigm23.ru"
            required
          />

          <label className="field-label" htmlFor="password">
            Пароль
          </label>
          <input
            id="password"
            className="text-input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введите пароль"
            minLength={6}
            required
          />

          <button type="submit" className="solid-button" disabled={loading}>
            {loading ? "Входим..." : "Войти"}
          </button>

          {error ? <p className="form-error">{error}</p> : null}
        </form>

        <div className="demo-credentials">
          <h3>Тестовые аккаунты</h3>
          <CollapsibleList<DemoAccount>
            items={DEMO_ACCOUNTS}
            className="feed-list"
            getKey={(account) => account.email}
            renderItem={(account) => (
              <li className="feed-item">
                <div>
                  <h3>{account.label}</h3>
                  <p>{account.email}</p>
                </div>
                <div className="meta-grid">
                  <span>Пароль: {account.password}</span>
                </div>
              </li>
            )}
          />
        </div>
      </SectionCard>
    </div>
  );
}
