from rest_framework import serializers

from base import logger
from base.exceptions import HRBaseAPIException
from base.models import Application, Job, Organization, Staff, User, UserRoles


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = [
            "password",
            "is_admin",
            "is_staff",
            "is_superuser",
            "user_permissions",
            "groups",
        ]


class CreateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "name", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


# class OrganizationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Organization
#         fields = "__all__"


class CreateOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "name",
            "admin",
            "valuation",
            "location",
            "staff_access_code",
        ]
        read_only_fields = ["admin", "staff_access_code"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        org = Organization.objects.create(admin=user, **validated_data)

        # Update user role after organization has been created.
        user.role = UserRoles.ORG_ADMIN
        user.save(update_fields=["role"])
        return org


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = "__all__"


class CreateOrgStaffSerializer(serializers.Serializer):
    org_access_code = serializers.CharField()

    # use custom method since I am not using ModelSerializer and
    # want to return an instance of another ModelObject(Staff)
    # and also allow the user to write their org_access_code
    # in CreateOrgStaffSerializer
    def create_staff(self, validated_data):
        """
        Allow user join an organization as a staff.
        Get organization from DB, then create staff record

        Params: validated_data
        Return: dict of Staff data
        """
        request = self.context["request"]
        org_access_code = validated_data["org_access_code"]

        try:
            org = Organization.objects.get(staff_access_code=org_access_code)
        except Organization.DoesNotExist:
            raise HRBaseAPIException(
                "No organization with access code: %s" % (org_access_code)
            )

        # Use get_or_creat to avoid creating duplicate record.
        # Considering a user cannot be in the same organization twice with one role.
        staff, _ = Staff.objects.get_or_create(
            user=request.user,
            organization=org,
        )
        return StaffSerializer(staff).data


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "created_by": {"read_only": True},
            "org_id": {"read_only": True},
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }

    def create(self, validated_data):
        user = self.context["user"]

        try:
            org = user.user_staff.get().organization
        except Staff.DoesNotExist as e:
            # Handle exception when there is no
            # relatedObject (staff) existing for that user.
            err_mg = e.args[0]
            logger.error("%s" % (err_mg))
            raise HRBaseAPIException("User has no staff record!!!")

        job = Job.objects.create(created_by=user, org_id=org, **validated_data)

        return job


class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = Application
        fields = "__all__"
        extra_kwargs = {
            "applicant_id": {"read_only": True},
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }

    def create(self, validated_data):
        user = self.context["user"]
        job = self.context["job"]

        application, created = Application.objects.get_or_create(
            applicant_id=user, job=job, **validated_data
        )

        if created is False:
            raise HRBaseAPIException("Already applied for this job")

        return application
