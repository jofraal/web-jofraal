from django import template

register = template.Library()

@register.filter
def user_has_purchased(product, user):
    return product.user_has_purchased(user)
