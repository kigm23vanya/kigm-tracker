"use client";

import { useEffect, useState } from "react";

import { AuthGuard } from "@/components/AuthGuard";
import { CollapsibleList } from "@/components/CollapsibleList";
import { SectionCard } from "@/components/SectionCard";
import { getAssignments, getEvents } from "@/lib/api";
import { AssignmentCard, EventItem } from "@/lib/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function MainMenuPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [assignments, setAssignments] = useState<AssignmentCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getEvents(), getAssignments()])
      .then(([eventsData, assignmentsData]) => {
        setEvents(eventsData);
        setAssignments(assignmentsData);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthGuard>
      <div className="stack-page">
        <div className="hero-banner reveal">
          <p className="kicker">Main Menu</p>
          <h2>Лента учебной и внеучебной активности</h2>
          <p>Мероприятия колледжа и задания из Google Classroom в одном месте.</p>
        </div>

        <div className="two-column-grid">
          <SectionCard title="Мероприятия колледжа" subtitle="Локальная база приложения">
            {loading ? <p>Загрузка...</p> : null}
            {!loading ? (
              <CollapsibleList<EventItem>
                items={events}
                className="feed-list"
                emptyText="Пока нет мероприятий."
                getKey={(event) => event.id}
                renderItem={(event) => (
                  <li className="feed-item reveal">
                    <div>
                      <h3>{event.title}</h3>
                      <p>{event.description ?? "Без описания"}</p>
                    </div>
                    <div className="meta-grid">
                      <span>{formatDate(event.starts_at)}</span>
                      <span>{event.location ?? "Локация не указана"}</span>
                      <span>+{event.activity_points} баллов</span>
                    </div>
                  </li>
                )}
              />
            ) : null}
          </SectionCard>

          <SectionCard title="Задания Google Classroom" subtitle="CourseWork + StudentSubmission">
            {loading ? <p>Загрузка...</p> : null}
            {!loading ? (
              <CollapsibleList<AssignmentCard>
                items={assignments}
                className="feed-list"
                emptyText="Пока нет заданий."
                getKey={(assignment) => assignment.id}
                renderItem={(assignment) => (
                  <li className="feed-item reveal">
                    <div>
                      <h3>{assignment.assignment_title}</h3>
                      <p className="subject-tag">{assignment.course_title}</p>
                      <p>{assignment.assignment_description ?? "Без описания"}</p>
                    </div>
                    <div className="meta-grid">
                      <span>Deadline: {assignment.due_date ? formatDate(assignment.due_date) : "нет"}</span>
                      <span>Статус: {assignment.submission_state ?? "нет данных"}</span>
                      <span>
                        Оценка: {assignment.assigned_grade ?? assignment.draft_grade ?? "-"}
                        {assignment.max_points ? ` / ${assignment.max_points}` : ""}
                      </span>
                    </div>
                  </li>
                )}
              />
            ) : null}
          </SectionCard>
        </div>
      </div>
    </AuthGuard>
  );
}
