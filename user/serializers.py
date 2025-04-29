from rest_framework import serializers

from user.models import Movie, Tags, Rate


class MovieSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Movie
        fields = ['image_link', 'name']


class TagsSerializer(serializers.ModelSerializer):
    movie_count = serializers.IntegerField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Tags
        fields = ['name', 'movie_count', 'avg_rating']


class TopRatedMovieSerializer(serializers.ModelSerializer):
    avg_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Movie
        fields = ['name', 'avg_rating', 'rating_count']
