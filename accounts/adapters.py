from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        """
        Called when a new user signs up via Google.
        Auto-assigns attendee role.
        """
        user = super().save_user(request, sociallogin, form)
        user.role = "attendee"
        user.save(update_fields=["role"])
        return user