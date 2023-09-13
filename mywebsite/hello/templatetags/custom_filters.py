from django import template

register = template.Library()


@register.filter(name='isinstance')
def is_instance(value, class_name):
    # Use a dictionary to map class names to actual classes.
    # Add or remove types as necessary.
    types = {
        'str': str,
        'int': int,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        # ... any other types you want to support
    }

    return isinstance(value, types.get(class_name, None))
