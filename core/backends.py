from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .auth_utils import normalize_username


class RegistrationNumberAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        user_model = get_user_model()
        candidates = [username]
        normalized_username = normalize_username(username)
        if normalized_username and normalized_username not in candidates:
            candidates.append(normalized_username)

        for candidate in candidates:
            try:
                user = user_model._default_manager.get(username=candidate)
            except user_model.DoesNotExist:
                continue
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
