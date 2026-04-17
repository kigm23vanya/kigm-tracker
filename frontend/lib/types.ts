export type LeaderboardScope = "group" | "course" | "college";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: "student" | "curator" | "admin" | "teacher";
  group_id: number | null;
  course_number: number;
  avatar_url: string | null;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthSession {
  user_id: number;
  email: string;
  full_name: string;
  access_token: string;
}

export interface EventItem {
  id: number;
  title: string;
  description: string | null;
  starts_at: string;
  location: string | null;
  organizer: string | null;
  activity_points: number;
  subject_id?: number | null;
  subject_name?: string | null;
}

export interface AssignmentCard {
  id: number;
  course_title: string;
  assignment_title: string;
  assignment_description: string | null;
  due_date: string | null;
  max_points: number | null;
  submission_state: string | null;
  draft_grade: number | null;
  assigned_grade: number | null;
  comment: string | null;
}

export interface ProfileSummary {
  user: User;
  title: string;
  phone: string | null;
  total_achievements: number;
  activity_points: number;
  experience: {
    experience: number;
    level: number | null;
    progress_percent: number;
    current_level_xp: number;
    next_level_xp: number | null;
    infinite: boolean;
  };
  teacher_profile: {
    curator_group: string | null;
    work_experience_years: number;
    organized_events: EventItem[];
  } | null;
}

export interface AchievementRecord {
  id: number;
  awarded_at: string;
  reason: string | null;
  achievement: {
    id: number;
    title: string;
    description: string;
    rarity: "common" | "rare" | "epic" | "legendary";
  };
}

export interface SubjectGrade {
  subject_name: string;
  final_grade: number | null;
  average_grade: number | null;
  completed_assignments: number;
}

export interface ProfileEvent {
  id: number;
  event_id: number;
  event_title: string;
  date: string;
  participation_status: "none" | "registered" | "participated";
  result: string | null;
  points_awarded: number;
}

export interface LeaderboardEntry {
  position: number;
  user_id: number;
  full_name: string;
  score: number;
}
