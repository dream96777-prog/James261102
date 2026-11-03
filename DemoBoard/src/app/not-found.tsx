import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <h1 className="text-xl font-semibold tracking-tight">
        글을 찾을 수 없습니다
      </h1>
      <p className="text-sm text-muted-foreground">
        삭제되었거나 주소가 잘못된 글입니다.
      </p>
      <Link href="/" className={buttonVariants({ variant: "outline", size: "lg" })}>
        목록으로
      </Link>
    </div>
  );
}
