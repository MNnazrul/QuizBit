from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Question, AnswerOption

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User 
        fields = ['id', 'username', 'password', 'email']

        extra_kwargs = {
            'password': {'write_only': True},
        }


class AnswerOptionSerializer(serializers.ModelSerializer):
    is_correct = serializers.BooleanField(write_only=True)
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct']
        def to_representation(self, instance):
            representation = super().to_representation(instance)
            representation.pop('is_correct', None)  # Remove 'is_correct' from the response
            return representation
        # def to_representation(self, instance):
        #     representation = super().to_representation(instance)
        #     representation.pop('is_correct', None) 
        #     return representation

class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'created_at', 'updated_at', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        question = Question.objects.create(**validated_data)
        for option_data in options_data:
            AnswerOption.objects.create(question=question, **option_data)
        
        return question