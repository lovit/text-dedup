# Commit Rules

## Conventional Commit 형식

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Type

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `refactor`: 기능 변경 없는 코드 구조 개선
- `test`: 테스트 추가 또는 수정
- `docs`: 문서 변경
- `style`: 포맷팅, 세미콜론 등 코드 의미에 영향 없는 변경
- `chore`: 빌드, 패키지 매니저 설정 등 기타 변경
- `perf`: 성능 개선

## Scope (선택)

변경 대상 모듈명 사용: `encoder`, `cli`, `about`

여러 모듈에 걸친 변경이면 scope 생략 가능.

## Subject (제목)

- 한글로 작성
- 명사형 종결 사용 (예: "추가", "수정", "삭제", "변환", "개선")
- 50자 이내
- 끝에 마침표 없음

## Body (본문)

- 한글로 작성
- 변경 이유와 내용을 설명
- 변경된 파일이 많으면 bullet list(`-`)로 정리
- 빈 줄로 subject와 구분

## 커밋 단위

- 논리적으로 독립된 변경 단위로 분리
- 하나의 커밋에 서로 다른 목적의 변경을 섞지 않음
- 예: import 컨벤션 수정, type hints 추가, 테스트 추가는 각각 별도 커밋

## 예시

```
refactor(encoder): Normalizer 클래스 정규식 패턴 캐싱 추가

- 매 호출마다 re.compile 호출 제거
- __init__에서 한 번만 컴파일하도록 변경

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

```
feat(cli): 출력 포맷 선택 옵션 추가

- --format 인자로 text, jsonl 선택 가능
- 기본값은 text 유지

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

```
test: encoder 모듈 단위 테스트 추가

- Normalizer, Encoder, humanized_to_number 테스트
- pytest 기반

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
