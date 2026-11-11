"""Loader tests: a valid suite, each SPEC §3.3 error line, multi-doc files, tags, scorer names."""

import sys
import textwrap
from pathlib import Path

import pytest

from casegate.errors import SuiteError
from casegate.loader import load_suite
from casegate.scorers import REGISTRY

FAKE = Path(__file__).parent / "fixtures" / "suite_fake"

SUITE = """\
name: s
target: {type: python, path: tests.fixtures.suite_fake.target:run, version: v1, model: none}
"""

EXACT_CASE = """\
id: {id}
tags: [{tags}]
input: {{reply: OK}}
expected: {{answer: OK}}
scorers: [{{type: exact}}]
"""


def make_suite(root: Path, suite: str = SUITE, **case_files: str) -> Path:
    """Write suite.yaml and cases/<name>.yaml files; keys use '_' for '-' in file names."""
    (root / "cases").mkdir(parents=True, exist_ok=True)
    (root / "suite.yaml").write_text(suite, encoding="utf-8")
    for name, text in case_files.items():
        (root / "cases" / f"{name.replace('_', '-')}.yaml").write_text(
            textwrap.dedent(text), encoding="utf-8"
        )
    return root


def errors_of(path: Path, tags: list[str] | None = None) -> list[str]:
    with pytest.raises(SuiteError) as info:
        load_suite(path, tags)
    return info.value.errors


def known() -> str:
    return ", ".join(sorted(REGISTRY))


# --- valid suites -------------------------------------------------------------------------


def test_suite_fake_loads_in_file_order() -> None:
    suite, cases = load_suite(FAKE, None)
    assert suite.name == "suite-fake"
    assert suite.root == str(FAKE.resolve())
    assert suite.target.version == "fake@1"
    assert suite.concurrency == 4
    assert suite.retries.attempts == 2
    assert suite.retries.backoff_s == [0.01]
    assert suite.must_pass_tags == ["core"]
    assert [c.id for c in cases] == [
        "pass-exact-01",
        "fail-contains-02",
        "retry-once-03",
        "tools-state-04",
    ]
    assert cases[0].source_file == "cases/01-pass-exact-01.yaml"
    assert [s.name for s in cases[3].scorers] == ["tool_trajectory", "state_match"]


def test_multi_doc_file_keeps_document_order(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        b_two=EXACT_CASE.format(id="b1", tags="x") + "---\n" + EXACT_CASE.format(id="b2", tags=""),
        a_one=EXACT_CASE.format(id="a1", tags="") + "---\n",  # a trailing empty document
    )
    _, cases = load_suite(tmp_path, None)
    assert [(c.id, c.source_file) for c in cases] == [
        ("a1", "cases/a-one.yaml"),
        ("b1", "cases/b-two.yaml"),
        ("b2", "cases/b-two.yaml"),
    ]


def test_tag_filter_keeps_cases_with_any_tag() -> None:
    _, cases = load_suite(FAKE, ["retry", "tools"])
    assert [c.id for c in cases] == ["retry-once-03", "tools-state-04"]


def test_no_cases_match_tags() -> None:
    assert errors_of(FAKE, ["nope", "none"]) == ["no cases match tags: nope, none"]


def test_unnamed_scorers_are_numbered_per_type(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        c1="""\
        id: c1
        input: {}
        expected: {answer: OK, answer_contains: [OK]}
        scorers: [{type: exact}, {type: contains}, {type: exact}, {type: exact, name: strict}]
        """,
    )
    _, cases = load_suite(tmp_path, None)
    assert [s.name for s in cases[0].scorers] == ["exact", "contains", "exact#2", "strict"]


def test_cases_glob_from_suite(tmp_path: Path) -> None:
    make_suite(tmp_path, SUITE + "cases: more/*.yml\n")
    (tmp_path / "more").mkdir()
    (tmp_path / "more" / "x.yml").write_text(EXACT_CASE.format(id="x", tags=""), encoding="utf-8")
    _, cases = load_suite(tmp_path, None)
    assert [c.source_file for c in cases] == ["more/x.yml"]


# --- suite.yaml errors ------------------------------------------------------------------------


def test_suite_yaml_not_found(tmp_path: Path) -> None:
    assert errors_of(tmp_path) == [f"suite.yaml: not found: {tmp_path / 'suite.yaml'}"]


def test_suite_yaml_cannot_parse(tmp_path: Path) -> None:
    make_suite(tmp_path, "name: [unclosed\n")
    (line,) = errors_of(tmp_path)
    assert line.startswith("suite.yaml: cannot parse: ")
    assert "\n" not in line


def test_suite_yaml_not_a_mapping(tmp_path: Path) -> None:
    make_suite(tmp_path, "- a\n- b\n")
    assert errors_of(tmp_path) == ["suite.yaml: cannot parse: top level must be a mapping"]


def test_suite_missing_version_and_model(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        "name: s\ntarget: {type: python, path: tests.fixtures.suite_fake.target:run}\n",
        c=EXACT_CASE.format(id="c", tags=""),
    )
    assert errors_of(tmp_path) == [
        "suite.yaml: target.version: Field required",
        "suite.yaml: target.model: Field required",
    ]


def test_python_target_without_path(tmp_path: Path) -> None:
    make_suite(tmp_path, "name: s\ntarget: {type: python, version: v, model: none}\n")
    assert errors_of(tmp_path) == [
        "suite.yaml: target: Value error, target.path is required for type python "
        r"and must match ^[\w.]+:\w+$",
        "no case files match cases/*.yaml",
    ]


def test_invalid_suite_still_reports_case_errors(tmp_path: Path) -> None:
    make_suite(tmp_path, "name: s\nconcurrency: 0\n" + SUITE.split("\n", 1)[1], c="id: c\n")
    errs = errors_of(tmp_path)
    assert errs[0] == "suite.yaml: concurrency: Input should be greater than or equal to 1"
    assert "cases/c.yaml case 0: input: Field required" in errs


# --- case errors --------------------------------------------------------------------------------


def test_no_case_files(tmp_path: Path) -> None:
    make_suite(tmp_path)
    assert errors_of(tmp_path) == ["no case files match cases/*.yaml"]


def test_case_file_cannot_parse(tmp_path: Path) -> None:
    make_suite(tmp_path, bad="id: [oops\n", ok=EXACT_CASE.format(id="ok", tags=""))
    (line,) = errors_of(tmp_path)
    assert line.startswith("cases/bad.yaml: cannot parse: ")


def test_case_validation_names_file_and_index(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        multi=EXACT_CASE.format(id="ok", tags="")
        + "---\nid: Bad Id\ninput: {}\nscorers: []\nextra_key: 1\n"
        + "---\n- not a mapping\n",
    )
    errs = errors_of(tmp_path)
    assert errs[0] == (
        "cases/multi.yaml case 1: id: String should match pattern '^[a-z0-9][a-z0-9._-]{0,79}$'"
    )
    assert (
        "cases/multi.yaml case 1: scorers: List should have at least 1 item after validation, not 0"
        in errs
    )
    assert "cases/multi.yaml case 1: extra_key: Extra inputs are not permitted" in errs
    assert errs[-1].startswith("cases/multi.yaml case 2: Input should be a valid dictionary")


def test_scorer_threshold_out_of_range(tmp_path: Path) -> None:
    make_suite(
        tmp_path, c=EXACT_CASE.format(id="c", tags="").replace("exact}", "exact, threshold: 2}")
    )
    assert errors_of(tmp_path) == [
        "cases/c.yaml case 0: scorers.0.threshold: Input should be less than or equal to 1"
    ]


def test_duplicate_case_id(tmp_path: Path) -> None:
    make_suite(
        tmp_path, a=EXACT_CASE.format(id="dup", tags=""), b=EXACT_CASE.format(id="dup", tags="")
    )
    assert errors_of(tmp_path) == ["duplicate case id dup: cases/a.yaml, cases/b.yaml"]


def test_unknown_scorer_type_skips_build_scorers(tmp_path: Path) -> None:
    # The exact scorer here has no answer; build_scorers would report it, but is not called.
    make_suite(
        tmp_path,
        c="""\
        id: c
        input: {}
        scorers: [{type: exact}, {type: bogus}, {type: llm_judgy}]
        """,
    )
    assert errors_of(tmp_path) == [
        f"cases/c.yaml case 0: unknown scorer type bogus (known: {known()})",
        f"cases/c.yaml case 0: unknown scorer type llm_judgy (known: {known()})",
    ]


def test_unknown_type_line_names_the_full_registry() -> None:
    # From M2 the judge scorers are known types too (SPEC §17).
    assert known() == (
        "citation_support, contains, exact, json_schema, llm_judge, not_contains, state_match, "
        "tool_trajectory"
    )


# --- scorer errors from build_scorers (prefix added there, bodies from check()) -------------


def test_missing_required_inputs(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        c="""\
        id: c
        input: {}
        scorers: [{type: exact}, {type: contains}, {type: not_contains}, {type: state_match},
                  {type: tool_trajectory}, {type: json_schema}]
        """,
    )
    assert errors_of(tmp_path) == [
        "case c scorer exact: exact: needs answer or expected.answer",
        "case c scorer contains: contains: needs items or expected.answer_contains",
        "case c scorer not_contains: not_contains: needs items or expected.answer_not_contains",
        "case c scorer state_match: state_match: needs non-empty state or expected.state",
        "case c scorer tool_trajectory: tool_trajectory: needs tools, forbidden, "
        "expected.tools or expected.tools_forbidden",
        "case c scorer json_schema: json_schema: needs schema, schema_path or expected.schema",
    ]


def test_params_and_expected_errors(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        c="""\
        id: c
        input: {}
        expected: {answer: 42, answer_contains: []}
        scorers:
          - {type: exact}
          - {type: contains}
          - {type: not_contains, items: [x], bogus: 1}
          - {type: json_schema, schema: {type: object}, schema_path: s.json}
        """,
    )
    assert errors_of(tmp_path) == [
        "case c scorer exact: expected.answer: Input should be a valid string",
        "case c scorer exact: expected.answer: Input should be a valid list",
        "case c scorer contains: contains: expected.answer_contains must not be empty",
        "case c scorer not_contains: bogus: Extra inputs are not permitted",
        "case c scorer json_schema: json_schema: schema and schema_path are mutually exclusive",
    ]


def test_matcher_and_path_errors(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        c="""\
        id: c
        input: {}
        expected:
          tools: [{name: refund, args: {amount: {regex: "("}}}]
          state: {"a..b": 1, total: {all_amounts_lte: true}}
        scorers: [{type: tool_trajectory}, {type: state_match}]
        """,
    )
    assert errors_of(tmp_path) == [
        "case c scorer tool_trajectory: tool_trajectory: refund.amount: "
        "invalid regex: missing ), unterminated subpattern at position 0",
        'case c scorer state_match: state_match: malformed path "a..b"',
        "case c scorer state_match: state_match: total: all_amounts_lte must be a number",
    ]


def test_duplicate_scorer_name(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        c=EXACT_CASE.format(id="c", tags="").replace(
            "[{type: exact}]", "[{type: exact}, {type: exact, name: exact}]"
        ),
    )
    assert errors_of(tmp_path) == ["case c: duplicate scorer name exact"]


def test_errors_from_several_files_are_collected(tmp_path: Path) -> None:
    make_suite(
        tmp_path,
        a="id: a\ninput: {}\nscorers: [{type: exact}]\n",
        b="id: b\ninput: {}\nscorers: [{type: nope}]\n",
        c="id: C\ninput: {}\nscorers: [{type: exact}]\n",
    )
    errs = errors_of(tmp_path)
    assert len(errs) == 3
    assert errs[0] == "case a scorer exact: exact: needs answer or expected.answer"
    assert errs[1].startswith("cases/b.yaml case 0: unknown scorer type nope")
    assert errs[2].startswith("cases/c.yaml case 0: id: String should match pattern")


# --- target errors from build_target (lines unchanged) --------------------------------------


@pytest.fixture
def isolated_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Run from tmp_path with a sys.path copy, so the loader's cwd insert does not leak."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _target_suite(root: Path, target_path: str) -> Path:
    suite = SUITE.replace("tests.fixtures.suite_fake.target:run", target_path)
    return make_suite(root / "suite", suite, c=EXACT_CASE.format(id="c", tags=""))


def test_target_module_from_cwd(isolated_path: Path) -> None:
    (isolated_path / "cg_loader_mod_ok.py").write_text(
        "async def run(case_input):\n    return {'text': 'OK'}\n", encoding="utf-8"
    )
    suite, _ = load_suite(_target_suite(isolated_path, "cg_loader_mod_ok:run"), None)
    assert sys.path[0] == str(isolated_path)
    assert suite.target.path == "cg_loader_mod_ok:run"


def test_target_cannot_import(isolated_path: Path) -> None:
    errs = errors_of(_target_suite(isolated_path, "cg_loader_no_such_mod:run"))
    assert errs == [
        "target.path: cannot import cg_loader_no_such_mod: ModuleNotFoundError: "
        "No module named 'cg_loader_no_such_mod'"
    ]


def test_target_missing_function_and_sync(isolated_path: Path) -> None:
    (isolated_path / "cg_loader_mod_sync.py").write_text(
        "def run(case_input):\n    return {'text': 'OK'}\n", encoding="utf-8"
    )
    assert errors_of(_target_suite(isolated_path, "cg_loader_mod_sync:missing")) == [
        "target.path: cg_loader_mod_sync has no attribute missing"
    ]
    assert errors_of(_target_suite(isolated_path, "cg_loader_mod_sync:run")) == [
        "target.path: cg_loader_mod_sync:run must be an async function"
    ]


def test_http_target_missing_header_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CG_LOADER_TOKEN", raising=False)
    suite = (
        "name: s\ntarget:\n  type: http\n  url: http://localhost:1/run\n  version: v\n"
        "  model: none\n  headers: {Authorization: 'Bearer ${CG_LOADER_TOKEN}'}\n"
    )
    make_suite(tmp_path, suite, c=EXACT_CASE.format(id="c", tags=""))
    assert errors_of(tmp_path) == [
        "target.headers.Authorization: environment variable CG_LOADER_TOKEN is not set"
    ]
    monkeypatch.setenv("CG_LOADER_TOKEN", "t")
    loaded, _ = load_suite(tmp_path, None)
    assert loaded.target.type == "http"


def test_all_error_kinds_in_one_raise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "path", list(sys.path))
    make_suite(
        tmp_path,
        SUITE.replace("tests.fixtures.suite_fake.target:run", "cg_loader_absent_mod:run"),
        a=EXACT_CASE.format(id="a", tags=""),
        b=EXACT_CASE.format(id="a", tags=""),
        c="id: c\ninput: {}\nscorers: [{type: nope}]\n",
    )
    with pytest.raises(SuiteError) as info:
        load_suite(tmp_path, None)
    text = str(info.value)
    assert "duplicate case id a: cases/a.yaml, cases/b.yaml" in text
    assert "unknown scorer type nope" in text
    assert "target.path: cannot import cg_loader_absent_mod" in text
    assert text == "\n".join(info.value.errors)
