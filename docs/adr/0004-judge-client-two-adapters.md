# 0004 A small JudgeClient with two adapters, no litellm

Status: accepted (2026-11-11)

## Context
`llm_judge` and `citation_support` call a model. The judge should be a different model from the target where possible. Options: Anthropic only, a provider router such as litellm, or a small interface of our own.

## Decision
Define a `JudgeClient` protocol with two adapters: Anthropic (structured output via `client.messages.parse` / `output_config.format`, no sampling fields) and any OpenAI-compatible endpoint (JSON schema response format, `temperature: 0` when the endpoint accepts it). The judge model comes from an environment variable that `suite.yaml` names.

## Why
Two adapters cover Anthropic, OpenAI, OpenRouter and local servers. litellm is a large dependency and makes the library harder to read in one sitting.

## Consequences
Other providers need a new adapter (about 60 lines). The `anthropic` SDK is an optional extra; the OpenAI-compatible adapter uses `httpx` only.

## Amendment (2026-11-11, from FACTS)
The brief asked for "temperature 0". On the Anthropic API version `2026-10-21`, any request that sends `temperature`, `top_p` or `top_k` returns a 400 on every model, and Claude Sonnet 5.5 and Opus 5.5 also reject forced `tool_choice`. So the Anthropic adapter sends no sampling field and uses structured outputs. Judge determinism is then measured, not assumed: `calibrate` and `--repeat` report judge variance. The README states this.
