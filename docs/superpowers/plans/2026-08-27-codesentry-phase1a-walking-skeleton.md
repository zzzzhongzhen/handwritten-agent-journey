# CodeSentry 一期地基 · 走通骨架(Phase 1a)实施计划

> **教学模式说明(重要,覆盖默认执行方式)**:本项目是学习作品,**学习关键代码由用户亲手写**,我给测试(TDD 靶子)+ 接口签名 + 审代码;胶水代码我搭骨架用户读懂。**不用 subagent 自动执行**——按模块结对写。步骤用 `- [ ]` 跟踪。
>
> **Spec:** `docs/superpowers/specs/2026-08-27-codesentry-design.md`

**目标:** 走通一条最薄的端到端线:给一个 bug 字符串 → 检索出 Swift repo 里最可疑的代码块并打印。用 NaiveChunker,不接 ClickUp,不做 Swift AST/评估/报告/投递(那些是后续计划)。

**架构:** 可插拔切块 → 遍历 repo 切块 → embed 存 Chroma → 查询定位。所有网络依赖(embed)通过参数注入,便于单测。

**技术栈:** Python 3.12 + uv、chromadb、openai(调 Kimi/硅基 embedding)、pytest、pathlib。

## 全局约束(每个任务都隐含遵守)

- Python **3.12+**,用 **uv** 管依赖(`uv add` / `uv run`)。
- 独立新仓 `~/Desktop/codesentry/`,个人号 zzzzhongzhen,SSH 别名 `github-personal`。
- `.gitignore` 必含:`.env`、`chroma_db/`、`data/`(任何 CoinEx 派生物绝不进 git)。
- embedding 走硅基 `BAAI/bge-m3`(`.env` 里 `SILICONFLOW_API_KEY`),和 40 号一致。
- 每个任务末尾 commit;测试放 `tests/`,`uv run pytest` 跑。

## 文件结构(本计划涉及)

```
codesentry/
├── pyproject.toml
├── .gitignore / .env(不提交)
├── src/codesentry/
│   ├── __init__.py
│   ├── config.py              读 .env / 常量
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── base.py            CodeChunk + CodeChunker 接口 + 注册表
│   │   ├── naive.py           NaiveChunker
│   │   └── walk.py            walk_repo(遍历文件)
│   └── retrieval/
│       ├── __init__.py
│       ├── embed.py           embed 函数(可注入)
│       └── locate.py          build_index + locate
├── scripts/triage_skeleton.py 命令行入口(骨架)
└── tests/
    ├── fixtures/              小 Swift 样例
    ├── test_naive_chunker.py
    ├── test_walk.py
    └── test_locate.py
```

---

### Task 1:建仓 + Python 项目骨架 🤝我带你建,你亲手敲每步

**Files:** Create `pyproject.toml`, `src/codesentry/__init__.py`, `.gitignore`, `tests/__init__.py`

**Produces:** 可 `import codesentry` 的空包 + git 仓。

- [ ] **Step 1:** `mkdir ~/Desktop/codesentry && cd` 进去,`git init`
- [ ] **Step 2:** `uv init --package`(生成 pyproject + src 布局),看懂它生成了什么(讲:包/模块/`__init__.py`/`[project]`)
- [ ] **Step 3:** 写 `.gitignore`(`.env`、`chroma_db/`、`data/`、`__pycache__/`、`.venv/`)
- [ ] **Step 4:** `uv add chromadb openai python-dotenv pytest`
- [ ] **Step 5:** 建 `tests/__init__.py`;`uv run python -c "import codesentry"` 应无报错
- [ ] **Step 6:** commit `chore: 初始化 codesentry 项目骨架`;建 GitHub 个人仓 + 推送

**学习点(用户):** Python 项目结构、包/模块/import、uv、gitignore 隐私铁律。

---

### Task 2:CodeChunk + CodeChunker 接口 ✍️你手写(核心设计码)

**Files:** Create `src/codesentry/chunking/base.py`, `tests/test_base.py`

**Produces:**
- `CodeChunk`(dataclass):`path,start_line,end_line,symbol,kind,parent,code,language`
- `CodeChunker`(Protocol):`chunk(self, source: str, path: str) -> list[CodeChunk]`

- [ ] **Step 1(我给测试):** 写 `tests/test_base.py`

```python
from codesentry.chunking.base import CodeChunk

def test_codechunk_holds_location_and_symbol():
    c = CodeChunk(path="A.swift", start_line=10, end_line=20,
                  symbol="foo()", kind="function", parent=None,
                  code="func foo() {}", language="swift")
    assert c.path == "A.swift" and c.start_line == 10
    assert c.symbol == "foo()"
```

- [ ] **Step 2:** `uv run pytest tests/test_base.py -v` → 应 FAIL(模块不存在)
- [ ] **Step 3(✍️你写):** 在 `base.py` 里用 `@dataclass` 定义 `CodeChunk`(8 个字段,类型注解),用 `typing.Protocol` 定义 `CodeChunker` 接口。**凭 spec 第 6 节写,别抄。**
- [ ] **Step 4:** 跑测试 → PASS
- [ ] **Step 5:** commit `feat(chunking): CodeChunk 数据结构 + CodeChunker 接口`

**学习点:** dataclass(≈struct)、Protocol(≈protocol)、"chunk 只吃字符串不读文件"的解耦。

---

### Task 3:NaiveChunker ✍️你手写(呼应 23 号切块)

**Files:** Create `src/codesentry/chunking/naive.py`, `tests/fixtures/Sample.swift`, `tests/test_naive_chunker.py`

**Consumes:** `CodeChunk`, `CodeChunker`(Task 2)
**Produces:** `NaiveChunker` 类,`chunk(source, path)` 按"函数/类"粗切(正则找 `func`/`class`/`struct` 起止)。找不到结构就整文件一块。

- [ ] **Step 1:** 建 fixture `tests/fixtures/Sample.swift`(含 2 个 func、1 个 class,行号清楚)
- [ ] **Step 2(我给测试):** 写 `tests/test_naive_chunker.py`

```python
from pathlib import Path
from codesentry.chunking.naive import NaiveChunker

def test_naive_splits_by_top_level_symbols():
    src = Path("tests/fixtures/Sample.swift").read_text(encoding="utf-8")
    chunks = NaiveChunker().chunk(src, "Sample.swift")
    assert len(chunks) >= 2
    assert all(c.path == "Sample.swift" for c in chunks)
    assert all(c.start_line >= 1 and c.end_line >= c.start_line for c in chunks)
    assert any("func" in c.code for c in chunks)
```

- [ ] **Step 3:** 跑 → FAIL
- [ ] **Step 4(✍️你写):** 实现 `NaiveChunker.chunk`——正则扫 `func/class/struct` 行作切点,记录 `start_line/end_line/symbol/kind`,兜底整文件一块。**回忆 23 号,但这次按代码结构。**
- [ ] **Step 5:** 跑 → PASS;自己再加一个"空文件/无函数"的边界测试并通过
- [ ] **Step 6:** commit `feat(chunking): NaiveChunker 基线切块`

**学习点:** 正则、行号计算、边界用例、"基线先跑通再上 AST"。

---

### Task 4:注册表 get_chunker ✍️你手写(呼应 14 号字典分发)

**Files:** Modify `src/codesentry/chunking/base.py`(加注册表);Test `tests/test_registry.py`

**Consumes:** `NaiveChunker`
**Produces:** `get_chunker(path: str) -> CodeChunker`——按后缀分发,骨架期一律回 `NaiveChunker`(Swift 实现后再加映射)。

- [ ] **Step 1(我给测试):**

```python
from codesentry.chunking.base import get_chunker
from codesentry.chunking.naive import NaiveChunker

def test_get_chunker_falls_back_to_naive():
    assert isinstance(get_chunker("x.swift"), NaiveChunker)
    assert isinstance(get_chunker("x.unknown"), NaiveChunker)
```

- [ ] **Step 2:** 跑 → FAIL
- [ ] **Step 3(✍️你写):** 实现 `get_chunker`(内部 dict `_REGISTRY`,`.get(suffix, NaiveChunker())`)
- [ ] **Step 4:** 跑 → PASS
- [ ] **Step 5:** commit `feat(chunking): 按后缀分发的 chunker 注册表`

**学习点:** 字典分发(=14 号 TOOL_FUNCTIONS)、可插拔落点。

---

### Task 5:walk_repo 遍历文件 ✍️你手写(学 pathlib / 文件 IO)

**Files:** Create `src/codesentry/chunking/walk.py`, `tests/test_walk.py`(用 fixture 目录)

**Produces:** `walk_repo(root: str, ext: str = ".swift") -> Iterator[tuple[str, str]]`——递归找匹配后缀的文件,yield `(相对路径, 文件内容)`,跳过其他文件。

- [ ] **Step 1:** 建 fixture 目录 `tests/fixtures/repo/`(放 2 个 `.swift` + 1 个 `.md`)
- [ ] **Step 2(我给测试):**

```python
from codesentry.chunking.walk import walk_repo

def test_walk_yields_only_swift():
    items = list(walk_repo("tests/fixtures/repo"))
    paths = {p for p, _ in items}
    assert len(items) == 2
    assert all(p.endswith(".swift") for p in paths)
    assert all(isinstance(src, str) and src for _, src in items)
```

- [ ] **Step 3:** 跑 → FAIL
- [ ] **Step 4(✍️你写):** 用 `pathlib.Path(root).rglob("*"+ext)` 遍历,`read_text(encoding="utf-8")` 读内容,yield。
- [ ] **Step 5:** 跑 → PASS
- [ ] **Step 6:** commit `feat(chunking): walk_repo 遍历 Swift 文件`

**学习点:** pathlib、`rglob`、生成器 yield、文件读(=07 号进阶)。

---

### Task 6:embed + build_index ✍️你写核心(呼应 40 号),🤝我搭注入骨架

**Files:** Create `src/codesentry/retrieval/embed.py`, `src/codesentry/retrieval/locate.py`(先写 build_index), `tests/test_index.py`, `src/codesentry/config.py`

**Consumes:** `CodeChunk`
**Produces:**
- `embed(text: str) -> list[float]`(调硅基 bge-m3;真网络)
- `build_index(chunks: list[CodeChunk], embed_fn, collection) -> None`——每块 embed 后 `collection.add(ids, embeddings, documents, metadatas)`,id=`f"{path}:{start_line}"`,metadata 存 path/行号/symbol。

- [ ] **Step 1:** `config.py` 读 `.env`(load_dotenv + `SILICONFLOW_API_KEY`);`.env` 填 key(不提交)
- [ ] **Step 2(我给测试,用假 embedder 避开网络):**

```python
import chromadb
from codesentry.chunking.base import CodeChunk
from codesentry.retrieval.locate import build_index

def _fake_embed(text): return [float(len(text)), 1.0, 0.0]  # 确定性假向量

def test_build_index_adds_all_chunks():
    col = chromadb.EphemeralClient().create_collection(
        "t", metadata={"hnsw:space": "cosine"})
    chunks = [CodeChunk("A.swift",1,3,"foo()","function",None,"func foo(){}","swift"),
              CodeChunk("B.swift",1,2,"bar()","function",None,"func bar(){}","swift")]
    build_index(chunks, _fake_embed, col)
    assert col.count() == 2
```

- [ ] **Step 3:** 跑 → FAIL
- [ ] **Step 4(✍️你写):** 实现 `build_index`(遍历 chunks、调 `embed_fn`、`collection.add`)。`embed.py` 里 `embed` 用 openai 客户端调硅基(=40 号)。**注意 embed_fn 是参数注入**——生产传真 embed,测试传假的。
- [ ] **Step 5:** 跑 → PASS(用假 embedder,不碰网络)
- [ ] **Step 6:** commit `feat(retrieval): embed + build_index(依赖注入便于测试)`

**学习点:** 依赖注入(可测性)、Chroma add、EphemeralClient 测试用、config/.env。

---

### Task 7:locate 定位 ✍️你手写(=40 号 rank_chroma 进化)

**Files:** Modify `src/codesentry/retrieval/locate.py`(加 locate);Test `tests/test_locate.py`

**Consumes:** `build_index`, `CodeChunk`
**Produces:** `locate(bug_text: str, collection, embed_fn, k: int = 5) -> list[dict]`——embed bug → `collection.query` → 返回 top-k 的 `{path, start_line, symbol, code, distance}`(按距离升序)。

- [ ] **Step 1(我给测试,假 embedder):**

```python
import chromadb
from codesentry.chunking.base import CodeChunk
from codesentry.retrieval.locate import build_index, locate

def _fake_embed(text):
    return [1.0, 0.0] if "refresh" in text.lower() else [0.0, 1.0]

def test_locate_ranks_relevant_first():
    col = chromadb.EphemeralClient().create_collection(
        "t", metadata={"hnsw:space": "cosine"})
    chunks = [CodeChunk("Refresh.swift",1,2,"refresh()","function",None,"func refresh(){}","swift"),
              CodeChunk("Other.swift",1,2,"other()","function",None,"func other(){}","swift")]
    build_index(chunks, _fake_embed, col)
    hits = locate("下拉 refresh 崩溃", col, _fake_embed, k=2)
    assert hits[0]["path"] == "Refresh.swift"
```

- [ ] **Step 2:** 跑 → FAIL
- [ ] **Step 3(✍️你写):** 实现 `locate`(embed → query → 组装结果 dict 列表)。回忆 40 号 `rank_chroma`,但这次返回结构化命中而非名次。
- [ ] **Step 4:** 跑 → PASS
- [ ] **Step 5:** commit `feat(retrieval): locate 代码定位查询`

**学习点:** query 返回结构([0] 剥 batch、distances)、结构化命中。

---

### Task 8:骨架命令行入口 🤝我搭骨架,你读懂 + 真机跑一次

**Files:** Create `scripts/triage_skeleton.py`

**Consumes:** `walk_repo`, `get_chunker`, `build_index`, `locate`, `embed`

- [ ] **Step 1(🤝我搭骨架):** `triage_skeleton.py` 串起来:`walk_repo(REPO_PATH)` → 每文件 `get_chunker(path).chunk(src, path)` 汇总 chunks → 建 PersistentClient collection → `build_index(chunks, embed, col)` → 对硬编码 bug 字符串 `locate(...)` → 打印 top-k `path:line symbol`。REPO_PATH 从 `.env` 读(指向 CoinEx 或先指向 fixtures/repo)。
- [ ] **Step 2(你读):** 逐行读懂这个入口在干嘛,能讲出每步调了哪个模块
- [ ] **Step 3:** 先指向 `tests/fixtures/repo` 跑通(小、快、不碰真库)
- [ ] **Step 4:** 再指向 CoinEx 真实库跑一次,看它对一个真实 bug 打印出哪些可疑文件(**第一次端到端见效!**)
- [ ] **Step 5:** commit `feat: 走通骨架——bug 字符串 → 可疑代码定位`

**学习点:** 入口/编排、PersistentClient 落盘、把学过的模块拼成一条线。

---

## 走通骨架完成 = 你有了什么

一个能跑的"给 bug → 出可疑 Swift 文件"最小系统(NaiveChunker + 向量检索),**全链路通、可单测**。**后续计划**依次加:SwiftChunker(AST)、双评估集 + Naive-vs-Swift 实验、ClickUp 接入、严重度 + 分诊报告生成、投递、生产硬化(退避/幂等/tracing)。

## 自审记录

- **Spec 覆盖**:本计划覆盖 spec 第 4(结构)、5A+5B前半(索引+定位)、6(接口)。评估(7)、报告/投递(5B后半)、硬化(8)、SwiftChunker 留后续计划——**有意分片,骨架先行**。
- **占位符**:无 TODO/TBD;测试均给完整代码;实现体标注"✍️你写"是教学设计(用户手写学习关键码),非占位。
- **类型一致**:`CodeChunk` 字段、`chunk(source,path)`、`build_index(chunks,embed_fn,collection)`、`locate(bug_text,collection,embed_fn,k)` 在各任务间签名一致。
