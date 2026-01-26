# serializers.py
from rest_framework import serializers
from .models import Category, State

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class StateSerializer(serializers.ModelSerializer):
    category_set = CategorySerializer(many=True)

    class Meta:
        model = State
        fields = ['id', 'name', 'category_set']
