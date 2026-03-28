from .models import StripePlan
from django.contrib import admin

@admin.register(StripePlan)
class StripePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'interval', 'credits', 'active')
    list_filter = ('interval', 'active')
    search_fields = ('name',)