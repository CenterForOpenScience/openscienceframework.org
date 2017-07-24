from django.utils import timezone

from rest_framework.exceptions import APIException, ValidationError, PermissionDenied

from api.cas import util, messages, errors

from framework.auth import register_unconfirmed, campaigns
from framework.auth.core import generate_verification_key
from framework.auth.exceptions import DuplicateEmailError, ChangePasswordError, InvalidTokenError, ExpiredTokenError
from framework.auth.views import send_confirm_email

from osf.models import OSFUser
from osf.exceptions import ValidationError as OSFValidationError

from website import settings as web_settings
from website.mails import send_mail
from website.mails import WELCOME, EXTERNAL_LOGIN_LINK_SUCCESS, FORGOT_PASSWORD
from website.util.time import throttle_period_expired

# TODO: raise API exception, use error_code for CAS, keep error_detail


def create_unregistered_user(credentials):
    """
    Handle new account creation through OSF.

    :param credentials: the user's information
    :return: the newly created but unconfirmed user
    :raises: APIException, ValidationError, PermissionDenied
    """

    # check required fields
    fullname = credentials.get('fullname')
    email = credentials.get('email')
    password = credentials.get('password')
    if not (fullname and email and password):
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # check and update campaign
    campaign = credentials.get('campaign')
    if campaign and campaign not in campaigns.get_campaigns():
        campaign = None

    try:
        user = register_unconfirmed(email, password, fullname, campaign=campaign)
    except DuplicateEmailError:
        # user already exists
        raise ValidationError(detail=messages.ALREADY_REGISTERED)
    except ChangePasswordError:
        # password is same as email
        raise ValidationError(detail=messages.PASSWORD_SAME_AS_EMAIL)
    except OSFValidationError:
        # email is invalid or its domain is blacklisted
        raise ValidationError(detail=messages.INVALID_EMAIL)
    except ValueError:
        # email has already been confirmed to this user
        raise ValidationError(detail=messages.EMAIL_ALREADY_CONFIRMED)

    try:
        send_confirm_email(user, email=user.username, renew=False, external_id_provider=None, external_id=None)
    except KeyError:
        raise APIException(detail=messages.REQUEST_FAILED)

    return user


def register_user(credentials):
    """
    Handle email verification for account creation through OSF.

    :param credentials: the user's information
    :return: the user
    :raises: ValidationError, PermissionDenied
    """

    # check required fields
    email = credentials.get('email')
    token = credentials.get('verificationCode')
    if not email or not token:
        # TODO: raise API exception, use error_code for CAS, keep error_detail
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # retrieve the user (the email must be primary)
    user = util.find_user_by_email_or_guid(None, email, username_only=True)
    if not user:
        raise ValidationError(detail=messages.EMAIL_NOT_FOUND)
    if user.date_confirmed:
        raise ValidationError(detail=messages.ALREADY_VERIFIED)

    # verify token, register user and send welcome email
    try:
        email = user.get_unconfirmed_email_for_token(token)
    except (ExpiredTokenError, InvalidTokenError):
        raise PermissionDenied(detail=messages.INVALID_CODE)
    user.register(email)
    send_mail(to_addr=user.username, mail=WELCOME, mimetype='html', user=user)

    # clear unclaimed records, email verifications and pending v2 key for password reset
    user.email_verifications = {}
    user.unclaimed_records = {}
    user.verification_key_v2 = {}

    # generate v1 key for CAS login
    user.verification_key = generate_verification_key(verification_type=None)
    user.save()

    return user


def resend_confirmation(credential):

    """
    Find OSF account by email. Verify that the user is eligible for resend new account verification. Resend the
    email if the user hasn't recently make the same request.

    :param credential: the user
    :return: the user
    :raises: ValidationError, PermissionDenied, APIException
    """

    # check required fields
    email = credential.get('email')
    if not email:
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # retrieve the user
    user = util.find_user_by_email_or_guid(None, email, username_only=False)
    if not user:
        raise ValidationError(detail=messages.EMAIL_NOT_FOUND)
    inactive_status = util.is_user_inactive(user)
    if not inactive_status:
        raise ValidationError(detail=messages.ALREADY_VERIFIED)
    if inactive_status != 'ACCOUNT_NOT_VERIFIED':
        raise ValidationError(detail=messages.ACCOUNT_NOT_ELIGIBLE)

    # check throttle
    if not throttle_period_expired(user.email_last_sent, web_settings.SEND_EMAIL_THROTTLE):
        raise ValidationError(detail=messages.EMAIL_THROTTLE_ACTIVE)

    # resend email
    try:
        send_confirm_email(user, email, renew=True, external_id_provider=None, external_id=None)
    except KeyError:
        raise APIException(detail=messages.REQUEST_FAILED)
    user.email_last_sent = timezone.now()
    user.save()

    return user


def create_or_link_external_user(credentials):
    """
    Handle account creation or link through external identity provider.

    :param credentials: the user
    :return: the newly created or linked user and pending status for external identity
    :raises: ValidationError, PermissionDenied, APIException
    """

    # check required fields
    email = credentials.get('email')
    provider = credentials.get('externalIdProvider')
    identity = credentials.get('externalId')
    fullname = '{} {}'.format(
        credentials.get('attributes').get('given-names', ''),
        credentials.get('attributes').get('family-name', '')
    ).strip()
    # user's ORCiD privacy settings may prevent releasing names, use the identity instead
    if not fullname:
        fullname = identity
    if not (email and fullname and provider and identity):
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # check and update campaign
    campaign = credentials.get('campaign')
    if campaign and campaign not in campaigns.get_campaigns():
        campaign = None

    # try to retrieve user
    user = util.find_user_by_email_or_guid(None, email, username_only=False)
    external_identity = {
        provider: {
            identity: None
        }
    }
    util.ensure_external_identity_uniqueness(provider, identity, user)

    if user:
        inactive_status = util.is_user_inactive(user)
        if inactive_status:
            # user not active but in database
            if inactive_status == errors.ACCOUNT_NOT_VERIFIED or inactive_status == errors.ACCOUNT_NOT_CLAIMED:
                user.fullname = fullname
                user.update_guessed_names()
                user.email_verifications = {}
                user.unclaimed_records = {}
                user.verification_key = {}
                external_identity[provider][identity] = 'CREATE'
            else:
                raise PermissionDenied(detail=messages.ACCOUNT_NOT_ELIGIBLE)
        else:
            # existing user
            external_identity[provider][identity] = 'LINK'
        if provider in user.external_identity:
            user.external_identity[provider].update(external_identity[provider])
        else:
            user.external_identity.update(external_identity)
        user.add_unconfirmed_email(email, expiration=None, external_identity=external_identity)
        user.save()
    else:
        # new user
        external_identity[provider][identity] = 'CREATE'
        user = OSFUser.create_unconfirmed(
            username=email,
            password=None,
            fullname=fullname,
            external_identity=external_identity,
            campaign=campaign
        )
        user.save()

    try:
        # renew is not compatible for external identity, must be set to `False`
        send_confirm_email(
            user,
            email,
            renew=False,
            external_id_provider=provider,
            external_id=identity
        )
    except KeyError:
        raise APIException(detail=messages.REQUEST_FAILED)

    return user, external_identity[provider][identity]


def register_external_user(credentials):
    """
    Handle email verification for account creation or link through external identity provider.

    :param credentials: the user
    :return: the created or linked user and the previous pending status
    :raises: ValidationError, PermissionDenied, APIException
    """

    # check required fields
    email = credentials.get('email')
    token = credentials.get('verificationCode')
    if not email or not token:
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # retrieve the user
    user = util.find_user_by_email_or_guid(None, email, username_only=False)
    if not user:
        raise APIException(detail=messages.EMAIL_NOT_FOUND)

    # check the token and its verification
    if token not in user.email_verifications:
        raise PermissionDenied(detail=messages.INVALID_CODE)
    verification = user.email_verifications[token]
    email = verification['email']
    provider = verification['external_identity'].keys()[0]
    identity = verification['external_identity'][provider].keys()[0]
    if provider not in user.external_identity:
        raise PermissionDenied(detail=messages.INVALID_CODE)

    external_identity_status = user.external_identity[provider][identity]
    util.ensure_external_identity_uniqueness(provider, identity, user)

    # register/update user, set identity status to verified, clear pending verifications and send emails
    if not user.is_registered:
        user.register(email)
    if not user.emails.filter(address=email.lower()):
        user.emails.create(address=email.lower())
    user.date_last_logged_in = timezone.now()
    user.external_identity[provider][identity] = 'VERIFIED'
    user.social[provider.lower()] = identity
    del user.email_verifications[token]
    if external_identity_status == 'CREATE':
        send_mail(to_addr=user.username, mail=WELCOME, mimetype='html', user=user)
    elif external_identity_status == 'LINK':
        send_mail(to_addr=user.username, mail=EXTERNAL_LOGIN_LINK_SUCCESS, user=user, external_id_provider=provider)

    # generate v1 key for CAS login
    user.verification_key = generate_verification_key(verification_type=None)
    user.save()

    return user, external_identity_status


def send_password_reset_email(credential):
    """
    Find account by email and verify if the user is eligible for reset password. If so, send the verification email
    if user hasn't recently make the same request.

    :param credential: the user
    :return: the user with updated pending password reset verification
    :raises: ValidationError, PermissionDenied, APIException
    """

    # check required fields
    email = credential.get('email')
    if not email:
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # retrieve the user
    user = util.find_user_by_email_or_guid(None, email, username_only=False)
    if not user:
        raise PermissionDenied(detail=messages.EMAIL_NOT_FOUND)

    # check throttle
    if not throttle_period_expired(user.email_last_sent, web_settings.SEND_EMAIL_THROTTLE):
        raise PermissionDenied(detail=messages.EMAIL_THROTTLE_ACTIVE)

    # check user status
    if util.is_user_inactive(user):
        raise PermissionDenied(detail=messages.ACCOUNT_NOT_ELIGIBLE)

    # generate v2 key for reset password and send
    user.verification_key_v2 = generate_verification_key(verification_type='password')
    token = user.verification_key_v2.get('token')
    send_mail(to_addr=email, mail=FORGOT_PASSWORD, user=user, verification_code=token)
    user.email_last_sent = timezone.now()
    user.save()

    return user, None


def reset_password(credentials):
    """
    Reset password for eligible OSF account.

    :param credentials: the user's information
    :return: the user
    :raises: ValidationError, PermissionDenied, APIException
    """

    # check required fields
    user_id = credentials.get('userId')
    email = credentials.get('email')
    token = credentials.get('verificationCode')
    password = credentials.get('password')
    if not ((email or user_id) and token and password):
        raise ValidationError(detail=messages.INVALID_REQUEST)

    # retrieve the user
    user = util.find_user_by_email_or_guid(user_id, email, username_only=False)
    if not user:
        raise ValidationError(detail=messages.USER_NOT_FOUND)

    # check to token
    if not user.verify_password_token(token):
        raise PermissionDenied(detail=messages.INVALID_CODE)

    # reset password
    try:
        user.set_password(password)
    except ChangePasswordError:
        raise ValidationError(detail=messages.PASSWORD_SAME_AS_EMAIL)

    # clear v2 key for password reset
    user.verification_key_v2 = {}

    # generate v1 key for CAS login
    user.verification_key = generate_verification_key(verification_type=None)
    user.save()

    return user
