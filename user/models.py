from datetime import datetime
from datetime import date
from django.db import models
from django.db.models import Avg
from django.db.models.fields.files import FileField
from itertools import chain


class User(models.Model):
    username = models.CharField(max_length=255, unique=True, verbose_name="Username")
    password = models.CharField(max_length=255, verbose_name="Password")
    email = models.EmailField(verbose_name="Email")
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Users"
        verbose_name = "User"

    def __str__(self):
        return self.username


class Tags(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tag", unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class UserTagPrefer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, verbose_name="User ID",
    )
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE, verbose_name='Tag Name')
    score = models.FloatField(default=0)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "Preferences"

    def __str__(self):
        return self.user.username + str(self.score)


class Movie(models.Model):
    tags = models.ManyToManyField(Tags, verbose_name='Tags', blank=True)
    collect = models.ManyToManyField(User, verbose_name="Collectors", blank=True)
    name = models.CharField(verbose_name="Movie Name", max_length=255)
    director = models.CharField(verbose_name="Director", max_length=255)
    country = models.CharField(verbose_name="Country", max_length=255)
    years = models.DateField(verbose_name='Release Date')
    leader = models.CharField(verbose_name="Lead Actors", max_length=1024)
    d_rate_nums = models.IntegerField(verbose_name="Douban Ratings Count")
    d_rate = models.CharField(verbose_name="Douban Rating", max_length=255)
    intro = models.TextField(verbose_name="Description")
    num = models.IntegerField(verbose_name="Views", default=0)
    origin_image_link = models.URLField(verbose_name='Douban Image URL', max_length=255, null=True)
    image_link = models.FileField(verbose_name="Cover Image", max_length=255, upload_to='movie_cover')
    imdb_link = models.URLField(null=True)
    douban_link = models.URLField(verbose_name='Douban URL')
    douban_id = models.CharField(verbose_name='Douban ID', max_length=128, null=True)

    @property
    def movie_rate(self):
        movie_rate = Rate.objects.filter(movie_id=self.id).aggregate(Avg('mark'))['mark__avg']
        return movie_rate or 'None'

    class Meta:
        verbose_name = "Movie"
        verbose_name_plural = "Movies"

    def __str__(self):
        return self.name

    def to_dict(self, fields=None, exclude=None):
        opts = self._meta
        data = {}
        for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
            if exclude and f.name in exclude:
                continue
            if fields and f.name not in fields:
                continue
            value = f.value_from_object(self)
            if isinstance(value, date):
                value = value.strftime('%Y-%m-%d')
            elif isinstance(f, FileField):
                value = value.url if value else None
            data[f.name] = value
        return data


class MovieUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    csv_file = models.FileField(upload_to='movie_uploads/', verbose_name="CSV File")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Upload Time")
    status = models.CharField(max_length=20, default="pending", verbose_name="Processing Status")
    processed_count = models.IntegerField(default=0, verbose_name="Processed Movies Count")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Movie Upload"
        verbose_name_plural = "Movie Uploads"
        
    def __str__(self):
        return f"{self.user.username}'s upload at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


class Rate(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Movie ID"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="User ID",
    )
    mark = models.FloatField(verbose_name="Rating")
    create_time = models.DateTimeField(verbose_name="Publication Time", auto_now_add=True)

    @property
    def avg_mark(self):
        average = Rate.objects.all().aggregate(Avg('mark'))['mark__avg']
        return average

    class Meta:
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    content = models.CharField(max_length=255, verbose_name="Content")
    create_time = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="Movie")

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"


class LikeComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='Comment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')

    class Meta:
        verbose_name = "Comment Like"
        verbose_name_plural = "Comment Likes"


class SharedRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    share_key = models.CharField(max_length=64, unique=True, verbose_name="Share Key")
    title = models.CharField(max_length=255, verbose_name="Share Title")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    movies = models.ManyToManyField(Movie, verbose_name="Shared Movies")
    shared_with = models.ManyToManyField(User, blank=True, related_name="shared_to_me", verbose_name="Shared With Users")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created Time")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    is_public = models.BooleanField(default=False, verbose_name="Public Sharing")
    
    class Meta:
        verbose_name = "Shared Recommendation"
        verbose_name_plural = "Shared Recommendations"
        
    def __str__(self):
        return f"{self.user.username}'s share: {self.title}"
