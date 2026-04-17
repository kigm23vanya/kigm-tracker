"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { AuthGuard } from "@/components/AuthGuard";
import { CollapsibleList } from "@/components/CollapsibleList";
import { SectionCard } from "@/components/SectionCard";
import { getLeaderboard } from "@/lib/api";
import { LeaderboardEntry, LeaderboardScope } from "@/lib/types";

const BOARD_LABELS = {
  grades: "По отметкам",
  activity: "По активности",
  achievements: "По достижениям",
} as const;

const SCOPE_LABELS: Record<LeaderboardScope, string> = {
  group: "Группа",
  course: "Курс",
  college: "Колледж",
};

export default function LeaderboardPage() {
  const [boardType, setBoardType] = useState<"grades" | "activity" | "achievements">("grades");
  const [scope, setScope] = useState<LeaderboardScope>("group");
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);

  useEffect(() => {
    getLeaderboard(boardType, scope).then(setRows);
  }, [boardType, scope]);

  return (
    <AuthGuard>
      <div className="stack-page">
        <div className="hero-banner reveal">
          <p className="kicker">Leaderboard</p>
          <h2>Рейтинги студентов</h2>
          <p>Сравнение по успеваемости, активности и достижениям.</p>
        </div>

        <SectionCard title="Фильтры рейтинга" subtitle="Выберите тип и область сравнения">
          <div className="controls-row">
            <div className="button-group">
              {(Object.keys(BOARD_LABELS) as Array<"grades" | "activity" | "achievements">).map((type) => (
                <button
                  key={type}
                  type="button"
                  className={boardType === type ? "chip active" : "chip"}
                  onClick={() => setBoardType(type)}
                >
                  {BOARD_LABELS[type]}
                </button>
              ))}
            </div>

            <div className="button-group">
              {(Object.keys(SCOPE_LABELS) as LeaderboardScope[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={scope === item ? "chip active" : "chip"}
                  onClick={() => setScope(item)}
                >
                  {SCOPE_LABELS[item]}
                </button>
              ))}
            </div>
          </div>
        </SectionCard>

        <SectionCard title={BOARD_LABELS[boardType]} subtitle={`Область: ${SCOPE_LABELS[scope]}`}>
          <CollapsibleList<LeaderboardEntry>
            items={rows}
            className="leaderboard-list"
            emptyText="Нет данных для отображения."
            getKey={(entry) => entry.user_id}
            renderItem={(entry) => (
              <li className="leader-row reveal">
                <strong className="rank">#{entry.position}</strong>
                <Link className="name profile-link" href={`/profile?userId=${entry.user_id}`}>
                  {entry.full_name}
                </Link>
                <span className="score">{entry.score}</span>
              </li>
            )}
          />
        </SectionCard>
      </div>
    </AuthGuard>
  );
}
