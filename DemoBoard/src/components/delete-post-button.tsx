"use client";

import { Trash2Icon } from "lucide-react";
import { useLayoutEffect, useState } from "react";
import { useFormStatus } from "react-dom";

import { deletePostAction } from "@/app/actions";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

export function DeletePostButton({ id }: { id: number }) {
  const [open, setOpen] = useState(false);

  // 화면이 숨겨져도 상태가 유지되므로, 돌아왔을 때 대화상자가 열려 있지 않게 닫는다.
  useLayoutEffect(() => () => setOpen(false), []);

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger
        render={<Button variant="destructive" size="lg" />}
      >
        <Trash2Icon />
        삭제
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>이 글을 삭제할까요?</AlertDialogTitle>
          <AlertDialogDescription>
            삭제한 글은 되돌릴 수 없습니다.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <form action={deletePostAction.bind(null, id)}>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <ConfirmDeleteButton />
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function ConfirmDeleteButton() {
  const { pending } = useFormStatus();
  return (
    <AlertDialogAction type="submit" variant="destructive" disabled={pending}>
      {pending ? "삭제 중…" : "삭제"}
    </AlertDialogAction>
  );
}
