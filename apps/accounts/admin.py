from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import CandidateProfile, OrganizationMember, Permission, Role, User
from apps.organizations.models import Organization
from apps.subscriptions.models import Plan, Subscription

admin.site.register(User, DjangoUserAdmin)
admin.site.register(CandidateProfile)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(OrganizationMember)
admin.site.register(Organization)
admin.site.register(Plan)
admin.site.register(Subscription)
