import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { LoginForm } from "@/components/login-form";
import { Card, CardContent } from "@/components/ui/card";
import { isAdmin } from "@/lib/session";

export const metadata: Metadata = { title: "로그인" };

export default function LoginPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">로그인</h1>
      <Card>
        <CardContent>
          <Suspense
            fallback={
              <p className="text-sm text-muted-foreground">불러오는 중…</p>
            }
          >
            <LoginGate />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}

async function LoginGate() {
  if (await isAdmin()) redirect("/");
  return <LoginForm />;
}
