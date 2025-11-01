from django.contrib import admin

from core.models import UserWallet, Draw, ForgedKey
admin.site.register(UserWallet)
admin.site.register(Draw)
admin.site.register(ForgedKey)