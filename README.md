# bfcl-eval

Evaluation-only package for [Berkeley Function Calling Leaderboard (BFCL)](https://gorilla.cs.berkeley.edu/leaderboard.html).

This is a lightweight, pip-installable package extracted from the [upstream BFCL repository](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) that focuses solely on **scoring model outputs** — no inference, no API calls, just evaluation.

## Installation

```bash
pip install git+https://github.com/bzantium/bfcl-eval.git
```

Or for local development:

```bash
git clone https://github.com/bzantium/bfcl-eval.git
cd bfcl-eval
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
python -m bfcl_eval \
  --model <model_name> \
  --test-category <category> \
  --result-dir /path/to/model/results \
  --score-dir /path/to/output/scores
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | *(required)* | Model name(s) to evaluate (repeatable) |
| `--test-category` | `all` | Test category(ies) to evaluate (repeatable) |
| `--result-dir` | `None` | Path to model response folder |
| `--score-dir` | `None` | Path to evaluation score output folder |
| `--partial-eval` | `False` | Evaluate on a partial set of benchmark entries |
| `--is-fc / --no-fc` | `True` | Whether results use function-calling format |
| `--underscore-to-dot / --no-underscore-to-dot` | `True` | Convert `.` to `_` in function names |

### Test Categories

The package includes benchmark data for the following categories:

- **Simple**: Single function call (Python, Java, JavaScript)
- **Multiple**: Select one function from several candidates
- **Parallel**: Multiple function calls from a single query
- **Parallel Multiple**: Combination of parallel and multiple
- **Relevance / Irrelevance**: Detect whether provided functions are relevant
- **Multi-Turn**: Multi-step and multi-turn function calling (base, missing func, missing param, long context)
- **Agentic**: Web search and memory management scenarios
- **Format Sensitivity**: Robustness to prompt format variations

### Input Format

Model results should be in JSONL format, with each line containing:

```json
{"id": "...", "result": "..."}
```

The `id` field must match the corresponding benchmark entry IDs.

## Evaluation Methods

- **AST Evaluation**: Compares the abstract syntax tree of generated function calls against ground truth
- **Multi-Turn Evaluation**: Executes multi-turn conversations and validates state/outputs at each step
- **Agentic Evaluation**: Evaluates web search and memory management capabilities

## Acknowledgements

Based on the [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) by UC Berkeley. See the [upstream repository](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) for full details.

```bibtex
@misc{berkeley-function-calling-leaderboard,
  title={Berkeley Function Calling Leaderboard},
  author={Fanjia Yan and Huanzhi Mao and Charlie Cheng-Jie Ji and Tianjun Zhang and Shishir G. Patil and Ion Stoica and Joseph E. Gonzalez},
  howpublished={\url{https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html}},
  year={2024},
}
```
