export type Player = { id: string; name: string; score: number };
export type Show = {
  room_id: string;
  revision: number;
  you: string;
  players: Player[];
  phase: string;
  index: number;
  total: number;
  hints: string[];
  hint_count: number;
  revealed: number;
  points: number;
  wrong_penalty: number;
  active: string | null;
  locked: string[];
  deadline: number | null;
  paused: boolean;
  remaining: number | null;
  answer?: string;
  all_hints?: string[];
  submission?: string | null;
  invites?: string[];
  can_undo?: boolean;
  online: string[];
  server_time: number;
  last_result: {
    player: string;
    correct: boolean;
    points: number;
    reason: string;
  } | null;
};
export type Room = { id: string; names: string[]; phase: string };

export type ShowMode = "host" | "play" | "show";
export type Act = (
  action: string,
  payload?: Record<string, unknown>,
) => Promise<void>;
