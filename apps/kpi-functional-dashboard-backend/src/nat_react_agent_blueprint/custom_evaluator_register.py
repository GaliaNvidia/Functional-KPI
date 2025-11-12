# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from nat.builder.builder import EvalBuilder
from nat.builder.evaluator import EvaluatorInfo
from nat.cli.register_workflow import register_evaluator
from nat.data_models.evaluator import EvaluatorBaseConfig


class CustomLLMJudgeEvaluatorConfig(EvaluatorBaseConfig, name="custom_evaluator"):
    """Configuration for LLM-as-a-judge custom evaluator."""

    llm_name: str = Field(description="Name of the LLM to use as judge")
    prompt: str = Field(
        description="Judge prompt template with placeholders: {question}, {reference_answer}, {generated_answer}"
    )


@register_evaluator(config_type=CustomLLMJudgeEvaluatorConfig)
async def register_custom_llm_judge_evaluator(
    config: CustomLLMJudgeEvaluatorConfig, builder: EvalBuilder
):
    from nat.builder.framework_enum import LLMFrameworkEnum
    from .custom_evaluator import LLMJSONJudgeEvaluator

    llm = await builder.get_llm(
        config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN
    )
    evaluator = LLMJSONJudgeEvaluator(
        llm=llm, prompt=config.prompt, max_concurrency=builder.get_max_concurrency()
    )

    yield EvaluatorInfo(
        config=config,
        evaluate_fn=evaluator.evaluate,
        description="Custom LLM-as-a-judge evaluator that returns {score, reasoning} JSON.",
    )
