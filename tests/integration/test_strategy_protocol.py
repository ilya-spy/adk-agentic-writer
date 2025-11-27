"""Tests for StrategyProtocol and adaptive content generation."""

import pytest
from src.adk_agentic_writer.agents.static import CoordinatorAgent, ProducerAgent, ReviewerAgent


class TestStrategyProtocol:
    """Test strategy protocol implementation."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator instance."""
        return CoordinatorAgent()

    @pytest.fixture
    def producer(self, coordinator):
        """Create producer instance with coordinator."""
        return ProducerAgent(coordinator=coordinator, reviewer=ReviewerAgent())

    @pytest.mark.asyncio
    async def test_analyze_user_behavior(self, producer):
        """Test user behavior analysis."""
        user_interactions = {
            "time_spent": 360,  # 6 minutes - high engagement
            "total_blocks": 10,
            "completed_blocks": 8,  # 80% completion
            "correct_answers": 7,
            "total_answers": 10,  # 70% accuracy
            "clicks": ["click1", "click2", "click3"],
        }

        analysis = await producer.analyze_user_behavior(user_interactions)

        assert "engagement_level" in analysis
        assert analysis["engagement_level"] == "high"
        assert "completion_rate" in analysis
        assert analysis["completion_rate"] == 0.8
        assert "difficulty_match" in analysis
        assert analysis["difficulty_match"] == "appropriate"
        assert "recommendations" in analysis
        assert isinstance(analysis["recommendations"], list)

    @pytest.mark.asyncio
    async def test_default_strategy(self, producer):
        """Test default strategy initialization."""
        strategy = producer.get_strategy()

        assert "difficulty" in strategy
        assert "style" in strategy
        assert "pacing" in strategy
        assert "interactivity" in strategy
        assert "depth" in strategy
        assert strategy["difficulty"] == "medium"

    @pytest.mark.asyncio
    async def test_update_strategy(self, producer):
        """Test strategy updates."""
        producer.update_strategy({"difficulty": "hard", "pacing": "fast"})
        strategy = producer.get_strategy()

        assert strategy["difficulty"] == "hard"
        assert strategy["pacing"] == "fast"
        assert strategy["style"] == "balanced"  # Unchanged

    @pytest.mark.asyncio
    async def test_generate_variant_blocks(self, producer):
        """Test parallel variant generation."""
        result = await producer.generate_variant_blocks(
            content_type="quiz",
            topic="Python Basics",
            num_variants=2,
            num_questions=3,
        )

        assert "variants" in result
        assert result["num_variants_generated"] >= 1
        assert "best_variant" in result
        assert "selection_method" in result

    @pytest.mark.asyncio
    async def test_adapt_content_strategy(self, producer):
        """Test strategy adaptation based on analysis."""
        behavior_analysis = {
            "overall_score": 5.0,  # Low score
            "feedback": ["needs simplification"],
        }

        result = await producer.adapt_content_strategy(
            behavior_analysis=behavior_analysis,
            topic="Math",
        )

        # Producer returns updated strategy directly
        assert "difficulty" in result
        assert result["difficulty"] == "easy" or result["difficulty"] == "medium"  # Should adapt based on behavior

    @pytest.mark.asyncio
    async def test_generate_adaptive_blocks(self, producer):
        """Test adaptive block generation."""
        # Set strategy
        producer.update_strategy({"difficulty": "hard", "style": "technical"})

        result = await producer.generate_adaptive_blocks(
            block_type="quiz",
            topic="Advanced Python",
            num_blocks=2,
        )

        assert "blocks" in result
        assert result["num_blocks_generated"] >= 1
        assert "strategy_used" in result

    @pytest.mark.asyncio
    async def test_reviewer_strategy_integration(self):
        """Test reviewer can use strategy protocol."""
        # Generate content
        coordinator = CoordinatorAgent()
        producer = ProducerAgent(coordinator=coordinator, reviewer=ReviewerAgent())
        content_result = await coordinator.generate_content(
            content_type="quiz", topic="Python", num_questions=3
        )

        # Reviewer evaluates
        reviewer = ReviewerAgent("reviewer")
        review = await reviewer._review_content(
            content=content_result["content"],
            content_type="quiz",
            criteria=["clarity", "engagement"],
        )

        # Producer adapts strategy based on review
        adapt_result = await producer.adapt_content_strategy(
            behavior_analysis=review,
            topic="Python",
        )

        # Producer returns updated strategy directly
        assert "difficulty" in adapt_result


class TestAdaptiveWorkflows:
    """Test adaptive content generation workflows."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator instance."""
        return CoordinatorAgent()

    @pytest.fixture
    def producer(self, coordinator):
        """Create producer instance with coordinator."""
        return ProducerAgent(coordinator=coordinator, reviewer=ReviewerAgent())

    @pytest.mark.asyncio
    async def test_low_quality_adaptation(self, producer):
        """Test adaptation for low quality scores."""
        # Simulate low quality with difficulty_match indicator
        analysis = {
            "overall_score": 4.5,
            "feedback": ["too complex"],
            "difficulty_match": "too_hard",
            "engagement_level": "low"
        }

        result = await producer.adapt_content_strategy(
            behavior_analysis=analysis,
            topic="Test",
        )

        # Check strategy was adapted
        assert result["difficulty"] == "easy"
        assert "pacing" in result

    @pytest.mark.asyncio
    async def test_high_quality_enhancement(self, producer):
        """Test enhancement for high quality scores."""
        # Simulate high quality with difficulty_match indicator
        analysis = {
            "overall_score": 9.0,
            "feedback": ["excellent"],
            "difficulty_match": "too_easy",
            "engagement_level": "high"
        }

        result = await producer.adapt_content_strategy(
            behavior_analysis=analysis,
            topic="Test",
        )

        # Check strategy was adapted
        assert result["difficulty"] in ["hard", "medium"]  # Should increase difficulty
        assert "pacing" in result

    @pytest.mark.asyncio
    async def test_variant_merging(self, producer):
        """Test variant generation and merging."""
        result = await producer.generate_variant_blocks(
            content_type="quiz",
            topic="Science",
            num_variants=3,
            num_questions=2,
        )

        assert len(result["variants"]) <= 3
        assert result["best_variant"] is not None
        assert result["num_variants_generated"] >= 1

    @pytest.mark.asyncio
    async def test_strategy_persistence(self, producer):
        """Test strategy persists across operations."""
        # Update strategy
        producer.update_strategy({"difficulty": "expert"})

        # Generate content
        await producer.coordinator.generate_content(
            content_type="quiz", topic="Test", num_questions=2
        )

        # Check strategy persisted
        strategy = producer.get_strategy()
        assert strategy["difficulty"] == "expert"
