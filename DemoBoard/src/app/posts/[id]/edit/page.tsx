import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";

import { updatePostAction } from "@/app/actions";
import { PostForm } from "@/components/post-form";
import { Card, CardContent } from "@/components/ui/card";
import { getPost } from "@/lib/posts";
import { parsePostId } from "@/lib/post-id";
import { isAdmin } from "@/lib/session";

export const metadata: Metadata = { title: "글 수정" };

export default function EditPostPage({
  params,
}: PageProps<"/posts/[id]/edit">) {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">글 수정</h1>
      <Card>
        <CardContent>
          <Suspense
            fallback={
              <p className="text-sm text-muted-foreground">불러오는 중…</p>
            }
          >
            <EditForm params={params} />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}

async function EditForm({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await connection();
  if (!(await isAdmin())) redirect("/login");

  const postId = parsePostId(id);
  const post = postId === undefined ? undefined : await getPost(postId);
  if (!post) notFound();

  return (
    <PostForm
      action={updatePostAction.bind(null, post.id)}
      initialValues={{
        title: post.title,
        author: post.author,
        content: post.content,
      }}
      submitLabel="저장"
      cancelHref={`/posts/${post.id}`}
    />
  );
}
