// Typed API client for the Agon backend (mirrors contracts/openapi.yaml).

export type Role = "REVIEWER" | "ADMIN";
export type ReviewStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
export type ResultStatus = "SUCCESS" | "FAILED";

export interface User {
  id: string;
  username: string;
  role: Role;
}

export interface Review {
  id: string;
  submission_id: string;
  reviewer_id: string;
  status: ReviewStatus;
  final_grade: number | null;
}

export interface ReviewSummary extends Review {
  candidate_label: string;
  created_at: string;
}

export interface TestResult {
  test_id: string;
  test_name: string;
  grade: number;
  status: ResultStatus;
  effective_weight: number;
  contribution: number;
  pros: string[];
  cons: string[];
}

export interface ReviewDetail extends ReviewSummary {
  results: TestResult[];
  pros: string[];
  cons: string[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return (await res.json()) as T;
}

export async function login(username: string, password: string): Promise<User> {
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    credentials: "include",
  });
  return handle<User>(res);
}

export async function uploadSubmission(
  candidateLabel: string,
  archive: File,
): Promise<Review> {
  const form = new FormData();
  form.append("candidate_label", candidateLabel);
  form.append("archive", archive);
  const res = await fetch("/submissions", {
    method: "POST",
    body: form,
    credentials: "include",
  });
  return handle<Review>(res);
}

export async function getReview(reviewId: string): Promise<ReviewDetail> {
  const res = await fetch(`/reviews/${reviewId}`, { credentials: "include" });
  return handle<ReviewDetail>(res);
}

export async function listReviews(): Promise<ReviewSummary[]> {
  const res = await fetch("/reviews", { credentials: "include" });
  return handle<ReviewSummary[]>(res);
}

export interface TestConfig {
  id: string;
  key: string;
  name: string;
  type: "METRIC" | "AI_AGENT";
  theme: string | null;
  enabled: boolean;
  default_weight: number;
}

export interface WeightOverride {
  test_id: string;
  weight: number;
}

export async function updateWeights(
  reviewId: string,
  overrides: WeightOverride[],
): Promise<ReviewDetail> {
  const res = await fetch(`/reviews/${reviewId}/weights`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overrides }),
    credentials: "include",
  });
  return handle<ReviewDetail>(res);
}

export async function listTests(): Promise<TestConfig[]> {
  const res = await fetch("/tests", { credentials: "include" });
  return handle<TestConfig[]>(res);
}

export async function updateTestConfig(
  testId: string,
  patch: { enabled?: boolean; default_weight?: number },
): Promise<TestConfig> {
  const res = await fetch(`/admin/tests/${testId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
    credentials: "include",
  });
  return handle<TestConfig>(res);
}

export async function listUsers(): Promise<User[]> {
  const res = await fetch("/admin/users", { credentials: "include" });
  return handle<User[]>(res);
}

export async function createUser(
  username: string,
  password: string,
  role: Role,
): Promise<User> {
  const res = await fetch("/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role }),
    credentials: "include",
  });
  return handle<User>(res);
}

export async function updateUserRole(userId: string, role: Role): Promise<User> {
  const res = await fetch(`/admin/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
    credentials: "include",
  });
  return handle<User>(res);
}
