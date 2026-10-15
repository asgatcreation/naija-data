"""Human-readable, translatable error messages for each error code from naija-data."""

from django.utils.translation import gettext_lazy as _

PHONE_MESSAGES = {
    "empty": _("Enter a phone number."),
    "invalid_characters": _("A phone number can only contain digits, spaces, dashes, brackets and a leading +."),
    "not_nigerian": _("Enter a Nigerian phone number (+234)."),
    "bad_length": _("This phone number has the wrong number of digits."),
    "unknown_prefix": _("This is not a Nigerian mobile prefix."),
    "unallocated": _("This number range is not allocated to any network."),
    "reserved": _("This number range is reserved and not in service."),
    "unknown_area_code": _("This is not a Nigerian landline area code."),
    "wrong_type": _("This type of phone number is not accepted here."),
}

PLATE_MESSAGES = {
    "empty": _("Enter a plate number."),
    "invalid_characters": _("A plate number can only contain letters, digits, spaces and dashes."),
    "unknown_format": _("Enter a plate number like ABC-123DE."),
    "unknown_state": _("This dealer plate does not start with D and a valid state code."),
    "wrong_format": _("This type of plate number is not accepted here."),
}

NUBAN_MESSAGES = {
    "format": _("Enter a 10-digit account number."),
    "check_digit": _("This account number is not valid for the selected bank."),
    "unknown_bank": _("Select a valid bank."),
}

ADMIN_MESSAGES = {
    "unknown_state": _("Select a valid state."),
    "unknown_lga": _("Select a valid local government area."),
    "lga_not_in_state": _("This local government area is not in the selected state."),
}
