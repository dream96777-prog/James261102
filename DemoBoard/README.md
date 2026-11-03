# DemoBoard

Next.js, shadcn/ui, TypeScript로 만든 데모 게시판입니다. 글 목록, 상세, 작성, 수정, 삭제를 지원하고, 글은 Neon PostgreSQL에 저장합니다.

## 실행

1. 의존성을 설치합니다.

   ```bash
   npm install
   ```

2. `.env.example`을 `.env.local`로 복사하고 `DATABASE_URL`에 Neon 접속 문자열을, `ADMIN_PASSWORD`와 `SESSION_SECRET`에 각각 추측하기 어려운 값을 넣습니다. 둘 중 하나라도 없으면 로그인할 수 없습니다. `.env.local`은 Git에 포함되지 않으며, 배포할 때는 같은 변수를 Vercel 환경 변수에도 등록합니다.

3. 처음 한 번만 테이블을 만듭니다. `db/schema.sql`을 실행하며, 같은 이름의 테이블이 있으면 오류로 멈추고 기존 테이블은 건드리지 않습니다.

   ```bash
   npm run db:setup
   ```

4. 개발 서버를 실행하고 http://localhost:8100 을 엽니다.

   ```bash
   npm run dev -- --port 8100
   ```

## 권한

글은 누구나 읽을 수 있고, 작성·수정·삭제는 관리자 비밀번호로 로그인해야 합니다. 화면뿐 아니라 각 서버 액션에서도 로그인 쿠키를 검사합니다.

## 한계

- 관리자 계정이 하나뿐이라 글별 소유자가 없고, 작성자 이름도 직접 입력한 값 그대로입니다.
- 로그인 시도 횟수를 제한하지 않으므로 `ADMIN_PASSWORD`는 충분히 길게 정합니다.
- 검색과 페이지 나누기는 없어 목록에 모든 글을 한 번에 불러옵니다.
