# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from nat.eval.evaluator.base_evaluator import BaseEvaluator
from nat.eval.evaluator.evaluator_model import EvalInputItem, EvalOutputItem


class LLMJSONJudgeEvaluator(BaseEvaluator):
    """
    LLM-as-a-judge evaluator that uses a provided prompt to compare
    the generated answer against the reference answer and returns a
    JSON object with fields: {"score": 0.0|0.5|1.0, "reasoning": "..."}.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        prompt: str,
        output_dir: str = "output_data",
        max_concurrency: int = 4,
    ) -> None:
        super().__init__(
            max_concurrency=max_concurrency, tqdm_desc="Custom LLM Judge Evaluating"
        )
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_template(prompt)
        self.output_dir = Path(output_dir)

    async def evaluate_item(self, item: EvalInputItem) -> EvalOutputItem:
        question = "" if item.input_obj is None else str(item.input_obj)
        reference_answer = (
            "" if item.expected_output_obj is None else str(item.expected_output_obj)
        )
        generated_answer = "" if item.output_obj is None else str(item.output_obj)

        try:
            # Extract JSON file and include first 10 rows into the generated_answer for judging
            sample_rows_text, used_file = self._extract_sample_rows(generated_answer)

            augmented_generated = generated_answer
            if sample_rows_text:
                augmented_generated = f"{generated_answer}\n\nJSON_SAMPLE_ROWS (first 10 rows from {used_file}):\n{sample_rows_text}"

            messages = self.prompt_template.format_messages(
                question=question,
                reference_answer=reference_answer,
                generated_answer=augmented_generated,
            )

            response = await self.llm.ainvoke(messages)
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            score, reasoning = self._parse_score_and_reasoning(response_text)

            return EvalOutputItem(
                id=item.id,
                score=score,
                reasoning={
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer,
                    "json_file_used": used_file,
                    "llm_judgment": reasoning,
                },
            )

        except Exception as e:
            return EvalOutputItem(
                id=item.id,
                score=0.0,
                reasoning={
                    "error": f"LLM evaluation failed: {str(e)}",
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer,
                },
            )

    def _parse_score_and_reasoning(self, text: str) -> tuple[float, str]:
        """Extract score/reasoning from LLM response. Robust to markdown wrappers."""
        # Try direct JSON
        try:
            obj = json.loads(text)
            return obj.get("score"), str(obj.get("reasoning", text))
        except Exception:
            pass

        # Extract JSON from code block
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(1))
                return obj.get("score"), str(obj.get("reasoning", text))
            except Exception:
                pass

        # Fallback: try to find a numeric hint and clamp to {0.0,0.5,1.0}
        num = self._extract_numeric(text)
        return num, text

    def _extract_numeric(self, text: str) -> float:
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
        if not m:
            return 0.0
        try:
            return float(m.group(1))
        except ValueError:
            return 0.0

    def _normalize(self, val: Any) -> float:
        try:
            x = float(val)
        except Exception:
            return 0.0
        # Map to discrete {0.0, 0.5, 1.0}
        if x <= 0.25:
            return 0.0
        if x <= 0.75:
            return 0.5
        return 1.0

    def _extract_sample_rows(self, generated_answer: str) -> tuple[str, Optional[str]]:
        """
        Find a JSON filename mentioned in the generated answer, load it, and
        return a pretty-printed string of the first 10 rows. Supports two formats:
          - A list[dict]
          - A dict with shape { "response": { "results": list[...] } } (ECI format)
        """
        # Find candidate *.json tokens (inside backticks, quotes, or plain)
        patterns = [
            r"`([^`]+\.json)`",
            r'"([^"]+\.json)"',
            r"'([^']+\.json)'",
            r"(\S+\.json)",
        ]

        text = generated_answer
        filename: Optional[str] = None
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                candidate = m.group(1)
                # Resolve path: absolute or relative to output_dir
                p = Path(candidate)
                if not p.is_absolute():
                    p = (self.output_dir / candidate).resolve()
                if p.exists():
                    filename = str(p)
                    break

        if not filename:
            return "", None

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return "", Path(filename).name

        # Normalize to list of rows
        rows: list[Any]
        if isinstance(data, list):
            rows = data
        elif (
            isinstance(data, dict)
            and isinstance(data.get("response"), dict)
            and isinstance(data["response"].get("results"), list)
        ):
            rows = data["response"]["results"]
        else:
            return "", Path(filename).name

        # Take first 10
        sample = rows[:10]
        try:
            pretty = json.dumps(sample, indent=2, ensure_ascii=False)
        except Exception:
            pretty = str(sample)
        return pretty, Path(filename).name
