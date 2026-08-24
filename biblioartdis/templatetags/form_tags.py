from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    """Agrega una clase CSS a un campo de formulario"""
    return value.as_widget(attrs={'class': arg}) 