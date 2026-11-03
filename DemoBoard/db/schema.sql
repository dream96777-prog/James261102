-- 같은 이름의 테이블이 있으면 오류로 멈추고 기존 테이블은 건드리지 않는다.
CREATE TABLE posts (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(100) NOT NULL,
  author VARCHAR(30) NOT NULL,
  content VARCHAR(5000) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
