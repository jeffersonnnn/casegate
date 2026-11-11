# 0007 Design direction A, "Lab instrument"

Status: accepted (2026-11-11)

## Context
casegate has no app screens. Its visible surfaces are the terminal, the Markdown report, the PR comment, the README, a one-page site, the logo and two videos. Three live options were built and shown in the browser (`docs/design/options/`): A "Lab instrument" (dark, one signal colour, IBM Plex), B "Traffic gate" (amber hazard stripes, Archivo Black capitals), C "Paper report" (cream paper, Source Serif).

## Decision
Use A. The full token set and rules are in `docs/DESIGN.md`.

## Why
A fits the product's claim, "measure, do not guess": it reads as an instrument, and the tick row (one tick per case, red where a case flipped) shows the gate's job in one image. B is louder but its hazard stripes compete with the red/green status signal. C reads well but a light theme fights the dark terminal that the videos are built around.

## Consequences
All assets (terminal theme, site, logo renders, banner, videos) use the A tokens. Changing direction later means re-rendering every asset.
