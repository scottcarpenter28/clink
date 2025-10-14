from django import template

register = template.Library()


@register.filter
def get_item(container, key):
    try:
        if isinstance(container, dict):
            return container.get(key)
        elif isinstance(container, (list, tuple)):
            return container[int(key)]
        return None
    except (KeyError, IndexError, ValueError, TypeError):
        return None
