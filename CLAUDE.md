# CLAUDE.md

## 프로젝트 개요

**text-dedup**은 메모리 효율적인 텍스트 중복 제거 도구이다. 텍스트를 SHA1 해시로 인코딩하고, 해시 프리픽스 기반으로 샤드 파일에 분할 저장한 뒤, 샤드별로 중복을 제거하고 병합한다.

- 라이선스: Apache 2.0
- 작성자: lovit
- 주요 의존성: `tqdm` (유일한 외부 패키지)

## 디렉터리 구조

```
text-dedup/
├── text_dedup/
│   ├── __init__.py       # __version__ export (importlib.metadata)
│   ├── cli.py            # CLI 진입점 (argparse 기반)
│   └── encoder.py        # 핵심 로직 (Normalizer, Encoder, task_*)
├── pyproject.toml        # 빌드 설정 + ruff 설정
├── .pre-commit-config.yaml # pre-commit 훅 설정
├── uv.lock               # uv 의존성 잠금 파일
├── README.md
└── LICENSE
```

## 핵심 모듈

### `encoder.py` — 핵심 비즈니스 로직

| 클래스/함수 | 역할 |
|---|---|
| `Normalizer` | 정규식 기반 텍스트 정규화 (기본: 숫자+한글+영문만 유지) |
| `Encoder` | Normalizer + 해시 함수로 텍스트 인코딩 |
| `encode_a_file()` | 단일 파일을 읽어 인코딩 후 샤드에 저장 |
| `task_encode()` | 여러 입력 파일/디렉터리에 대한 인코딩 오케스트레이션 |
| `task_merge()` | 샤드 파일에서 중복 제거 후 출력 파일로 병합 |
| `task_dedup()` | 최상위 오케스트레이터 (encode → merge → cleanup) |
| `save_shards()` | 해시 프리픽스 기반으로 샤드 파일에 분할 저장 |
| `get_shard_path()` | 프리픽스에서 샤드 파일 경로 생성 (예: `shard/12/34.shard`) |
| `humanized_to_number()` | 사람이 읽기 쉬운 크기 파싱 (10k, 100.5mb, 4.5gb) |

### `cli.py` — CLI 진입점

`text-dedup` 콘솔 스크립트. `task_dedup()`에 argparse 인자를 전달한다.

## 설치 및 실행

```bash
# 설치
git clone https://github.com/lovit/text-dedup.git
cd text-dedup
uv sync

# 실행
uv run text-dedup \
  --inputs path/to/textfile \
  --shard path/to/shard-directory \
  --output path/to/deduplicated.text \
  --prefix_length 4
```

### 주요 CLI 인자

| 인자 | 기본값 | 설명 |
|---|---|---|
| `-i, --inputs` | (필수) | 입력 텍스트 파일 경로 (복수 가능) |
| `-s, --shard_root` | (필수) | 샤드 디렉터리 경로 |
| `-o, --output` | (필수) | 중복 제거 결과 파일 경로 |
| `-f, --hash_func_type` | `sha1` | 해시 함수 |
| `-r, --hash_func_input_format` | `0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z` | 정규화 패턴 |
| `-p, --n_processes` | `cpu_count - 1` | 멀티프로세싱 워커 수 |
| `-c, --chunksize` | `100000` | 배치 청크 크기 |
| `-b, --max_block_size` | `None` | 출력 블록 최대 크기 (예: 10Mb) |
| `-pr, --prefix_length` | `4` | 샤드 프리픽스 길이 |
| `-t, --sort` | `False` | 샤드 내 정렬 (`--keep` 필요) |
| `-k, --keep` | `False` | 샤드 파일 유지 |

## 빌드 시스템

- `pyproject.toml` + `hatchling` 빌드 백엔드
- `uv`로 패키지 관리 (`uv sync`, `uv run`)
- 버전은 `pyproject.toml`에서 관리, 런타임에서는 `importlib.metadata`로 접근
- 콘솔 스크립트: `text-dedup=text_dedup.cli:main`

## 코드 컨벤션

- **네이밍**: snake_case (함수/변수), PascalCase (클래스)
- **Type hints**: Python 3.12 내장 문법 사용 (`list`, `X | Y`)
- **인코딩**: 모든 파일 I/O에 `encoding="utf-8"` 명시
- **멀티프로세싱**: `multiprocessing.Pool`과 `imap` 사용
- **오케스트레이션 함수**: `task_` 프리픽스 (예: `task_encode`, `task_merge`, `task_dedup`)
- **CJK 지원**: 기본 정규화 패턴에 한글 범위 포함

## 린터 및 포매터

- `ruff` 사용 (lint + format)
- 규칙: `E`, `F`, `I` (isort), `UP` (pyupgrade)
- `pre-commit`으로 커밋 시 자동 실행

```bash
uv run ruff check .        # 린트
uv run ruff format .       # 포맷
uv run pre-commit install  # 훅 설치
```

## 테스트

현재 테스트 파일 없음. 테스트 추가 시 `pytest` 사용 권장.

## CI/CD

현재 CI/CD 설정 없음.

## 작업 시 참고사항

- 이 패키지는 대용량 텍스트 처리를 목적으로 하므로, 메모리 효율성에 유의할 것
- `os.popen("wc -l ...")` 등 셸 명령어 호출이 있으므로 Linux/macOS 환경 전제
- 샤드 정리 시 `os.system("rm -r ...")` 사용 — 크로스 플랫폼 호환에 주의
