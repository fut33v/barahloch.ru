from django import template
register = template.Library()


@register.filter(name='abs')
def abs_filter(value):
    return abs(value)


@register.filter(name='neg')
def abs_filter(value):
    return -value


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

