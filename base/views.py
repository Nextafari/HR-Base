from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView

from base.exceptions import HRBaseAPIException
from base.models import (
    Application,
    Job,
    Organization,
    Staff,
    User,
    UserRoles,
)
from base.serializers import (
    ApplicationSerializer,
    CreateAccountSerializer,
    CreateOrgStaffSerializer,
    CreateOrgSerializer,
    JobSerializer,
    StaffSerializer,
    UserSerializer,
    UserLoginSerializer,
)


class CreateAccountView(APIView):
    """Create an account for a user."""

    permission_classes = [AllowAny]
    serializer_class = CreateAccountSerializer

    @swagger_auto_schema(
        request_body=serializer_class,
        tags=["Account"],
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)
        serializer.save()
        return Response(
            {
                "status": True,
                "message": "success, account created!",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @swagger_auto_schema(
        request_body=serializer_class,
        tags=["Account"],
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.get(email=email)

        if not user.check_password(password):
            raise HRBaseAPIException("Incorrect credentials! Check and try again.")

        token, created = Token.objects.get_or_create(user=user)
        data = {
            "auth_credentials": {"token": token.key},
            "user": UserSerializer(user).data,
        }
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return Response(
            {
                "status": True,
                "message": "login successful.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationView(APIView):
    """
    User can create an organization and assumes the
    role of organization admin.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrgSerializer

    @swagger_auto_schema(request_body=serializer_class, tags=["Organization"])
    def post(self, request):
        context = {"request": request}
        serializer = self.serializer_class(data=request.data, context=context)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)

        serializer.save()
        return Response(
            {
                "status": True,
                "message": "success, organization created!",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class StaffJoinsOrganizationView(APIView):
    """Create an organization's Staff object in the Staff table."""

    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrgStaffSerializer

    @swagger_auto_schema(
        request_body=serializer_class,
        tags=["Organization"],
    )
    def post(self, request):
        context = {"request": request}
        serializer = self.serializer_class(data=request.data, context=context)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)

        data = serializer.create_staff(serializer.validated_data)
        return Response(
            {
                "status": True,
                "message": "success, staff added to organization.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationStaffView(APIView):
    """Allow only organization admin to view, remove/delete staff record."""

    ORG_ADMIN = UserRoles.ORG_ADMIN
    permission_classes = [IsAuthenticated]
    serializer_class = CreateOrgStaffSerializer

    def validate_org_admin(self, user):
        if user.role != self.ORG_ADMIN:
            raise HRBaseAPIException("You are not authorized for this action!!!")

    @swagger_auto_schema(tags=["Organization staff"])
    def get(self, request):
        user = request.user
        self.validate_org_admin(user)

        try:
            # Handle when user is an HR since a user can join an org with access code
            org = user.user_staff.get().organization
        except Staff.DoesNotExist:
            # Assume is user is an admin user
            org = Organization.objects.get(admin=user)

        org_staff = Staff.objects.filter(organization=org)
        serializer = StaffSerializer(org_staff, many=True)
        return Response(
            {
                "status": True,
                "message": "success, org staff returned.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Organization staff"],
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_QUERY,
                description="Enter id of staff to be deleted.",
                type=openapi.TYPE_NUMBER,
            )
        ],
    )
    def delete(self, request):
        admin = request.user
        self.validate_org_admin(admin)

        pk = request.query_params.get("pk")
        if pk is None:
            raise HRBaseAPIException("Must pass id of staff!!!")

        try:
            org = Organization.objects.get(admin=admin)
            staff = Staff.objects.get(pk=pk, organization=org)
            staff.delete()
        except Staff.DoesNotExist:
            raise HRBaseAPIException(
                "Staff not found!!!", code=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "status": True,
                "message": "Staff deleted.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )


class JobView(ViewSet):
    """Create and view list of jobs available."""

    HR = UserRoles.ORG_HR

    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer

    def validate_hr(self, user):
        if user.role != self.HR:
            raise HRBaseAPIException("You are not authorized for this action!!!")

    @swagger_auto_schema(
        tags=["Job"],
    )
    def list(self, request):
        jobs = Job.objects.filter(is_open=True)
        serializer = self.serializer_class(jobs, many=True)
        return Response(
            {
                "status": True,
                "message": "Jobs retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        request_body=serializer_class,
        tags=["Job"],
    )
    def create(self, request):
        """Create Job Instance"""
        user = request.user
        self.validate_hr(user)

        context = {"user": user}
        serializer = self.serializer_class(data=request.data, context=context)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)

        serializer.save()

        return Response(
            {
                "status": True,
                "message": "job created successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        request_body=serializer_class,
        tags=["Job"],
    )
    def partial_update(self, request, pk=None):
        """Update a Job Instance"""
        user = request.user
        self.validate_hr(user)

        job = Job.objects.get(pk=pk)
        serializer = self.serializer_class(job, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)
        serializer.save()

        return Response(
            {
                "status": True,
                "message": "job updated successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class JobApplicationView(ViewSet):
    """
    Only users who are not staff of the organization(with the Job post)
    can submit an application for the job.
    """

    HR = UserRoles.ORG_HR
    ADMIN = UserRoles.ORG_ADMIN

    permission_classes = [IsAuthenticated]
    serializer_class = ApplicationSerializer

    @swagger_auto_schema(request_body=serializer_class, tags=["Job"])
    @action(detail=True, methods=["POST"])
    def apply(self, request, pk=None):
        user = request.user
        # Users who are not staff of the Organisation that posted a
        # Job opening can submit an Application for the job
        job = self.get_job_or_404(pk)
        self.validate_user(user, job.org_id, action="apply")

        context = {"user": user, "job": job}
        serializer = self.serializer_class(data=request.data, context=context)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            raise HRBaseAPIException(serializer.errors)
        serializer.save()
        return Response(
            {
                "status": True,
                "message": "You have successfully applied for this job",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(tags=["Job"])
    @action(detail=True)
    def applications(self, request, pk):
        user = request.user
        # validate to confirm if user is in the Approved list to view
        # an organizations job applications
        job = self.get_job_or_404(pk)

        self.validate_user(user, job.org_id, action="applications")

        applications = Application.objects.filter(job=job)
        serializer = self.serializer_class(applications, many=True)
        return Response(
            {
                "status": True,
                "message": "Applications returned, successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def validate_user(self, user, job_org, **kwargs):
        action = kwargs.get("action")
        staff = Staff.objects.filter(user=user, organization=job_org)

        # Validate who can create a job application
        if action == "apply" and staff.exists() is True:
            raise HRBaseAPIException(
                "You are a staff member of this org, you cannot apply for this role!!"
            )

        # Validate users who can view an organization's job applications
        if (
            action == "applications"
            and user.role not in [self.HR, self.ADMIN]
            and staff.exists() is False
        ):
            raise HRBaseAPIException(
                "You are not authorized to view applications to this job!!"
            )

    def get_job_or_404(self, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            raise HRBaseAPIException("Job not found", code=status.HTTP_404_NOT_FOUND)
        return job
