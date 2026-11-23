from datetime import datetime as DateTime

# explicit calendar vocabulary prevents the installed host locale from changing the saved information
KInfoWeekdays = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


# the witnessed desktop profile uses english month names independently of host settings
KInfoMonths = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


# both long date and clock fields share the same local calendar day text
def InfoLocalDate(LocalValue: DateTime) -> str:
    Weekday = KInfoWeekdays[LocalValue.weekday()]
    MonthName = KInfoMonths[LocalValue.month - 1]
    return f"{Weekday}, {MonthName} {LocalValue.day}, {LocalValue.year:04d}"


# both provenance events need the same twelve hour formatting across midnight and noon
def InfoLocalTime(LocalValue: DateTime) -> str:
    PeriodValue = "AM" if LocalValue.hour < 12 else "PM"
    ClockValue = (
        f"{LocalValue.hour % 12 or 12}:{LocalValue.minute:02d}:{LocalValue.second:02d}"
    )
    return f"{InfoLocalDate(LocalValue)} {ClockValue} {PeriodValue}"
