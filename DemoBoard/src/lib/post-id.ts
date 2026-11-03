// posts.id는 PostgreSQL INTEGER이므로 범위를 넘는 값은 쿼리 오류 대신 없는 글로 처리한다.
const MAX_POST_ID = 2_147_483_647;

export function parsePostId(value: string): number | undefined {
  if (!/^[1-9]\d*$/.test(value)) return undefined;
  const id = Number(value);
  return id <= MAX_POST_ID ? id : undefined;
}
