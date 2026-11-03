import { ArrowLeftIcon, PencilIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";

import { DeletePostButton } from "@/components/delete-post-button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { formatDate } from "@/lib/format";
import { getPost } from "@/lib/posts";
import { parsePostId } from "@/lib/post-id";

export const metadata: Metadata = { title: "글 보기" };

export default function PostPage({ params }: PageProps<"/posts/[id]">) {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">불러오는 중…</p>}
    >
      <PostDetail params={params} />
    </Suspense>
  );
}

async function PostDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await connection();

  const postId = parsePostId(id);
  const post = postId === undefined ? undefined : await getPost(postId);
  if (!post) notFound();

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="gap-2 border-b">
          <h1 className="text-xl font-semibold tracking-tight wrap-anywhere">
            {post.title}
          </h1>
          <p className="flex flex-wrap gap-x-2 gap-y-1 text-sm text-muted-foreground">
            <span className="wrap-anywhere">{post.author}</span>
            <span aria-hidden>·</span>
            <time dateTime={post.createdAt}>{formatDate(post.createdAt)}</time>
            {post.updatedAt !== post.createdAt && (
              <span>(수정 {formatDate(post.updatedAt)})</span>
            )}
          </p>
        </CardHeader>
        <CardContent>
          <p className="min-h-32 whitespace-pre-wrap wrap-anywhere leading-relaxed">
            {post.content}
          </p>
        </CardContent>
      </Card>
      <div className="flex items-center justify-between gap-2">
        <Link
          href="/"
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          <ArrowLeftIcon />
          목록
        </Link>
        <div className="flex gap-2">
          <Link
            href={`/posts/${post.id}/edit`}
            className={buttonVariants({ variant: "outline", size: "lg" })}
          >
            <PencilIcon />
            수정
          </Link>
          <DeletePostButton id={post.id} />
        </div>
      </div>
    </div>
  );
}
