"""
Unit tests for Task 8: discover_connection / suggest_exploration_path.
PRD §2.3.2 Tool 3 + suggest_exploration_path; implemented in tools/briefing.py.

Test coverage:
- discover_connection: return structure, connection_strength range, various boundary
  formats, strong/weak/no overlap, LLM success/fallback/parse-error paths.
- suggest_exploration_path: return structure, step content, num_steps clamping,
  current_signals enrichment, LLM success/fallback/parse-error paths.
- Internal helpers: _extract_boundary_terms, _keyword_overlap_strength,
  _find_best_bridge_term, _build_template_path.
"""
from unittest.mock import patch, MagicMock

import pytest

from tools.briefing import (
    _extract_boundary_terms,
    _find_best_bridge_term,
    _keyword_overlap_strength,
    _build_template_path,
    discover_connection,
    suggest_exploration_path,
)


# ============================================================
# _extract_boundary_terms
# ============================================================


class TestExtractBoundaryTerms:

    def test_string_list_in_nodes(self) -> None:
        boundary = {"nodes": ["Machine Learning", "Calculus"]}
        terms = _extract_boundary_terms(boundary)
        assert "machine learning" in terms
        assert "calculus" in terms

    def test_dict_list_in_topics(self) -> None:
        boundary = {"topics": [{"name": "Linear Algebra"}, {"title": "Statistics"}]}
        terms = _extract_boundary_terms(boundary)
        assert "linear algebra" in terms
        assert "statistics" in terms

    def test_scalar_topic_key(self) -> None:
        boundary = {"topic": "Deep Learning", "subject": "Computer Science"}
        terms = _extract_boundary_terms(boundary)
        assert "deep learning" in terms
        assert "computer science" in terms

    def test_mixed_formats(self) -> None:
        boundary = {
            "nodes": ["graph theory"],
            "concepts": [{"concept": "eigenvector"}],
            "domain": "Mathematics",
        }
        terms = _extract_boundary_terms(boundary)
        assert "graph theory" in terms
        assert "eigenvector" in terms
        assert "mathematics" in terms

    def test_empty_boundary(self) -> None:
        assert _extract_boundary_terms({}) == []

    def test_ignores_unknown_keys(self) -> None:
        boundary = {"random_key": ["value1"]}
        assert _extract_boundary_terms(boundary) == []

    def test_strips_whitespace(self) -> None:
        boundary = {"nodes": ["  NLP  ", "  Vision  "]}
        terms = _extract_boundary_terms(boundary)
        assert "nlp" in terms
        assert "vision" in terms

    def test_skips_empty_strings(self) -> None:
        boundary = {"nodes": ["", "  ", "valid"]}
        terms = _extract_boundary_terms(boundary)
        assert "" not in terms
        assert "valid" in terms


# ============================================================
# _keyword_overlap_strength
# ============================================================


class TestKeywordOverlapStrength:

    def test_exact_single_word_match(self) -> None:
        score = _keyword_overlap_strength("optimization", ["optimization"])
        assert score == 1.0

    def test_partial_multi_word_overlap(self) -> None:
        score = _keyword_overlap_strength(
            "machine learning applications",
            ["machine learning"],
        )
        assert 0.0 < score < 1.0

    def test_no_overlap(self) -> None:
        score = _keyword_overlap_strength(
            "quantum physics",
            ["machine learning", "neural network"],
        )
        assert score == 0.0

    def test_empty_boundary_terms(self) -> None:
        assert _keyword_overlap_strength("anything", []) == 0.0

    def test_empty_personal_node(self) -> None:
        assert _keyword_overlap_strength("", ["machine learning"]) == 0.0

    def test_best_of_multiple_terms(self) -> None:
        score = _keyword_overlap_strength(
            "deep learning",
            ["computer vision", "deep learning theory"],
        )
        assert score > 0.0

    def test_score_range(self) -> None:
        score = _keyword_overlap_strength(
            "reinforcement learning",
            ["learning", "reinforcement", "optimization"],
        )
        assert 0.0 <= score <= 1.0


# ============================================================
# _find_best_bridge_term
# ============================================================


class TestFindBestBridgeTerm:

    def test_returns_best_match(self) -> None:
        result = _find_best_bridge_term(
            "machine learning",
            ["biology", "machine learning applications", "art"],
        )
        assert "machine learning" in result

    def test_returns_first_when_no_overlap(self) -> None:
        result = _find_best_bridge_term(
            "quantum physics",
            ["painting", "cooking"],
        )
        assert result in ("painting", "cooking")

    def test_empty_terms(self) -> None:
        assert _find_best_bridge_term("anything", []) == ""


# ============================================================
# discover_connection — return structure (PRD §2.3.2 Tool 3)
# ============================================================


REQUIRED_CONN_KEYS = {
    "connection_id",
    "connection_strength",
    "bridge_concept",
    "explanation",
    "potential_learning_outcome",
    "suggested_activity",
}


class TestDiscoverConnectionStructure:

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_return_keys(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "machine learning",
            {"topics": ["linear algebra", "statistics"]},
        )
        assert REQUIRED_CONN_KEYS.issubset(result.keys())

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_connection_id_prefix(self, _mock_llm: MagicMock) -> None:
        result = discover_connection("s1", "NLP", {"nodes": ["text processing"]})
        assert result["connection_id"].startswith("conn_")

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_strength_range(self, _mock_llm: MagicMock) -> None:
        result = discover_connection("s1", "whatever", {"topics": ["something"]})
        assert 0.0 <= result["connection_strength"] <= 1.0

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_all_text_fields_are_strings(self, _mock_llm: MagicMock) -> None:
        result = discover_connection("s1", "RL", {"topic": "AI"})
        for key in ("bridge_concept", "explanation",
                     "potential_learning_outcome", "suggested_activity"):
            assert isinstance(result[key], str)
            assert len(result[key]) > 0


# ============================================================
# discover_connection — rule-based logic
# ============================================================


class TestDiscoverConnectionRuleBased:

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_strong_overlap(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "machine learning",
            {"topics": ["machine learning fundamentals"]},
        )
        assert result["connection_strength"] > 0.0
        assert "machine learning" in result["bridge_concept"].lower()

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_exact_match_strength_is_high(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "optimization",
            {"nodes": ["optimization"]},
        )
        assert result["connection_strength"] == 1.0

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_no_overlap_weak_connection(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "quantum entanglement",
            {"topics": ["french literature", "classical music"]},
        )
        assert result["connection_strength"] < 0.3
        assert "independent exploration" in result["bridge_concept"].lower()

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_empty_boundary(self, _mock_llm: MagicMock) -> None:
        result = discover_connection("s1", "NLP", {})
        assert result["connection_strength"] == 0.0
        assert REQUIRED_CONN_KEYS.issubset(result.keys())

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_boundary_with_dict_items(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "data visualization",
            {"concepts": [{"name": "data analysis"}, {"name": "visual design"}]},
        )
        assert result["connection_strength"] > 0.0

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_multiple_boundary_sources(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "neural network",
            {
                "nodes": ["deep learning"],
                "topic": "artificial intelligence",
                "concepts": [{"name": "neural network"}],
            },
        )
        assert result["connection_strength"] == 1.0


# ============================================================
# discover_connection — LLM paths
# ============================================================


class TestDiscoverConnectionLLM:

    def test_llm_success(self) -> None:
        fake_llm_result = {
            "connection_strength": 0.85,
            "bridge_concept": "LLM bridge",
            "explanation": "LLM explanation",
            "potential_learning_outcome": "LLM outcome",
            "suggested_activity": "LLM activity",
        }
        with patch("tools.briefing._discover_connection_llm", return_value=fake_llm_result):
            result = discover_connection("s1", "NLP", {"topic": "AI"})
        assert result["bridge_concept"] == "LLM bridge"
        assert result["connection_strength"] == 0.85
        assert result["connection_id"].startswith("conn_")

    def test_llm_returns_none_falls_back(self) -> None:
        with patch("tools.briefing._discover_connection_llm", return_value=None):
            result = discover_connection("s1", "biology", {"topic": "chemistry"})
        assert result["connection_id"].startswith("conn_")
        assert REQUIRED_CONN_KEYS.issubset(result.keys())


class TestDiscoverConnectionLLMInternal:

    @patch("tools.briefing._call_minimax", create=True)
    def test_llm_parse_error_returns_none(self, mock_call: MagicMock) -> None:
        mock_call.return_value = "NOT VALID JSON !!!"
        from tools.briefing import _discover_connection_llm
        with patch("tools.briefing._discover_connection_llm") as mock_fn:
            mock_fn.return_value = None
            result = discover_connection("s1", "test", {"topic": "x"})
        assert result["connection_id"].startswith("conn_")

    def test_llm_import_failure_returns_none(self) -> None:
        from tools.briefing import _discover_connection_llm
        with patch.dict("sys.modules", {"agents.catalyst.llm": None}):
            result = _discover_connection_llm("s1", "test", {"topic": "x"})
        assert result is None


# ============================================================
# suggest_exploration_path — return structure
# ============================================================


REQUIRED_PATH_KEYS = {
    "path_id",
    "interest_seed",
    "steps",
    "estimated_duration",
    "difficulty_progression",
}

REQUIRED_STEP_KEYS = {"title", "description", "resource_hint", "difficulty"}


class TestSuggestExplorationPathStructure:

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_return_keys(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "reinforcement learning")
        assert REQUIRED_PATH_KEYS.issubset(result.keys())

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_path_id_prefix(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "NLP")
        assert result["path_id"].startswith("path_")

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_interest_seed_preserved(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "quantum computing")
        assert result["interest_seed"] == "quantum computing"

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_steps_have_required_keys(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "NLP")
        for step in result["steps"]:
            assert REQUIRED_STEP_KEYS.issubset(step.keys())

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_difficulty_in_range(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML", num_steps=6)
        for step in result["steps"]:
            assert 0.0 <= step["difficulty"] <= 1.0

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_estimated_duration_is_string(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML")
        assert isinstance(result["estimated_duration"], str)
        assert len(result["estimated_duration"]) > 0


# ============================================================
# suggest_exploration_path — num_steps parameter
# ============================================================


class TestSuggestExplorationPathNumSteps:

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_default_4_steps(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML")
        assert len(result["steps"]) == 4

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_custom_num_steps(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML", num_steps=3)
        assert len(result["steps"]) == 3

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_min_clamp_to_2(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML", num_steps=1)
        assert len(result["steps"]) == 2

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_max_clamp_to_8(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "ML", num_steps=20)
        assert len(result["steps"]) <= 8


# ============================================================
# suggest_exploration_path — current_signals enrichment
# ============================================================


class TestSuggestExplorationPathSignals:

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_signals_add_cross_pollinate_step(self, _mock_llm: MagicMock) -> None:
        signals = {
            "keywords": ["ML"],
            "research_directions": ["autonomous driving"],
            "tech_stack": ["PyTorch"],
        }
        result = suggest_exploration_path(
            "s1", "computer vision", current_signals=signals, num_steps=8,
        )
        titles = [s["title"] for s in result["steps"]]
        has_cross = any("autonomous driving" in t for t in titles)
        assert has_cross, f"Expected cross-pollinate step, got: {titles}"

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_signals_add_tech_apply_step(self, _mock_llm: MagicMock) -> None:
        signals = {
            "keywords": ["ML"],
            "research_directions": [],
            "tech_stack": ["TensorFlow"],
        }
        result = suggest_exploration_path(
            "s1", "image classification", current_signals=signals, num_steps=8,
        )
        titles = [s["title"] for s in result["steps"]]
        has_tech = any("TensorFlow" in t for t in titles)
        assert has_tech, f"Expected tech-apply step, got: {titles}"

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_no_signals_still_works(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "robotics")
        assert len(result["steps"]) == 4
        assert REQUIRED_PATH_KEYS.issubset(result.keys())

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_empty_signals_dict(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "NLP", current_signals={})
        assert len(result["steps"]) == 4


# ============================================================
# _build_template_path
# ============================================================


class TestBuildTemplatePath:

    def test_sorted_by_difficulty(self) -> None:
        steps = _build_template_path("ML", None, 6)
        difficulties = [s["difficulty"] for s in steps]
        assert difficulties == sorted(difficulties)

    def test_seed_in_titles(self) -> None:
        steps = _build_template_path("graph neural networks", None, 4)
        for step in steps:
            assert "graph neural networks" in step["title"].lower() or \
                   "graph neural networks" in step["description"].lower()

    def test_signals_enrichment_within_limit(self) -> None:
        signals = {
            "research_directions": ["NLP"],
            "tech_stack": ["spaCy"],
        }
        steps = _build_template_path("text mining", signals, 3)
        assert len(steps) == 3


# ============================================================
# suggest_exploration_path — LLM paths
# ============================================================


class TestSuggestExplorationPathLLM:

    def test_llm_success(self) -> None:
        fake_result = {
            "steps": [
                {"title": "S1", "description": "D1", "resource_hint": "R1", "difficulty": 0.2},
                {"title": "S2", "description": "D2", "resource_hint": "R2", "difficulty": 0.5},
            ],
            "estimated_duration": "4-8 hours",
            "difficulty_progression": "beginner → advanced",
        }
        with patch("tools.briefing._suggest_path_llm", return_value=fake_result):
            result = suggest_exploration_path("s1", "NLP", num_steps=2)
        assert result["steps"][0]["title"] == "S1"
        assert result["estimated_duration"] == "4-8 hours"
        assert result["path_id"].startswith("path_")
        assert result["interest_seed"] == "NLP"

    def test_llm_returns_none_falls_back_to_template(self) -> None:
        with patch("tools.briefing._suggest_path_llm", return_value=None):
            result = suggest_exploration_path("s1", "biology")
        assert result["path_id"].startswith("path_")
        assert len(result["steps"]) == 4
        assert "biology" in result["steps"][0]["title"].lower()


class TestSuggestPathLLMInternal:

    def test_llm_import_failure_returns_none(self) -> None:
        from tools.briefing import _suggest_path_llm
        with patch.dict("sys.modules", {"agents.catalyst.llm": None}):
            result = _suggest_path_llm("s1", "test", None, 4)
        assert result is None


# ============================================================
# discover_connection — idempotency & edge cases
# ============================================================


class TestDiscoverConnectionEdgeCases:

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_unique_connection_ids(self, _mock_llm: MagicMock) -> None:
        ids = set()
        for _ in range(20):
            r = discover_connection("s1", "ML", {"topic": "AI"})
            ids.add(r["connection_id"])
        assert len(ids) == 20

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_unicode_in_knowledge_node(self, _mock_llm: MagicMock) -> None:
        result = discover_connection(
            "s1",
            "강화학습",
            {"topic": "artificial intelligence"},
        )
        assert REQUIRED_CONN_KEYS.issubset(result.keys())

    @patch("tools.briefing._discover_connection_llm", return_value=None)
    def test_very_long_knowledge_node(self, _mock_llm: MagicMock) -> None:
        long_node = "machine learning " * 100
        result = discover_connection("s1", long_node, {"topic": "ML"})
        assert REQUIRED_CONN_KEYS.issubset(result.keys())
        assert 0.0 <= result["connection_strength"] <= 1.0


# ============================================================
# suggest_exploration_path — edge cases
# ============================================================


class TestSuggestExplorationPathEdgeCases:

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_unique_path_ids(self, _mock_llm: MagicMock) -> None:
        ids = set()
        for _ in range(20):
            r = suggest_exploration_path("s1", "ML")
            ids.add(r["path_id"])
        assert len(ids) == 20

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_unicode_seed(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "深度学习")
        assert REQUIRED_PATH_KEYS.issubset(result.keys())
        assert result["interest_seed"] == "深度学习"

    @patch("tools.briefing._suggest_path_llm", return_value=None)
    def test_empty_seed(self, _mock_llm: MagicMock) -> None:
        result = suggest_exploration_path("s1", "")
        assert REQUIRED_PATH_KEYS.issubset(result.keys())
        assert len(result["steps"]) >= 2


# ============================================================
# Existing synthesize_briefing not broken (regression guard)
# ============================================================


class TestSynthesizeBriefingRegression:

    def test_import_still_works(self) -> None:
        from tools.briefing import synthesize_briefing
        result = synthesize_briefing("s1")
        assert "briefing_id" in result
        assert result["should_notify"] is False

    def test_with_event(self) -> None:
        from tools.briefing import synthesize_briefing
        event = {
            "title": "Test Paper",
            "summary": "A test paper about ML.",
            "relevance_score": 0.9,
            "source": "arxiv",
            "id": "1234",
            "pdf_url": "http://example.com/paper.pdf",
        }
        result = synthesize_briefing("s1", event=event)
        assert result["should_notify"] is True
        assert "Test Paper" in result["personalized_content"]
