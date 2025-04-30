

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from user import views

urlpatterns = [

                  path("admin/", admin.site.urls),
                  path("", include("user.urls")),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
admin.site.site_header = 'Recommendation System Backend Management'
admin.site.index_title = 'Home - Recommendation System'
admin.site.site_title = 'Recommendation System'
