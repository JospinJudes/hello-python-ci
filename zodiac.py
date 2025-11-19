def get_zodiac_sign(dob):
    month, day = map(int, dob.split('-')[1:])
    zodiac_signs = [
        (1, 20, "Capricorn"), (2, 19, "Aquarius"), (3, 20, "Pisces"), (4, 20, "Aries"),
        (5, 21, "Taurus"), (6, 21, "Gemini"), (7, 22, "Cancer"), (8, 23, "Leo"),
        (9, 23, "Virgo"), (10, 23, "Libra"), (11, 22, "Scorpio"), (12, 22, "Sagittarius"),
        (12, 31, "Capricorn")
    ]
    for m, d, sign in zodiac_signs:
        if (month, day) <= (m, d):
            return sign