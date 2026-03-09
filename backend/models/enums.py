from enum import StrEnum


class SessionType(StrEnum):
    RACE = "Race"
    QUALIFYING = "Qualifying"
    SPRINT = "Sprint"
    SPRINT_QUALIFYING = "Sprint Qualifying"
    FP1 = "Practice 1"
    FP2 = "Practice 2"
    FP3 = "Practice 3"


class BannerType(StrEnum):
    RACE_RESULT = "race_result"
    QUALIFYING = "qualifying"
    NEXT_RACE = "next_race"
    DRIVER_CARD = "driver_card"
    STANDINGS = "standings"


class Language(StrEnum):
    EN = "en"
    RU = "ru"
