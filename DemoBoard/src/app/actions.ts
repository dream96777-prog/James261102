"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import * as posts from "@/lib/posts";
import type { PostInput } from "@/lib/posts";

export type PostFormState = {
  values?: PostInput;
  errors?: Partial<Record<keyof PostInput, string>>;
  message?: string;
};

const LIMITS = { title: 100, author: 30, content: 5000 } as const;

function parseForm(formData: FormData): {
  values: PostInput;
  errors: PostFormState["errors"];
} {
  const read = (name: keyof PostInput) =>
    String(formData.get(name) ?? "")
      .replace(/\r\n/g, "\n")
      .trim();
  const values = {
    title: read("title"),
    author: read("author"),
    content: read("content"),
  };

  const errors: PostFormState["errors"] = {};
  if (!values.title) errors.title = "제목을 입력해 주세요.";
  else if (values.title.length > LIMITS.title)
    errors.title = `제목은 ${LIMITS.title}자 이내로 입력해 주세요.`;

  if (!values.author) errors.author = "작성자를 입력해 주세요.";
  else if (values.author.length > LIMITS.author)
    errors.author = `작성자는 ${LIMITS.author}자 이내로 입력해 주세요.`;

  if (!values.content) errors.content = "내용을 입력해 주세요.";
  else if (values.content.length > LIMITS.content)
    errors.content = `내용은 ${LIMITS.content.toLocaleString()}자 이내로 입력해 주세요.`;

  return { values, errors };
}

export async function createPostAction(
  _prev: PostFormState,
  formData: FormData,
): Promise<PostFormState> {
  const { values, errors } = parseForm(formData);
  if (errors && Object.keys(errors).length > 0) return { values, errors };

  const post = await posts.createPost(values);
  revalidatePath("/", "layout");
  redirect(`/posts/${post.id}`);
}

export async function updatePostAction(
  id: number,
  _prev: PostFormState,
  formData: FormData,
): Promise<PostFormState> {
  const { values, errors } = parseForm(formData);
  if (errors && Object.keys(errors).length > 0) return { values, errors };

  const post = await posts.updatePost(id, values);
  if (!post) return { values, message: "이미 삭제된 글입니다." };

  revalidatePath("/", "layout");
  redirect(`/posts/${id}`);
}

export async function deletePostAction(id: number) {
  await posts.deletePost(id);
  revalidatePath("/", "layout");
  redirect("/");
}
