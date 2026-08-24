from django import template

register = template.Library()

@register.filter
def get(dictionary, key, default=None):
    """
    Gets a value from a dictionary. Can handle nested dictionaries.
    Usage: {{ dictionary|get:key }}
    For nested dictionaries: {{ dictionary|get:first_key|get:second_key }}
    """
    if dictionary is None:
        return default
    try:
        value = dictionary.get(str(key))
        return default if value is None else value
    except (AttributeError, TypeError):
        return default