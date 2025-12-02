from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from .celery_task import Celery_send_mail
from .models import *

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="email already exists")]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    referral_code_used = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'phone_number', 'password', 'password2', 'referral_code_used']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # referral_code = validated_data.pop('referral_code_used', None)
        referral_code = self.context.get("referral_code_used")

        referrer = None
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
            except CustomUser.DoesNotExist:
                raise ValidationError({"referral_code_used": "Invalid referral code."})

        # Create the user
        user = CustomUser.objects.create_user(**validated_data)
        user.is_active = False

        # Link valid referrer
        if referrer:
            referrer.favorite_item += 1
            referrer.save()
            user.referred_by = referral_code

        user.save()

        # generate otp
        active_code = PasswordResetCode.objects.create(user=user)
        Celery_send_mail.delay(
            email=user.email,
            subject="Activate Your Account – Action Required",
            message=(
                f"Hello Sir/Madam,\n\n"
                f"Thank you for registering. Please use the code below to activate your account:\n\n"
                f"Activation Code: {active_code.code}\n\n"
                f"If you didn’t request this, you can ignore this email.\n\n"
                f"Thanks,\n"
                f"Support Team"
            )
        )
        return user


class VerifyActiveCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
            reset_code = PasswordResetCode.objects.get(user=user, code=attrs['code'], is_used=False)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification code.")

        if reset_code.is_expired():
            raise serializers.ValidationError("Verification code has expired.")

        self.user = user
        self.reset_code = reset_code
        return attrs

    def save(self):
        self.user.is_active = True
        self.user.save()
        self.reset_code.is_used = True
        self.reset_code.save()
        return self.user


class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No user with this email exists.")
        if user.is_active:
            raise serializers.ValidationError("User is already active.")
        self.user = user
        return value

    def save(self):
        # Create a new verification code
        reset_code = PasswordResetCode.objects.create(user=self.user)

        # Send email
        self.user.email_user(
            subject="Resend Verification Code",
            message=f"Your new verification code is: {reset_code.code}",
        )
        return self.user


# for forgot password
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        reset_code = PasswordResetCode.objects.create(user=user)
        # Send reset code via email
        Celery_send_mail.delay(
            email=user.email,
            message=(
                f"Hello Sir/Madam,\n\n"
                f"We received a request to reset your password. "
                f"Use the code below to reset your password:\n\n"
                f"Password Reset Code: {reset_code.code}\n\n"
                f"If you didn’t request this, you can ignore this email.\n\n"
                f"Thanks,\n"
                f"Support Team"
            ),
            subject="Reset Your Password – Action Required"
        )
        return user


class VerifyResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
            reset_code = PasswordResetCode.objects.get(user=user, code=attrs['code'], is_used=False)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset code.")

        # Optional: check expiry
        if reset_code.is_expired():
            raise serializers.ValidationError("Reset code has expired.")

        # Store for view use
        self.user = user
        self.reset_code = reset_code
        return attrs


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
            reset_code = PasswordResetCode.objects.get(user=user, code=attrs['code'], is_used=False)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification code.")

        if reset_code.is_expired():
            raise serializers.ValidationError("Verification code has expired.")

        self.user = user
        self.reset_code = reset_code
        return attrs

    def save(self):
        # Activate user
        self.user.is_active = True
        self.user.is_staff = True
        self.user.save()
        # Mark code as used
        self.reset_code.is_used = True
        self.reset_code.save()
        return self.user


class VerfifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
            reset_code = PasswordResetCode.objects.get(user=user, code=attrs['code'], is_used=False)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification code.")

        if reset_code.is_expired():
            raise serializers.ValidationError("Verification code has expired.")

        self.user = user
        self.reset_code = reset_code
        return attrs

    def save(self):
        self.user.is_active = False
        self.user.save()
        self.reset_code.is_used = False
        self.reset_code.save()
        return self.user


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "Password fields didn't match."})

        try:
            user = User.objects.get(email=attrs['email'])
            reset_code = PasswordResetCode.objects.get(user=user, code=attrs['code'], is_used=False)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset code.")

        if reset_code.is_expired():
            raise serializers.ValidationError("Reset code has expired.")

        self.user = user
        self.reset_code = reset_code
        return attrs

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        self.reset_code.is_used = True
        self.reset_code.save()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from the old password."})

        # Optional: enforce Django's password validators (e.g. min length, complexity)
        validate_password(data['new_password'], self.context['request'].user)

        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'phone_number', 'profile_picture', 'is_active']
        read_only_fields = ['id']


class UpdateProfileSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'profile_picture', 'old_password', 'new_password']

    def validate(self, attrs):
        user = self.instance
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')

        if old_password or new_password:
            if not old_password:
                raise serializers.ValidationError({"old_password": "Old password is required to set a new password."})
            if not new_password:
                raise serializers.ValidationError({"new_password": "New password is required."})
            if not check_password(old_password, user.password):
                raise serializers.ValidationError({"old_password": "Old password is incorrect."})
            password_validation.validate_password(new_password, user)

        return attrs

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)

        old_password = validated_data.get('old_password')
        new_password = validated_data.get('new_password')

        if old_password and new_password:
            if not check_password(old_password, instance.password):
                raise serializers.ValidationError({"old_password": "Old password is incorrect."})
            password_validation.validate_password(new_password, instance)
            instance.set_password(new_password)

        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id',
                  'email',
                  'full_name',
                  'phone_number',
                  'profile_picture',
                  'is_staff',
                  'is_active',
                  'is_superuser'
                  ]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id',
                  'email',
                  'full_name',
                  'phone_number',
                  'profile_picture',
                  'is_active'
                  ]



class CreateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="email already exists")]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ['profile_picture','full_name', 'email', 'phone_number', 'is_superuser', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            profile_picture=validated_data.get('profile_picture', None),
            email=validated_data['email'],
            full_name=validated_data.get('full_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            password=validated_data['password'],
            is_staff=True,
            is_active=True,
            is_superuser=validated_data.get('is_superuser', False),
        )
        return user
    
    

class ProjectCretientialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCretientials
        fields = [
            'id',
            'OPENAI_API_KEY',
            'STRIPE_PUBLISHABLE_KEY',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
