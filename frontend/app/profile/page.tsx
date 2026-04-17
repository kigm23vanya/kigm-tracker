"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { AuthGuard } from "@/components/AuthGuard";
import { CollapsibleList } from "@/components/CollapsibleList";
import { SectionCard } from "@/components/SectionCard";
import { getProfileAchievements, getProfileEvents, getProfileGrades, getProfileSummary } from "@/lib/api";
import { AchievementRecord, EventItem, ProfileEvent, ProfileSummary, SubjectGrade } from "@/lib/types";

function prettyDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

export default function ProfilePage() {
  const searchParams = useSearchParams();
  const targetUserIdParam = searchParams.get("userId");
  const targetUserId = targetUserIdParam ? Number(targetUserIdParam) : undefined;
  const validTargetUserId = Number.isFinite(targetUserId) ? targetUserId : undefined;

  const [summary, setSummary] = useState<ProfileSummary | null>(null);
  const [achievements, setAchievements] = useState<AchievementRecord[]>([]);
  const [grades, setGrades] = useState<SubjectGrade[]>([]);
  const [events, setEvents] = useState<ProfileEvent[]>([]);

  useEffect(() => {
    Promise.all([
      getProfileSummary(validTargetUserId),
      getProfileAchievements(validTargetUserId),
      getProfileGrades(validTargetUserId),
      getProfileEvents(validTargetUserId),
    ]).then(([summaryData, achievementsData, gradesData, eventsData]) => {
      setSummary(summaryData);
      setAchievements(achievementsData);
      setGrades(gradesData);
      setEvents(eventsData);
    });
  }, [validTargetUserId]);

  const rarityLabel: Record<string, string> = {
    common: "Обычное",
    rare: "Редкое",
    epic: "Эпическое",
    legendary: "Легендарное",
  };

  const participationLabel: Record<string, string> = {
    none: "Нет участия",
    registered: "Зарегистрирован",
    participated: "Участвовал",
  };

  return (
    <AuthGuard>
      <div className="stack-page">
        <div className="hero-banner reveal">
          <p className="kicker">Profile</p>
          <h2>{summary ? `Статистика студента: ${summary.user.full_name}` : "Статистика студента"}</h2>
          <p>Рейтинг, опыт, достижения и участие в жизни колледжа. Можно просматривать профили других пользователей.</p>
          {validTargetUserId ? (
            <p>
              <Link href="/profile" className="profile-link">
                Вернуться к моему профилю
              </Link>
            </p>
          ) : null}
        </div>

        <SectionCard title="Основные данные" subtitle="Звание, ФИО, почта, контакт и мастерство">
          {summary ? (
            <div className="metrics-grid">
              <article className="metric">
                <strong>Звание: {summary.title}</strong>
                <span>{summary.user.full_name}</span>
                <span>{summary.user.email}</span>
                {summary.phone ? <span className="contact-line">{summary.phone}</span> : null}
              </article>
              <article className="metric">
                <strong>Мастерство {summary.user.course_number}</strong>
                <span>Курс {summary.user.course_number}</span>
              </article>
              <article className="metric">
                <strong>{summary.total_achievements}</strong>
                <span>достижений</span>
              </article>
              <article className="metric">
                <strong>
                  {summary.experience.infinite ? "∞" : `${summary.experience.experience.toLocaleString("ru-RU")}`}
                </strong>
                <span>опыта</span>
              </article>
            </div>
          ) : (
            <p>Загрузка...</p>
          )}
        </SectionCard>

        <SectionCard title="Шкала уровня" subtitle="Опыт, текущий уровень и прогресс">
          {summary ? (
            <div className="xp-block">
              <div className="xp-label-row">
                <strong>{summary.experience.infinite ? "Уровень: ∞" : `Уровень ${summary.experience.level ?? 1}`}</strong>
                <span>
                  {summary.experience.infinite
                    ? "Бесконечный опыт"
                    : `${summary.experience.current_level_xp}/${summary.experience.next_level_xp ?? 0} XP`}
                </span>
              </div>
              <div className="xp-track" role="progressbar" aria-valuenow={summary.experience.progress_percent} aria-valuemin={0} aria-valuemax={100}>
                <div
                  className="xp-fill"
                  style={{ width: summary.experience.infinite ? "100%" : `${summary.experience.progress_percent}%` }}
                />
              </div>
              <p>
                Прогресс: {summary.experience.infinite ? "100%" : `${summary.experience.progress_percent.toFixed(2)}%`}.
                Баллы активности: {summary.activity_points}.
              </p>
            </div>
          ) : (
            <p>Загрузка...</p>
          )}
        </SectionCard>

        {summary?.user.role === "teacher" && summary.teacher_profile ? (
          <SectionCard title="Профиль преподавателя" subtitle="Кураторство, стаж и организованные мероприятия">
            <div className="metrics-grid teacher-grid">
              <article className="metric">
                <strong>{summary.user.full_name}</strong>
                <span>{summary.user.email}</span>
                <span>Куратор группы: {summary.teacher_profile.curator_group ?? "не назначен"}</span>
              </article>
              <article className="metric">
                <strong>{summary.teacher_profile.work_experience_years}</strong>
                <span>лет стажа в колледже</span>
              </article>
            </div>

            <CollapsibleList<EventItem>
              items={summary.teacher_profile.organized_events}
              className="feed-list"
              emptyText="Пока нет организованных мероприятий."
              getKey={(event) => event.id}
              renderItem={(event) => (
                <li className="feed-item reveal">
                  <div>
                    <h3>{event.title}</h3>
                    <p>{event.description ?? "Без описания"}</p>
                  </div>
                  <div className="meta-grid">
                    <span>{prettyDate(event.starts_at)}</span>
                    <span>{event.subject_name ?? "Без предметной привязки"}</span>
                    <span>+{event.activity_points} активности</span>
                  </div>
                </li>
              )}
            />
          </SectionCard>
        ) : null}

        <div className="two-column-grid">
          <SectionCard title="Достижения" subtitle="Редкости: common/rare/epic/legendary">
            <CollapsibleList<AchievementRecord>
              items={achievements}
              className="feed-list"
              emptyText="Пока нет достижений."
              getKey={(item) => item.id}
              renderItem={(item) => (
                <li className="feed-item reveal">
                  <div>
                    <h3>{item.achievement.title}</h3>
                    <p>{item.achievement.description}</p>
                  </div>
                  <div className="meta-grid">
                    <span>{rarityLabel[item.achievement.rarity] ?? item.achievement.rarity}</span>
                    <span>{prettyDate(item.awarded_at)}</span>
                  </div>
                </li>
              )}
            />
          </SectionCard>

          <SectionCard title="Отметки по предметам" subtitle="Итог, средний балл и выполнение">
            <CollapsibleList<SubjectGrade>
              items={grades}
              className="feed-list"
              emptyText="Пока нет оценок."
              getKey={(item) => item.subject_name}
              renderItem={(item) => (
                <li className="feed-item reveal">
                  <div>
                    <h3>{item.subject_name}</h3>
                    <p>Выполнено заданий: {item.completed_assignments}</p>
                  </div>
                  <div className="meta-grid">
                    <span>Итог: {item.final_grade ?? "-"}</span>
                    <span>Средний: {item.average_grade ?? "-"}</span>
                  </div>
                </li>
              )}
            />
          </SectionCard>
        </div>

        <SectionCard title="Участие в мероприятиях" subtitle="Статус, результат, начисленные баллы">
          <CollapsibleList<ProfileEvent>
            items={events}
            className="feed-list"
            emptyText="Пока нет участия в мероприятиях."
            getKey={(item) => item.id}
            renderItem={(item) => (
              <li className="feed-item reveal">
                <div>
                  <h3>{item.event_title}</h3>
                  <p>Статус: {participationLabel[item.participation_status] ?? item.participation_status}</p>
                </div>
                <div className="meta-grid">
                  <span>{prettyDate(item.date)}</span>
                  <span>Результат: {item.result ?? "-"}</span>
                  <span>+{item.points_awarded} баллов активности</span>
                </div>
              </li>
            )}
          />
        </SectionCard>
      </div>
    </AuthGuard>
  );
}
