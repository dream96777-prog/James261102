import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatDate } from "@/lib/format";
import { listPosts } from "@/lib/posts";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">전체 글</h1>
      <Suspense
        fallback={<p className="text-sm text-muted-foreground">불러오는 중…</p>}
      >
        <PostList />
      </Suspense>
    </div>
  );
}

async function PostList() {
  await connection();
  const posts = await listPosts();

  if (posts.length === 0) {
    return (
      <Card className="items-center px-4 py-12 text-center">
        <p className="text-sm text-muted-foreground">
          아직 글이 없습니다. 첫 글을 작성해 보세요.
        </p>
      </Card>
    );
  }

  return (
    <Card className="gap-0 py-0">
      <ul className="divide-y">
        {posts.map((post) => (
          <li key={post.id}>
            <Link
              href={`/posts/${post.id}`}
              className="flex flex-col gap-1 px-4 py-3 transition-colors hover:bg-muted sm:flex-row sm:items-center sm:gap-4"
            >
              <span className="hidden w-8 shrink-0 text-sm text-muted-foreground tabular-nums sm:block">
                {post.id}
              </span>
              <span className="flex min-w-0 flex-1 items-center gap-2">
                <span className="truncate font-medium">{post.title}</span>
                {post.updatedAt !== post.createdAt && (
                  <Badge variant="secondary" className="shrink-0">
                    수정됨
                  </Badge>
                )}
              </span>
              <span className="flex shrink-0 gap-2 text-xs text-muted-foreground sm:text-sm">
                <span className="max-w-32 truncate">{post.author}</span>
                <span aria-hidden>·</span>
                <time dateTime={post.createdAt}>
                  {formatDate(post.createdAt)}
                </time>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
