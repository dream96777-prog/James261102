import { neon } from "@neondatabase/serverless";

export type Post = {
  id: number;
  title: string;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
};

export type PostInput = Pick<Post, "title" | "author" | "content">;

type PostRow = {
  id: number;
  title: string;
  author: string;
  content: string;
  created_at: Date;
  updated_at: Date;
};

// 환경 변수가 없어도 빌드는 되도록 실제 쿼리 시점에 연결을 만든다.
function getSql() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL이 설정되어 있지 않습니다.");
  return neon(url);
}

function toPost(row: Record<string, unknown>): Post {
  const { id, title, author, content, created_at, updated_at } = row as PostRow;
  return {
    id,
    title,
    author,
    content,
    createdAt: created_at.toISOString(),
    updatedAt: updated_at.toISOString(),
  };
}

export async function listPosts(): Promise<Post[]> {
  const rows = await getSql()`SELECT * FROM posts ORDER BY id DESC`;
  return rows.map(toPost);
}

export async function getPost(id: number): Promise<Post | undefined> {
  const [row] = await getSql()`SELECT * FROM posts WHERE id = ${id}`;
  return row && toPost(row);
}

export async function createPost(input: PostInput): Promise<Post> {
  const [row] = await getSql()`
    INSERT INTO posts (title, author, content)
    VALUES (${input.title}, ${input.author}, ${input.content})
    RETURNING *`;
  return toPost(row);
}

export async function updatePost(
  id: number,
  input: PostInput,
): Promise<Post | undefined> {
  const [row] = await getSql()`
    UPDATE posts
    SET title = ${input.title},
        author = ${input.author},
        content = ${input.content},
        updated_at = now()
    WHERE id = ${id}
    RETURNING *`;
  return row && toPost(row);
}

export async function deletePost(id: number): Promise<void> {
  await getSql()`DELETE FROM posts WHERE id = ${id}`;
}
