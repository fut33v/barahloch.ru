from django import template
import re, html
register = template.Library()

_REGEX_HTTP = re.compile("http")
_REGEX_HTTPS = re.compile("https")


@register.filter(name='abs')
def abs_filter(value):
    return abs(value)


@register.filter(name='neg')
def neg_filter(value):
    return -value


def make_numbers_bold(text):
    if not isinstance(text, str):
        return text
    _tokens = text.split(' ')
    _tokens_bold = []
    for t in _tokens:
        is_digit = False
        # is_link = False
        for c in t:
            if c.isdigit():
                is_digit = True
        h1 = _REGEX_HTTP.findall(t)
        h2 = _REGEX_HTTPS.findall(t)
        if len(h1) > 0 or len(h2) > 0:
            # is_link = True
            is_digit = False
        if is_digit:
            _tokens_bold.append("<b>" + t + "</b>")
        else:
            _tokens_bold.append(t)

    result = str()
    for t in _tokens_bold:
        result += t + " "

    return result


@register.filter(name='bold_numbers')
def bold_numbers_filter(text):
    return make_numbers_bold(text)


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter(name='unescape')
def unescape_filter(value):
    return html.unescape(value)
