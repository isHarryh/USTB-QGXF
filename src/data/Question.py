# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
from dataclasses import dataclass
from functools import total_ordering
from typing import Any, Dict, List, Optional


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
