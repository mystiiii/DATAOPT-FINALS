def theme_preferences(request):
    """Expose the signed-in user's color scheme & custom colors safely to all templates."""
    scheme = 'slate-blue'
    custom_colors = {}
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            profile = user.profile
        except Exception:
            profile = None
        if profile:
            scheme = profile.color_scheme or 'slate-blue'
            if isinstance(profile.custom_colors, dict):
                custom_colors = profile.custom_colors
    return {
        'user_color_scheme': scheme,
        'user_custom_colors': custom_colors,
    }
