from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException

from base import logger


class HRBaseAPIException(APIException):
    """
    Custom exception class to handle API errors,
    this class is similar to rest_framework ValidationError.

    Resources: https://www.django-rest-framework.org/api-guide/exceptions/#validationerror
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid input.")
    default_code = "invalid"

    def __init__(self, detail=None, code=None):
        super().__init__(detail=None, code=None)
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        # Reference:: DRF_exceptions_ValidationError For validation failures,
        # we may collect many errors together,
        # so the details should always be coerced to a list if not already.
        if isinstance(detail, str):
            detail = detail
        elif isinstance(detail, tuple) and not isinstance(detail, str):
            detail = list(detail)
        elif not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = {"status": False, "message": detail}
        logger.error("%s" % (self.detail))
