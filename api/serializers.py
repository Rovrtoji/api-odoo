from rest_framework import serializers

class CreateUserCoreSerializer(serializers.Serializer):
    name = serializers.CharField()
    login = serializers.CharField()
    email = serializers.EmailField()
    password_new = serializers.CharField()
    tipo = serializers.CharField()
