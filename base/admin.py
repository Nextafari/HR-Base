from django.contrib import admin

from base.models import User, Organization, Job, Application, Staff


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "created",
    ]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "admin_id",
        "created",
        "modified",
    ]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "org_id",
        "created_by",
        "created",
        "modified",
    ]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created",
        "modified",
    ]


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "organization",
        "date_joined",
    ]
