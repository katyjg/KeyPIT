from django import template
import calendar

register = template.Library()

@register.filter
def rangelist(i):
    return [r for r in range(1, i+1)]

@register.filter
def month_name(month_number):
    month_number = int(month_number)
    return calendar.month_name[month_number]

@register.filter
def month_abbr(month_number):
    month_number = int(month_number)
    return calendar.month_abbr[month_number]