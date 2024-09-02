from django.utils.crypto import get_random_string


def gen_staff_access_code():
    RANDOM_STRING_CHARS = "abchrbasefghijklmnopqrsytuvwxzut0123456789"
    return get_random_string(3, allowed_chars=RANDOM_STRING_CHARS)
