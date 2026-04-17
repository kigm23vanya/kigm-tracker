import {
  AuthLoginResponse,
  AuthSession,
  AchievementRecord,
  AssignmentCard,
  EventItem,
  LeaderboardEntry,
  LeaderboardScope,
  ProfileEvent,
  ProfileSummary,
  SubjectGrade,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SESSION_STORAGE_KEY = "kigm.tracker.session";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readSession(): AuthSession | null {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed?.user_id || !parsed?.email) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeSession(session: AuthSession): void {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function getSession(): AuthSession | null {
  return readSession();
}

export function isLoggedIn(): boolean {
  return readSession() !== null;
}

export function logout(): void {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

function getCurrentUserId(): string | null {
  const session = readSession();
  if (!session) {
    return null;
  }
  return String(session.user_id);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  const userId = getCurrentUserId();
  if (userId) {
    headers.set("X-User-Id", userId);
  }

  const method = init?.method?.toUpperCase();
  if (method && method !== "GET" && method !== "HEAD" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const errorPayload = (await response.json()) as { detail?: string };
      if (errorPayload?.detail) {
        detail = errorPayload.detail;
      }
    } catch {
      // Ignore JSON parsing errors and keep default message.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

function withFallback<T>(promise: Promise<T>, fallback: T): Promise<T> {
  return promise.catch(() => fallback);
}

export async function loginWithPassword(email: string, password: string): Promise<AuthSession> {
  const normalizedEmail = email.trim().toLowerCase();
  if (!normalizedEmail.endsWith("@kigm23.ru")) {
    throw new Error("Разрешены только адреса с доменом @kigm23.ru");
  }

  const payload = await requestJson<AuthLoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email: normalizedEmail,
      password,
    }),
  });

  const session: AuthSession = {
    user_id: payload.user.id,
    email: payload.user.email,
    full_name: payload.user.full_name,
    access_token: payload.access_token,
  };

  writeSession(session);
  return session;
}

export function getEvents(): Promise<EventItem[]> {
  return withFallback(
    requestJson<EventItem[]>("/events"),
    [
      {
        id: 1,
        title: 'Хакатон "СтудКод"',
        description: "Командная разработка и защита проекта",
        starts_at: new Date().toISOString(),
        location: "IT-лаборатория",
        organizer: "Кафедра ИТ",
        activity_points: 40,
        subject_name: "Алгоритмы и структура данных",
      },
      {
        id: 2,
        title: "Олимпиада",
        description: "Предметная олимпиада по математике и алгоритмам",
        starts_at: new Date().toISOString(),
        location: "Учебный корпус 2",
        organizer: "Антон Жуков",
        activity_points: 35,
        subject_name: "Высшая математика",
      },
      {
        id: 3,
        title: "Субботник",
        description: "Общеколледжное мероприятие",
        starts_at: new Date().toISOString(),
        location: "Территория колледжа",
        organizer: "Ирина Иванова",
        activity_points: 15,
      },
      {
        id: 4,
        title: "Учебные сборы",
        description: "Учебно-практические сборы по сетям",
        starts_at: new Date().toISOString(),
        location: "Тренировочный центр",
        organizer: "Елена Соколова",
        activity_points: 25,
        subject_name: "Компьютерные сети",
      },
    ],
  );
}

export function getAssignments(): Promise<AssignmentCard[]> {
  return withFallback(
    requestJson<AssignmentCard[]>("/assignments"),
    [
      {
        id: 1,
        course_title: "Алгоритмы и структура данных",
        assignment_title: "Практика: Алгоритмы и структура данных",
        assignment_description: "Решить задачи по сортировкам и графам",
        due_date: new Date().toISOString(),
        max_points: 5,
        submission_state: "RETURNED",
        draft_grade: 5,
        assigned_grade: 5,
        comment: "Отличная работа",
      },
      {
        id: 2,
        course_title: "Высшая математика",
        assignment_title: "Экзамен: Высшая математика",
        assignment_description: "Экзаменационная контрольная",
        due_date: new Date().toISOString(),
        max_points: 5,
        submission_state: "RETURNED",
        assigned_grade: 5,
        draft_grade: 5,
        comment: "Экзамен сдан",
      },
      {
        id: 3,
        course_title: "Базы данных",
        assignment_title: "Практика: Базы данных",
        assignment_description: "Смоделировать схему и SQL-запросы",
        due_date: new Date().toISOString(),
        max_points: 5,
        submission_state: "RETURNED",
        assigned_grade: 4,
        draft_grade: 4,
        comment: "Хорошая нормализация",
      },
    ],
  );
}

function profilePath(userId?: number): string {
  return typeof userId === "number" ? `/profile/${userId}` : "/profile";
}

export function getProfileSummary(userId?: number): Promise<ProfileSummary> {
  return withFallback(
    requestJson<ProfileSummary>(profilePath(userId)),
    {
      user: {
        id: 2,
        full_name: "Степан Студент",
        email: "st.student@kigm23.ru",
        role: "student",
        group_id: 1,
        course_number: 2,
        avatar_url: null,
      },
      title: "студент",
      phone: "89996665267",
      total_achievements: 3,
      activity_points: 40,
      experience: {
        experience: 4780,
        level: 4,
        progress_percent: 76,
        current_level_xp: 760,
        next_level_xp: 1000,
        infinite: false,
      },
      teacher_profile: null,
    },
  );
}

export function getProfileAchievements(userId?: number): Promise<AchievementRecord[]> {
  const path = typeof userId === "number" ? `/profile/${userId}/achievements` : "/profile/achievements";
  return withFallback(requestJson<AchievementRecord[]>(path), [
    {
      id: 1,
      awarded_at: new Date().toISOString(),
      reason: "Регистрация в системе",
      achievement: {
        id: 1,
        title: "Зачисление",
        description: "Студент зарегистрирован в системе",
        rarity: "common",
      },
    },
    {
      id: 2,
      awarded_at: new Date().toISOString(),
      reason: "Первая оценка 5",
      achievement: {
        id: 2,
        title: "Первая пятерка",
        description: "Получена первая оценка 5",
        rarity: "epic",
      },
    },
  ]);
}

export function getProfileGrades(userId?: number): Promise<SubjectGrade[]> {
  const path = typeof userId === "number" ? `/profile/${userId}/grades` : "/profile/grades";
  return withFallback(requestJson<SubjectGrade[]>(path), [
    {
      subject_name: "Русский язык",
      final_grade: 4,
      average_grade: 4,
      completed_assignments: 2,
    },
    {
      subject_name: "Высшая математика",
      final_grade: 5,
      average_grade: 5,
      completed_assignments: 2,
    },
    {
      subject_name: "Алгоритмы и структура данных",
      final_grade: 5,
      average_grade: 4.5,
      completed_assignments: 2,
    },
    {
      subject_name: "Базы данных",
      final_grade: 4,
      average_grade: 4,
      completed_assignments: 2,
    },
    {
      subject_name: "Английский язык",
      final_grade: 4,
      average_grade: 4,
      completed_assignments: 2,
    },
    {
      subject_name: "Операционные сети, среды архитектура аппаратных средства",
      final_grade: 3,
      average_grade: 3,
      completed_assignments: 2,
    },
    {
      subject_name: "Компьютерные сети",
      final_grade: 4,
      average_grade: 4,
      completed_assignments: 2,
    },
    {
      subject_name: "Разработка, поддержка и тестирование программных модулей",
      final_grade: 5,
      average_grade: 4.5,
      completed_assignments: 2,
    },
  ]);
}

export function getProfileEvents(userId?: number): Promise<ProfileEvent[]> {
  const path = typeof userId === "number" ? `/profile/${userId}/events` : "/profile/events";
  return withFallback(requestJson<ProfileEvent[]>(path), [
    {
      id: 1,
      event_id: 1,
      event_title: 'Хакатон "СтудКод"',
      date: new Date().toISOString(),
      participation_status: "participated",
      result: "Финалист",
      points_awarded: 40,
    },
    {
      id: 2,
      event_id: 2,
      event_title: "Олимпиада",
      date: new Date().toISOString(),
      participation_status: "participated",
      result: "Участник",
      points_awarded: 30,
    },
    {
      id: 3,
      event_id: 3,
      event_title: "Субботник",
      date: new Date().toISOString(),
      participation_status: "participated",
      result: "Участник",
      points_awarded: 12,
    },
  ]);
}

export function getLeaderboard(
  type: "grades" | "activity" | "achievements",
  scope: LeaderboardScope,
): Promise<LeaderboardEntry[]> {
  return withFallback(
    requestJson<LeaderboardEntry[]>(`/leaderboard/${type}?scope=${scope}`),
    [
      {
        position: 1,
        user_id: 3,
        full_name: "Мария Петрова",
        score: 98,
      },
      {
        position: 2,
        user_id: 2,
        full_name: "Степан Студент",
        score: 92,
      },
      {
        position: 3,
        user_id: 9,
        full_name: "София Романова",
        score: 90,
      },
      {
        position: 4,
        user_id: 8,
        full_name: "Дарья Волкова",
        score: 87,
      },
      {
        position: 5,
        user_id: 4,
        full_name: "Алина Ким",
        score: 79,
      },
      {
        position: 6,
        user_id: 6,
        full_name: "Никита Смирнов",
        score: 74,
      },
      {
        position: 7,
        user_id: 5,
        full_name: "Олег Иванов",
        score: 69,
      },
      {
        position: 8,
        user_id: 7,
        full_name: "Роман Козлов",
        score: 61,
      },
      {
        position: 9,
        user_id: 10,
        full_name: "Полина Фадеева",
        score: 59,
      },
      {
        position: 10,
        user_id: 11,
        full_name: "Кирилл Волков",
        score: 57,
      },
      {
        position: 11,
        user_id: 12,
        full_name: "Владислав Новиков",
        score: 55,
      },
      {
        position: 12,
        user_id: 13,
        full_name: "Дарья Кузнецова",
        score: 53,
      },
      {
        position: 13,
        user_id: 14,
        full_name: "Илья Егоров",
        score: 51,
      },
      {
        position: 14,
        user_id: 15,
        full_name: "Яна Степанова",
        score: 50,
      },
      {
        position: 15,
        user_id: 16,
        full_name: "Максим Лебедев",
        score: 48,
      },
      {
        position: 16,
        user_id: 17,
        full_name: "Елена Грачева",
        score: 46,
      },
      {
        position: 17,
        user_id: 18,
        full_name: "Роман Козлов",
        score: 44,
      },
      {
        position: 18,
        user_id: 19,
        full_name: "Валерия Семенова",
        score: 42,
      },
      {
        position: 19,
        user_id: 20,
        full_name: "Георгий Мельников",
        score: 40,
      },
      {
        position: 20,
        user_id: 21,
        full_name: "Артем Белов",
        score: 38,
      },
    ],
  );
}
