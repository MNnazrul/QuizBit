from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer, QuestionSerializer, AnswerOptionSerializer
from .models import *

# ============ User singup, login, token authentication, last authenticate user done =========
@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({
            'details': "Not found",
            'status': 400,
        })
    serializer = UserSerializer(instance=user)
    token, created = Token.objects.get_or_create(user=user)
    return Response({
            'token': token.key,
            'user': serializer.data,
        }, status=status.HTTP_200_OK)

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


@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def test_token(request):
    return Response({"Passed for {}".format(request.user.username)})

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


# showing all questions.

class QuestionListView(generics.ListAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    

# getting last authenticated user.
@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def last_auth(request):
    return Response({
        'user': request.user.username
    })


# submiting Answer
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    user = request.user
    question_id = request.data.get('question_id')
    option_id = request.data.get('option_id')
    try:
        question = Question.objects.get(id = question_id)
        chosen_option = AnswerOption.objects.get(id = option_id, question=question)
    except Question.DoesNotExist:
        return Response({
            "error": "Question not found",
        }, status=404)
    except AnswerOption.DoesNotExist:
        return Response({
            "error": "Invalid option",
        }, status=400)
    
    is_correct = chosen_option.is_correct

    submission = Submission.objects.create(
        user = user,
        question = question,
        chosen_option = chosen_option,
        is_correct = is_correct
    )
    return Response({
        "question_id": submission.question.id,
        "chosen_option": submission.chosen_option.id,
        "is_correct": submission.is_correct,
        "full_question": {
            "question": question.text,
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "is_correct": option.is_correct
                } for option in question.options.all()
            ]
        }
    }, status = 200)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def user_records(request):
    user = request.user
    submissions = Submission.objects.filter(user =user)
    total_attempts = submissions.count()
    correct_attemps = submissions.filter(is_correct = True).count()

    records = [
        {
            "question_id": submission.question.id,
            "chosen_option": submission.chosen_option.id,
            "is_correct": submission.is_correct,
            "submitted_at": submission.submission_time,
        } for submission in submissions
    ]

    return Response({
        "user": user.username,
        "summary": {
            "tota_attempts": total_attempts,
            "correct_attempts": correct_attemps
        }, 
        "records": records,
    }, status=200)

