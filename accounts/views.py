from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken , TokenError
from django.contrib.auth import authenticate
from .serializers import SignupSerializer
import redis
import os

redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    db=0,
    decode_responses=True
)

MAX_ATTEMPTS = 5
BLOCK_TIME = 60 * 15  # 15 minutes in seconds


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        redis_client.setex(
            f"refresh:{user.id}",
            60 * 60 * 24 * 7,
            refresh_token
        )

        response = Response({
            'access': access_token,
            'username': user.username,
            'role': user.role,
        }, status=status.HTTP_201_CREATED)

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
        )

        return response


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # get client IP
        ip = request.META.get('REMOTE_ADDR')
        block_key = f"login_block:{ip}"
        attempts_key = f"login_attempts:{ip}"

        # check if IP is blocked
        if redis_client.exists(block_key):
            ttl = redis_client.ttl(block_key)
            return Response(
                {'error': f'Too many failed attempts. Try again in {ttl} seconds.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # verify credentials
        user = authenticate(username=username, password=password)

        if not user:
            # increment failed attempts
            attempts = redis_client.incr(attempts_key)
            redis_client.expire(attempts_key, BLOCK_TIME)

            remaining = MAX_ATTEMPTS - int(attempts)

            if remaining <= 0:
                # block the IP
                redis_client.setex(block_key, BLOCK_TIME, '1')
                redis_client.delete(attempts_key)
                return Response(
                    {'error': 'Too many failed attempts. Blocked for 15 minutes.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            return Response(
                {'error': f'Invalid credentials. {remaining} attempts remaining.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # login successful — clear any failed attempts
        redis_client.delete(attempts_key)
        redis_client.delete(block_key)

        # generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # save refresh token to redis
        redis_client.setex(
            f"refresh:{user.id}",
            60 * 60 * 24 * 7,
            refresh_token
        )

        response = Response({
            'access': access_token,
            'username': user.username,
            'role': user.role,
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'No refresh token found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # delete refresh token from redis
        user_id = request.user.id
        redis_client.delete(f"refresh:{user_id}")

        # clear the cookie
        response = Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('refresh_token')

        return response
    

class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # read refresh token from httpOnly cookie
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'No refresh token found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # verify token signature
            token = RefreshToken(refresh_token)
            user_id = token['user_id']

            # check redis — is this token still valid
            stored_token = redis_client.get(f"refresh:{user_id}")

            if not stored_token or stored_token != refresh_token:
                return Response(
                    {'error': 'Refresh token is invalid or expired.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # generate new access token
            new_access_token = str(token.access_token)

            return Response({
                'access': new_access_token,
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response(
                {'error': 'Invalid refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )