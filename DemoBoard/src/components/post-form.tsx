"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useActionState } from "react";

import type { PostFormState } from "@/app/actions";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { PostInput } from "@/lib/posts";

type PostFormProps = {
  action: (state: PostFormState, formData: FormData) => Promise<PostFormState>;
  initialValues?: PostInput;
  submitLabel: string;
  cancelHref: string;
};

// 화면을 떠났다가 링크로 다시 들어오면 이전 입력값이 남지 않도록 새 폼으로 시작한다.
export function PostForm(props: PostFormProps) {
  const { bfcacheId } = useRouter();
  return <PostFormFields key={bfcacheId} {...props} />;
}

function PostFormFields({
  action,
  initialValues,
  submitLabel,
  cancelHref,
}: PostFormProps) {
  const [state, formAction, pending] = useActionState(action, {});
  const values = state.values ?? initialValues;

  return (
    <form action={formAction} className="flex flex-col gap-5">
      <Field id="title" label="제목" error={state.errors?.title}>
        <Input
          id="title"
          name="title"
          defaultValue={values?.title}
          maxLength={100}
          required
          aria-invalid={Boolean(state.errors?.title)}
          placeholder="제목을 입력하세요"
          className="h-10"
        />
      </Field>
      <Field id="author" label="작성자" error={state.errors?.author}>
        <Input
          id="author"
          name="author"
          defaultValue={values?.author}
          maxLength={30}
          required
          aria-invalid={Boolean(state.errors?.author)}
          placeholder="이름을 입력하세요"
          className="h-10 sm:max-w-60"
        />
      </Field>
      <Field id="content" label="내용" error={state.errors?.content}>
        <Textarea
          id="content"
          name="content"
          defaultValue={values?.content}
          maxLength={5000}
          required
          aria-invalid={Boolean(state.errors?.content)}
          placeholder="내용을 입력하세요"
          className="min-h-64"
        />
      </Field>

      {state.message && (
        <p role="alert" className="text-sm text-destructive">
          {state.message}
        </p>
      )}

      <div className="flex justify-end gap-2">
        <Link
          href={cancelHref}
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          취소
        </Link>
        <Button type="submit" size="lg" disabled={pending}>
          {pending ? "저장 중…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}

function Field({
  id,
  label,
  error,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
