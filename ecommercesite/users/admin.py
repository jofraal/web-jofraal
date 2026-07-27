from django.contrib import admin
from .models import Profile, Address

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'document_type', 'document_number']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_type', 'district', 'is_default']
    list_filter = ['address_type', 'is_default', 'country']
    search_fields = ['user__username', 'user__email', 'street', 'district']
    list_editable = ['is_default']
    raw_id_fields = ['user']