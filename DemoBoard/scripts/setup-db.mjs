import { readFile } from "node:fs/promises";

import { neon } from "@neondatabase/serverless";

const sql = neon(process.env.DATABASE_URL);
const schema = await readFile(new URL("../db/schema.sql", import.meta.url), "utf8");

try {
  await sql.query(schema);
  console.log("posts 테이블을 만들었습니다.");
} catch (error) {
  // 드라이버 오류 객체에 접속 정보가 섞이지 않도록 메시지만 출력한다.
  console.error(`테이블을 만들지 못했습니다: ${error.message}`);
  process.exitCode = 1;
}
