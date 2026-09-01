from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .auth_utils import normalize_username


class RegistrationNumberAuthBackend(ModelBackend):
    """
    Allows login with:
    - Student registration number (e.g. IN14/00001/22)
    - Email address (for supervisors, lecturers, and anyone who registered with email)
    - Exact username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        user_model = get_user_model()
        candidates = []

        # Try email match first (for supervisors/lecturers who registered with email)
        email_lower = username.strip().lower()
        try:
            user_by_email = user_model._default_manager.get(email__iexact=email_lower)
            candidates.append(user_by_email.username)
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            pass

        # Also try the raw input and the normalized registration number form
        if username not in candidates:
            candidates.append(username)
        normalized_username = normalize_username(username)
        if normalized_username and normalized_username not in candidates:
            candidates.append(normalized_username)

        for candidate in candidates:
            try:
                user = user_model._default_manager.get(username__iexact=candidate)
            except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
                continue
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
