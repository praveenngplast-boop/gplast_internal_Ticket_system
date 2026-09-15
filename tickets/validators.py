# tickets/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SimpleLengthValidator:
    """
    GPLAST password policy:
      - Minimum 4 characters
      - Maximum 14 characters
      - No restriction on character types
    """
    MIN_LENGTH = 4
    MAX_LENGTH = 14

    def validate(self, password, user=None):
        errors = []
        if len(password) < self.MIN_LENGTH:
            errors.append(
                _(f"Password must be at least {self.MIN_LENGTH} characters.")
            )
        if len(password) > self.MAX_LENGTH:
            errors.append(
                _(f"Password must be at most {self.MAX_LENGTH} characters.")
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            f"Your password must be between {self.MIN_LENGTH} and "
            f"{self.MAX_LENGTH} characters."
        )