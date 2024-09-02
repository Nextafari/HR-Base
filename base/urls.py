from django.urls import path
from rest_framework.routers import DefaultRouter

from base import views


router = DefaultRouter()
router.register("api/jobs/create", views.JobView, "create_and_update_job")
router.register("api/jobs", views.JobApplicationView, "create_and_list_job_application")


urlpatterns = [
    path(
        "api/account/create",
        views.CreateAccountView.as_view(),
        name="create_account",
    ),
    path(
        "api/account/login",
        views.UserLoginView.as_view(),
        name="login",
    ),
    path("api/org/create", views.OrganizationView.as_view(), name="create_org"),
    path(
        "api/org/staff/join",
        views.StaffJoinsOrganizationView.as_view(),
        name="staff_joins_org",
    ),
    path(
        "api/org/staff",
        views.OrganizationStaffView.as_view(),
        name="org_staff",
    ),
] + router.urls
