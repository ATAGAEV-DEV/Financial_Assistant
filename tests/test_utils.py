import unittest

from app.tools.utils import hash_password


class UtilsTests(unittest.TestCase):
    """Test password utility functions."""

    def test_hash_password_returns_sha256_hex_digest(self) -> None:
        """Password hashing returns the expected deterministic digest."""
        self.assertEqual(
            hash_password("secret"),
            "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
        )


if __name__ == "__main__":
    unittest.main()
