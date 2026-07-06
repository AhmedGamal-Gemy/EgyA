from collections import Counter

from shared.enums.flag_type import FlagType
from shared.schemas.flag import Flag
from shared.schemas.report import FlagSummary


def aggregate_flags(flags: list[Flag]) -> list[FlagSummary]:
    by_type: dict[FlagType, list[Flag]] = {}
    for f in flags:
        by_type.setdefault(f.flag_type, []).append(f)

    return [
        FlagSummary(
            flag_type=flag_type,
            count=len(items),
            examples=[i.message for i in items[:3]],  # a few representative examples, not all
        )
        for flag_type, items in by_type.items()
    ]
