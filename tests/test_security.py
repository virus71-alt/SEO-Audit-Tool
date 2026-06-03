from seo_audit.core.security import (
    create_access_token, decode_token, hash_password, verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("hunter2_long_pwd")
    assert verify_password("hunter2_long_pwd", h)
    assert not verify_password("nope", h)


def test_jwt_roundtrip():
    token = create_access_token(subject="42", extra_claims={"role": "user"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
