# gd_posts

Turn any **topic** into a polished blog post using a small **LangGraph**
workflow with three stages:

1. **Researcher** — runs Gemini Deep Research on the topic and returns a
   structured, citation-rich report that becomes the `source_content`.
2. **Writer** — drafts a Markdown post from the research report.
3. **Judge** — reviews the draft and returns a structured `JudgeFeedback`
   (`approved`, `score`, `feedback`).

If the judge approves, the post is printed. Otherwise the draft is sent back
to the writer with the feedback, up to `MAX_ITERATIONS` times (default
**3**). After the final round the last draft is returned along with the
rejection feedback.

```text
   ┌────────────┐    ┌──────────┐    ┌──────────┐
 ──│ researcher ├───►│  writer  ├───►│  judge   ├── approve / give_up ──► finalize ──► END
   └────────────┘    └──────────┘    └──────────┘
                          ▲                 │
                          │                 │
                          └──── rewrite ────┘
```

The three LLMs are configured **independently** through environment
variables, so you can mix providers freely (e.g. Deep Research from Google,
a strong writer on Ollama Cloud, a cheap judge on Gemini Flash).

## Stack

- [LangGraph](https://langchain-ai.github.io/langgraph/) for the
  researcher/writer/judge control flow.
- [Pydantic](https://docs.pydantic.dev/) for the workflow state and the
  structured judge response.
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
  for environment-driven configuration.
- LangChain provider integrations for Gemini, OpenAI, and Ollama
  (incl. Ollama Cloud) for the writer/judge.
- [`google-genai`](https://github.com/googleapis/python-genai) Interactions
  API for the Deep Research agent.

## Project layout

```text
gd_posts/
├── prompts/
│   ├── research.txt      # Instructions for the Deep Research agent
│   ├── writer.txt        # System prompt for the writer LLM
│   └── judge.txt         # System prompt for the judge LLM
├── src/
│   ├── config.py         # Pydantic settings (WRITER__* / JUDGE__* / RESEARCH__*)
│   ├── llm.py            # Factory: provider → LangChain chat model
│   ├── researcher.py     # Deep Research client + LangGraph node
│   ├── state.py          # PostState + JudgeFeedback Pydantic models
│   ├── nodes.py          # writer / judge / finalize / decide_next
│   ├── graph.py          # LangGraph wiring
│   └── main.py           # CLI entry point
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your API keys
```

## Configuration

Settings are loaded from the environment (or a local `.env`) via
`pydantic-settings`. The writer, judge, and research agent are configured
independently using the `WRITER__*` / `JUDGE__*` / `RESEARCH__*`
nested-env-var convention:

| Variable                    | Description                                       |
| --------------------------- | ------------------------------------------------- |
| `WRITER__PROVIDER`          | `google_genai` \| `openai` \| `ollama` \| `ollama_cloud` |
| `WRITER__MODEL`             | Model name for the chosen provider                |
| `WRITER__API_KEY`           | API key (optional if provider reads its own env)  |
| `WRITER__BASE_URL`          | Override host (OpenAI-compatible / self-hosted)   |
| `WRITER__TEMPERATURE`       | Sampling temperature (default `0.8`)              |
| `JUDGE__*`                  | Same fields, used for the judge LLM               |
| `RESEARCH__AGENT`           | Deep Research agent id (default `deep-research-pro-preview-12-2025`) |
| `RESEARCH__API_KEY`         | Gemini key. Falls back to `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| `RESEARCH__POLL_INTERVAL_S` | Polling interval while research is in flight (default `5.0`) |
| `RESEARCH__MAX_WAIT_S`      | Hard timeout for a research run (default `1800`)  |
| `MAX_ITERATIONS`            | Max writer/judge rounds (default `3`, max `10`)   |

### Switching writer / judge providers

You only need to change a few env vars. Examples:

**Gemini (default)**
```dotenv
WRITER__PROVIDER=google_genai
WRITER__MODEL=gemini-2.0-flash
WRITER__API_KEY=AIza...
```

**OpenAI**
```dotenv
WRITER__PROVIDER=openai
WRITER__MODEL=gpt-4o-mini
WRITER__API_KEY=sk-...
```

**Ollama Cloud** — uses `https://ollama.com` and sends the API key as a Bearer
token via the underlying `ollama` client headers:
```dotenv
WRITER__PROVIDER=ollama_cloud
WRITER__MODEL=gpt-oss:120b-cloud
WRITER__API_KEY=your-ollama-cloud-key
```

**Local Ollama**
```dotenv
WRITER__PROVIDER=ollama
WRITER__MODEL=llama3.1
WRITER__BASE_URL=http://localhost:11434
```

**Any OpenAI-compatible API** (vLLM, LM Studio, Together AI, etc.):
```dotenv
WRITER__PROVIDER=openai
WRITER__MODEL=meta-llama/Llama-3.1-70B-Instruct
WRITER__BASE_URL=https://api.together.xyz/v1
WRITER__API_KEY=your-key
```

You can also mix and match — e.g. a powerful writer on Ollama Cloud and a
fast, cheap Gemini judge:
```dotenv
WRITER__PROVIDER=ollama_cloud
WRITER__MODEL=gpt-oss:120b-cloud
WRITER__API_KEY=your-ollama-cloud-key

JUDGE__PROVIDER=google_genai
JUDGE__MODEL=gemini-2.0-flash
JUDGE__API_KEY=AIza...
```

### Adding another provider

Open `src/llm.py` and add a new branch in `make_llm`. The factory only needs
to return any `BaseChatModel` — the rest of the workflow is provider-agnostic.

## Usage

```bash
python -m src.main "history of Google TPUs"
```

Write the result to a file instead of stdout:

```bash
python -m src.main "history of Google TPUs" -o post.md
```

Save the raw Deep Research report alongside the post:

```bash
python -m src.main "history of Google TPUs" -o post.md --save-report report.md
```

Override the iteration cap for a single run:

```bash
python -m src.main "history of Google TPUs" --max-iterations 5
```

The CLI prints the configuration, Deep Research progress, and the final
score / feedback on `stderr`, and the post itself on `stdout` (or to `-o` if
specified). This makes it easy to pipe the output:

```bash
python -m src.main "history of Google TPUs" > post.md
```

## Deep Research notes

- The agent (`deep-research-pro-preview-12-2025` by default) is reached via
  the `google-genai` Interactions API. It runs in the background and the
  researcher node polls until completion.
- A typical research run takes **several minutes**. There is no on-disk
  cache: every invocation starts a fresh research interaction. Use
  `--save-report` if you want to keep a copy of the report from a run.
- Use `RESEARCH__MAX_WAIT_S` to bound a single run; the node raises a
  `TimeoutError` if the agent has not completed by then.
- The agent's output format is shaped by [`prompts/research.txt`](prompts/research.txt).
  Edit it to change the structure of the report (sections, depth, citation
  style).

## How the loop works

- `researcher` reads `state.topic`, combines it with `prompts/research.txt`,
  starts a Deep Research interaction, polls until completion, and writes the
  resulting Markdown report into `state.source_content`.
- `writer` reads the source content, the previous draft, and **all prior
  reviewer feedback**, and produces the next Markdown draft.
- `judge` evaluates the draft against the source and returns a strict
  `JudgeFeedback` via `with_structured_output(JudgeFeedback)`.
- `decide_next` routes to `finalize` (approval), `finalize` (max rounds
  reached), or back to `writer` (rewrite).
- `finalize` copies the current draft into `final_post` and the graph ends.

The full feedback history is passed back to the writer on every rewrite, so
the model has full context on what has already been criticised.
