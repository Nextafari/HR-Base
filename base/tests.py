from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from base.models import User, UserRoles, Staff, Organization, Job


class AccountTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "password123",
        }

    def test_user_creation(self):
        response = self.client.post(reverse("create_account"), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_login(self):
        self.client.post(reverse("create_account"), self.user_data)
        response = self.client.post(
            reverse("login"),
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data["data"]["auth_credentials"])


class OrganizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            name="Org Admin",
            email="admin@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.user)
        self.organization_data = {
            "name": "Test Organization",
            "valuation": 1000000000,
            "location": "HR Base, Victoria Island, Lagos, Nigeria.",
        }

    def test_organization_creation(self):
        prev_user_role = self.user.role
        response = self.client.post(reverse("create_org"), self.organization_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["admin"], self.user.id)
        self.assertNotEqual(prev_user_role, self.user.role)
        self.assertEqual(self.user.role, "org_admin")
        self.assertIn("staff_access_code", response.data["data"])


class StaffJoinTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            name="Org Admin", email="admin@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.organization = Organization.objects.create(
            name="Test Organization", location="Test Org", admin=self.user
        )
        self.staff_user = User.objects.create_user(
            name="Staff User", email="staff@example.com", password="password123"
        )

    def test_join_organization_as_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            reverse("staff_joins_org"),
            {"org_access_code": self.organization.staff_access_code},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            self.organization.org_staff.filter(user__id=self.staff_user.id).exists()
        )


class OrganizationStaffManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org_admin = User.objects.create_user(
            name="Org Admin",
            email="admin@example.com",
            password="password123",
            role=UserRoles.ORG_ADMIN,
        )
        self.client.force_authenticate(user=self.org_admin)
        self.organization = Organization.objects.create(
            name="Test Organization", location="Test Org", admin=self.org_admin
        )
        self.staff_user = User.objects.create_user(
            name="Staff User", email="staff@example.com", password="password123"
        )
        self.staff = Staff.objects.create(
            user=self.staff_user, organization=self.organization
        )

    def test_get_organization_staff_list(self):
        response = self.client.get(reverse("org_staff"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_remove_staff_member(self):
        url = f"/v1/core/api/org/staff?pk={self.staff.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Staff.objects.filter(id=self.staff_user.id).exists())


class JobManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org_admin = User.objects.create_user(
            name="Org Admin", email="admin@example.com", password="password123"
        )
        self.organization = Organization.objects.create(
            name="Test Organization", location="Test Org", admin=self.org_admin
        )
        self.org_hr = User.objects.create_user(
            name="Org HR",
            role=UserRoles.ORG_HR,
            email="hr@example.com",
            password="password123",
        )
        self.staff = Staff.objects.create(
            user=self.org_hr, organization=self.organization
        )
        self.client.force_authenticate(user=self.org_hr)

    def test_create_job(self):
        url = "/v1/core/api/jobs/create/"
        job_data = {
            "title": "Test Job",
            "description": "Job Description",
            "organization": self.organization.id,
        }
        response = self.client.post(url, data=job_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["title"], job_data["title"])

    def test_update_job(self):
        job = Job.objects.create(
            title="Test Job",
            created_by=self.org_hr,
            description="Job Description",
            org_id=self.organization,
        )
        update_data = {
            "title": "Updated Job Title",
            "description": "Updated Description",
        }
        url = f"/v1/core/api/jobs/create/{job.id}/"
        response = self.client.patch(url, data=update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["title"], update_data["title"])


class JobApplicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org_admin = User.objects.create_user(
            name="Org Admin",
            email="admin@example.com",
            role=UserRoles.ORG_ADMIN,
            password="password123",
        )
        self.org_hr = User.objects.create_user(
            name="Org HR",
            email="admin2@example.com",
            role=UserRoles.ORG_HR,
            password="password123",
        )
        self.organization = Organization.objects.create(
            name="Test Organization", location="Test Org", admin=self.org_admin
        )
        self.job = Job.objects.create(
            title="Test Job",
            created_by=self.org_hr,
            description="Job Description",
            org_id=self.organization,
        )
        self.applicant = User.objects.create_user(
            name="Applicant", email="applicant@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.applicant)

    def test_apply_for_job(self):
        url = f"/v1/core/api/jobs/{self.job.id}/apply/"
        payload = {
            "skill_description": "I know how to speak english, do the xyz while doing some loling to it all."
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("status", response.data)
        self.assertTrue(
            self.job.application_set.filter(applicant_id=self.applicant).exists()
        )

    def test_get_applications_success(self):
        # Authenticate with admin to return organization applications
        self.client.force_authenticate(user=self.org_admin)

        url = f"/v1/core/api/jobs/{self.job.id}/applications/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data["data"], list))

    def test_get_applications_error(self):
        url = f"/v1/core/api/jobs/{self.job.id}/applications/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
        self.assertTrue(
            response.data["message"].__contains__(
                "You are not authorized to view applications to this job!!"
            )
        )
