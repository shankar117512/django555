# accounts/metrics.py
from prometheus_client import Counter

USER_REGISTER_COUNTER = Counter(
    "user_registrations_total",
    "Total number of user registrations",
)

USER_LOGIN_COUNTER = Counter(
    "user_logins_total",
    "Total number of successful logins",
)

PROFILE_UPDATE_COUNTER = Counter(
    "profile_updates_total",
    "Total number of profile updates",
)
