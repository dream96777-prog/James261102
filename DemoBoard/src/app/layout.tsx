import { PencilLineIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "DemoBoard", template: "%s | DemoBoard" },
  description: "Next.js와 shadcn/ui로 만든 데모 게시판",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-muted/40">
        <header className="sticky top-0 z-10 border-b bg-background">
          <div className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between px-4">
            <Link href="/" className="text-base font-semibold tracking-tight">
              DemoBoard
            </Link>
            <Link href="/posts/new" className={buttonVariants({ size: "lg" })}>
              <PencilLineIcon />
              글쓰기
            </Link>
          </div>
        </header>
        <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6 sm:py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
