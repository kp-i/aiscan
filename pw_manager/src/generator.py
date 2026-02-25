"""Password generator using secrets (cryptographically secure)."""
import secrets
import string


def generate(
    length: int = 20,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = True,
) -> str:
    """Generate a random password.

    Args:
        length: Total character count (8-128).
        use_upper: Include uppercase letters.
        use_lower: Include lowercase letters.
        use_digits: Include digits.
        use_symbols: Include symbols.
        exclude_ambiguous: Exclude 0/O/l/1/I/| etc.
    """
    if length < 4:
        length = 4
    if length > 128:
        length = 128

    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    if exclude_ambiguous:
        upper = upper.translate(str.maketrans("", "", "OI"))
        lower = lower.translate(str.maketrans("", "", "lo"))
        digits = digits.translate(str.maketrans("", "", "01"))
        symbols = symbols.translate(str.maketrans("", "", "|"))

    pool = ""
    required: list[str] = []

    if use_upper:
        pool += upper
        required.append(secrets.choice(upper))
    if use_lower:
        pool += lower
        required.append(secrets.choice(lower))
    if use_digits:
        pool += digits
        required.append(secrets.choice(digits))
    if use_symbols:
        pool += symbols
        required.append(secrets.choice(symbols))

    if not pool:
        pool = string.ascii_letters + string.digits

    remaining = [secrets.choice(pool) for _ in range(length - len(required))]
    password_list = required + remaining
    secrets.SystemRandom().shuffle(password_list)
    return "".join(password_list)


def estimate_strength(password: str) -> tuple[int, str]:
    """Return (score 0-100, label) for a password."""
    score = 0
    length = len(password)

    if length >= 8:
        score += 20
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10
    if length >= 20:
        score += 10

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    variety = sum([has_upper, has_lower, has_digit, has_symbol])
    score += variety * 12

    if score >= 80:
        return score, "強い"
    elif score >= 55:
        return score, "普通"
    elif score >= 30:
        return score, "弱い"
    else:
        return score, "非常に弱い"
