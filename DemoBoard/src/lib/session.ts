import "server-only";

import { createHash, createHmac, timingSafeEqual } from "node:crypto";

import { cookies } from "next/headers";
import { connection } from "next/server";

const COOKIE_NAME = "demoboard_session";
const SESSION_MS = 7 * 24 * 60 * 60 * 1000;

// 길이가 달라도 비교할 수 있도록 해시한 뒤 일정한 시간에 비교한다.
function safeEqual(a: string, b: string): boolean {
  const hash = (value: string) => createHash("sha256").update(value).digest();
  return timingSafeEqual(hash(a), hash(b));
}

function sign(expiresAt: number, secret: string): string {
  return createHmac("sha256", secret).update(String(expiresAt)).digest("hex");
}

// 환경 변수가 없으면 아무도 통과하지 못하게 막는다.
export function verifyAdminPassword(password: string): boolean {
  const expected = process.env.ADMIN_PASSWORD;
  return Boolean(expected) && safeEqual(password, expected as string);
}

export async function createSession(): Promise<void> {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error("SESSION_SECRET이 설정되어 있지 않습니다.");

  const expiresAt = Date.now() + SESSION_MS;
  (await cookies()).set(COOKIE_NAME, `${expiresAt}.${sign(expiresAt, secret)}`, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    expires: new Date(expiresAt),
    path: "/",
  });
}

export async function deleteSession(): Promise<void> {
  (await cookies()).delete(COOKIE_NAME);
}

export async function isAdmin(): Promise<boolean> {
  // 만료 확인에 현재 시각을 쓰므로 요청 시점에 실행되도록 한다.
  await connection();

  const secret = process.env.SESSION_SECRET;
  const token = (await cookies()).get(COOKIE_NAME)?.value;
  if (!secret || !token) return false;

  const [expiresAt, signature] = token.split(".");
  return (
    signature !== undefined &&
    Number(expiresAt) > Date.now() &&
    safeEqual(signature, sign(Number(expiresAt), secret))
  );
}
