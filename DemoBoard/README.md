# DemoBoard

Next.js, shadcn/ui, TypeScript로 만든 데모 게시판입니다. 글 목록, 상세, 작성, 수정, 삭제를 지원하고, 글은 Neon PostgreSQL에 저장합니다.

## 실행

1. 의존성을 설치합니다.

   ```bash
   npm install
   ```

2. `.env.example`을 `.env.local`로 복사하고 `DATABASE_URL`에 Neon 접속 문자열을 넣습니다. `.env.local`은 Git에 포함되지 않습니다.

3. 처음 한 번만 테이블을 만듭니다. `db/schema.sql`을 실행하며, 같은 이름의 테이블이 있으면 오류로 멈추고 기존 테이블은 건드리지 않습니다.

   ```bash
   npm run db:setup
   ```

4. 개발 서버를 실행하고 http://localhost:8100 을 엽니다.

   ```bash
   npm run dev -- --port 8100
   ```

## 한계

- 로그인이 없어 누구나 모든 글을 수정·삭제할 수 있고, 작성자 이름도 직접 입력한 값 그대로입니다.
- 검색과 페이지 나누기는 없어 목록에 모든 글을 한 번에 불러옵니다.
