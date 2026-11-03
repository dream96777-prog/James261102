import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { createPostAction } from "@/app/actions";
import { PostForm } from "@/components/post-form";
import { Card, CardContent } from "@/components/ui/card";
import { isAdmin } from "@/lib/session";

export const metadata: Metadata = { title: "글쓰기" };

export default function NewPostPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">글쓰기</h1>
      <Card>
        <CardContent>
          <Suspense
            fallback={
              <p className="text-sm text-muted-foreground">불러오는 중…</p>
            }
          >
            <NewPostForm />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}

async function NewPostForm() {
  if (!(await isAdmin())) redirect("/login");

  return (
    <PostForm action={createPostAction} submitLabel="등록" cancelHref="/" />
  );
}
