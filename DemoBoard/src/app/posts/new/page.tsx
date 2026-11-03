import type { Metadata } from "next";

import { createPostAction } from "@/app/actions";
import { PostForm } from "@/components/post-form";
import { Card, CardContent } from "@/components/ui/card";

export const metadata: Metadata = { title: "글쓰기" };

export default function NewPostPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">글쓰기</h1>
      <Card>
        <CardContent>
          <PostForm
            action={createPostAction}
            submitLabel="등록"
            cancelHref="/"
          />
        </CardContent>
      </Card>
    </div>
  );
}
