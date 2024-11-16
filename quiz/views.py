from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer, QuestionSerializer, AnswerOptionSerializer
from .models import Question, AnswerOption

# ============ User singup, login, token authentication, last authenticate user done =========
last_authenticated_username = None
@api_view(['POST'])
def login(request):
    global last_authenticated_username
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({
            'details': "Not found",
            'status': 400,
        })
    serializer = UserSerializer(instance=user)
    last_authenticated_username = user.username
    token, created = Token.objects.get_or_create(user=user)
    return Response({
            'token': token.key,
            'user': serializer.data,
        }, status=status.HTTP_200_OK)



@api_view(['GET'])
def last_authenticate_user(request):
    global last_authenticated_username
    if not last_authenticated_username:
        return Response({
            'Message': 'Not username login',
        })
    return Response({
        'User name': last_authenticated_username
    })

@api_view(['POST'])
def signup(request):

    if User.objects.filter(username=request.data['username']).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=request.data['email']).exists():
        return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = UserSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data['username'])
        user.set_password(request.data['password'])
        user.save()
        token = Token.objects.create(user = user)
        return Response({
            'token': token.key,
            'user': serializer.data,
        })
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])

def test_token(request):
    return Response({"Passed for {}".format(request.user.email)})

# ======================== end_1 =========================================


#============== add questoins, and view all question ================


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_question(request):
    
    question_data = request.data.get('question')
    options_data = request.data.get('options')

    if options_data is None:
        return Response(
            {'error': 'Options data is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(options_data) != 4:
        return Response(
            {'error': 'A question must have exactly 4 options.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    question = Question.objects.create(
        text=question_data['text']
    )

    for option in options_data:
        AnswerOption.objects.create(
            question=question,
            text=option['text'],
            is_correct=option.get('is_correct', False)  
        )
    return Response({
        'message': 'Question and options added successfully!',
        'question': {
            'text': question.text,
            'options': options_data
        }
    }, status=status.HTTP_201_CREATED)