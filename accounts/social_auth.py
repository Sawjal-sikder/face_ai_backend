import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt
import time

User = get_user_model()


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        auth_code = request.data.get("auth_code")
        if not auth_code:
            return Response({"error": "auth_code is required"}, status=400)

        # Exchange auth_code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": auth_code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": "",  # can be empty for mobile apps
            "grant_type": "authorization_code",
        }

        try:
            token_resp = requests.post(token_url, data=data)
            token_resp.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": "Failed to exchange auth_code", "details": str(e)}, status=400)

        token_data = token_resp.json()
        id_token_value = token_data.get("id_token")
        access_token = token_data.get("access_token")

        if not id_token_value:
            return Response({"error": "No id_token received"}, status=400)

        # Verify ID token
        try:
            id_info = id_token.verify_oauth2_token(
                id_token_value, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            email = id_info.get("email")
            name = id_info.get("name")
        except Exception as e:
            return Response({"error": "Invalid ID token", "details": str(e)}, status=400)

        # Get or create user
        user, _ = User.objects.get_or_create(email=email, defaults={"full_name": name})

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Google login successful",
            "email": email,
            "full_name": name,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "google_access_token": access_token
        })
        
        
class AppleLoginView(APIView):
    permission_classes = [AllowAny]
    
    
    def post(self, request):
        auth_code = request.data.get("auth_code")

        if not auth_code:
            return Response({"error": "auth_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Exchange auth_code with Apple
        token_url = "https://appleid.apple.com/auth/token"
        data = {
            "client_id": settings.APPLE_CLIENT_ID,
            "client_secret": generate_apple_client_secret(),
            "code": auth_code,
            "grant_type": "authorization_code",
        }

        resp = requests.post(token_url, data=data)
        if resp.status_code != 200:
            return Response({"error": "Failed to get token", "details": resp.json()}, status=status.HTTP_400_BAD_REQUEST)

        token_data = resp.json()
        id_token_value = token_data.get("id_token")
        access_token = token_data.get("access_token")

        if not id_token_value:
            return Response({"error": "No id_token received"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Decode ID token (JWT)
        try:
            decoded = jwt.decode(id_token_value, options={"verify_signature": False})
            email = decoded.get("email")
            name = decoded.get("name", "")
        except Exception as e:
            return Response({"error": "Invalid id_token", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": name or email.split("@")[0]}
        )

        # Step 4: Issue JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Apple login successful",
            "email": email,
            "name": name,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "apple_access_token": access_token,  # optional
        })
        
        
        
        
def generate_apple_client_secret():
    headers = {
        "kid": settings.APPLE_KEY_ID,
        "alg": "ES256"
    }

    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,  
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID,
    }

    client_secret = jwt.encode(
        payload,
        settings.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers=headers
    )

    return client_secret