# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
from dataclasses import dataclass
from enum import IntEnum
from functools import total_ordering
from typing import Any, Callable, Dict, List, Optional, TypeVar

from ..utils.Randomness import Randomness


class QuestionType(IntEnum):
    SINGLE_CHOICE = 1
    MULTIPLE_CHOICE = 2
    JUDGE = 3
    FILL_BLANK = 4


@dataclass
@total_ordering
class Answer:
    id: int
    title: str

    def __lt__(self, other: object) -> bool:
        return isinstance(other, Answer) and self.id < other.id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Answer) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def load_from_web_data(data: Dict[str, Any]) -> "Answer":
        return Answer(id=data["answerId"], title=data["answerTitle"])

    @staticmethod
    def load_from_kv_table(table: Dict[str, Dict[str, Any]]) -> List["Answer"]:
        return [Answer(id=int(k), title=v["title"]) for k, v in table.items()]

    @staticmethod
    def dump_to_kv_table(array: List["Answer"]) -> Dict[str, Dict[str, Any]]:
        return {str(obj.id): {"title": obj.title} for obj in array}


_K = TypeVar("_K")


@dataclass
@total_ordering
class Question:
    id: int
    title: str
    type: int
    answers: List[Answer]
    right_answer: Optional[str]
    stage_id: Optional[int] = None  # Custom data

    def __lt__(self, other: object) -> bool:
        return isinstance(other, Answer) and self.id < other.id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Answer) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def summary(self, indent: int = 0, max_title_len: int = 40, max_answer_len: int = 10) -> str:
        if indent < 0:
            raise ValueError("indent must be non-negative")
        if max_title_len < 4 or max_answer_len < 4:
            raise ValueError("max_title_len and max_answer_len must be at least 4")

        def slim_text(text: str, max_len: int):
            if len(text) > max_len:
                half = (max_len - 2) // 2
                return text[:half] + " ... " + text[-half:]
            return text

        title = slim_text(self.title.replace("&nbsp;", " "), max_title_len)

        if self.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.JUDGE]:
            answer_parts = []
            for i, answer in enumerate(sorted(self.answers)):
                label = chr(65 + i)  # A, B, C...
                answer_text = slim_text(answer.title, max_answer_len)
                answer_parts.append(f"{label}.{answer_text}")
            return f"{' ' * indent}{title}\n{' ' * indent}{' '.join(answer_parts)}"
        else:
            return f"{' ' * indent}{title}"

    def random_answer(self, multiple_choice_k: int = 2, fill_blank_default: str = " ") -> str:
        if self.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.JUDGE]:
            k = min(len(self.answers), multiple_choice_k if self.type == QuestionType.MULTIPLE_CHOICE else 1)
            if k < 1:
                raise ValueError("No enough choice to select")
            return "|".join(Randomness.choose([str(a.id) for a in self.answers], k=k))
        elif self.type == QuestionType.FILL_BLANK:
            return fill_blank_default
        else:
            raise ValueError(f"Not supported question type: {self.type}")

    @staticmethod
    def cluster(questions: List["Question"], key: Callable[["Question"], _K]) -> Dict[_K, List["Question"]]:
        result = {}
        for q in questions:
            k = key(q)
            if k not in result:
                result[k] = []
            result[k].append(q)
        return result

    @staticmethod
    def load_from_web_data(data: Dict[str, Any]) -> "Question":
        return Question(
            id=data["questionId"],
            title=data["questionTitle"],
            type=data["questionType"],
            answers=list(map(Answer.load_from_web_data, data["answerList"])),
            right_answer=data.get("rightAnswer"),
        )

    @staticmethod
    def load_from_kv_table(table: Dict[str, Dict[str, Any]]) -> List["Question"]:
        return [
            Question(
                id=int(k),
                title=v["title"],
                type=v["type"],
                answers=(Answer.load_from_kv_table(v["answers"])),
                right_answer=v.get("rightAnswer"),
                stage_id=v.get("stageId"),
            )
            for k, v in table.items()
        ]

    @staticmethod
    def dump_to_kv_table(array: List["Question"]) -> Dict[str, Dict[str, Any]]:
        return {
            str(obj.id): {
                "title": obj.title,
                "type": obj.type,
                "answers": Answer.dump_to_kv_table(obj.answers),
                "rightAnswer": obj.right_answer,
                "stageId": obj.stage_id,
            }
            for obj in array
        }
