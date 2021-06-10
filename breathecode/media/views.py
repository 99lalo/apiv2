import os, hashlib, requests, logging
from breathecode.services.google_cloud.function import Function
from django.shortcuts import redirect
from breathecode.media.models import Media, Category, MediaResolution
from breathecode.utils import GenerateLookupsMixin, num_to_roman
from rest_framework.views import APIView
from breathecode.utils import ValidationException, capable_of, HeaderLimitOffsetPagination
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import StreamingHttpResponse
from django.db.models import Q
from breathecode.media.serializers import (
    GetMediaSerializer,
    MediaSerializer,
    MediaPUTSerializer,
    GetCategorySerializer,
    CategorySerializer
)
from slugify import slugify


logger = logging.getLogger(__name__)
MIME_ALLOW = ["image/png", "image/svg+xml",
              "image/jpeg", "image/gif", "video/quicktime", "video/mp4", "audio/mpeg", "application/pdf", "image/jpg"]


def media_gallery_bucket():
    return os.getenv('MEDIA_GALLERY_BUCKET')


class MediaView(APIView, HeaderLimitOffsetPagination, GenerateLookupsMixin):
    # permission_classes = [AllowAny]

    @capable_of('read_media')
    def get(self, request, media_id=None, media_slug=None, media_name=None, academy_id=None):
        if media_id:
            item = Media.objects.filter(id=media_id).first()

            if not item:
                raise ValidationException('Media not found', code=404)

            serializer = GetMediaSerializer(item, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if media_slug:
            item = Media.objects.filter(slug=media_slug).first()

            if not item:
                raise ValidationException('Media not found', code=404)

            serializer = GetMediaSerializer(item, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if media_name:
            item = Media.objects.filter(name=media_name).first()

            if not item:
                raise ValidationException('Media not found', code=404)

            serializer = GetMediaSerializer(item, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        lookups = self.generate_lookups(
            request,
            many_fields=['mime', 'name', 'slug', 'id'],
            many_relationships=['academy']
        )

        items = Media.objects.filter(**lookups)

        # filter media by all categories, if one request have category 1 and 2,
        # if just get the media is in all the categories passed
        categories = request.GET.get('categories')
        if categories:
            categories = categories.split(',')
            for category in categories:
                items = items.filter(categories__pk=category)

        tp = request.GET.get('type')
        if tp:
            items = items.filter(mime__icontains=tp)

        like = request.GET.get('like')
        if like:
            items = items.filter(Q(name__icontains=like) |
                                 Q(slug__icontains=like))

        sort = request.GET.get('sort', '-created_at')
        items = items.order_by(sort)

        page = self.paginate_queryset(items, request)
        serializer = GetMediaSerializer(page, many=True)

        if self.is_paginate(request):
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)

    @capable_of('crud_media')
    def put(self, request, media_id=None, academy_id=None):
        data = Media.objects.filter(id=media_id).first()
        if not data:
            raise ValidationException('Media not found', code=404)

        serializer = MediaSerializer(data, data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @capable_of('crud_media')
    def delete(self, request, media_id=None, academy_id=None):
        from ..services.google_cloud import Storage

        data = Media.objects.filter(
            id=media_id, academy__id=academy_id).first()
        if not data:
            raise ValidationException('Media not found', code=404)

        url = data.url
        hash = data.hash
        data.delete()

        if not Media.objects.filter(hash=hash).count():
            storage = Storage()
            file = storage.file(media_gallery_bucket(), url)
            file.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class CategoryView(APIView, HeaderLimitOffsetPagination):
    # permission_classes = [AllowAny]

    @capable_of('read_media')
    def get(self, request, category_id=None, category_slug=None, academy_id=None):
        if category_id:
            item = Category.objects.filter(id=category_id).first()

            if not item:
                raise ValidationException('Category not found', code=404)

            serializer = GetCategorySerializer(item, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if category_slug:
            item = Category.objects.filter(slug=category_slug).first()

            if not item:
                raise ValidationException('Category not found', code=404)

            serializer = GetCategorySerializer(item, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        items = Category.objects.filter()

        page = self.paginate_queryset(items, request)
        serializer = GetCategorySerializer(page, many=True)

        if self.is_paginate(request):
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)

    @capable_of('crud_media')
    def post(self, request, academy_id=None):
        serializer = CategorySerializer(data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @capable_of('crud_media')
    def put(self, request, category_slug=None, academy_id=None):
        data = Category.objects.filter(slug=category_slug).first()
        if not data:
            raise ValidationException('Category not found', code=404)

        serializer = CategorySerializer(data, data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @capable_of('crud_media')
    def delete(self, request, category_slug=None, academy_id=None):
        data = Category.objects.filter(slug=category_slug).first()
        if not data:
            raise ValidationException('Category not found', code=404)

        if Media.objects.filter(categories__slug=category_slug).count():
            raise ValidationException('Category contain some medias', code=403)

        data.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class UploadView(APIView):
    parser_classes = [MultiPartParser, FileUploadParser]
    # permission_classes = [AllowAny]

    # upload was separated because in one moment I think that the serializer
    # not should get many create and update operations together
    def upload(self, request, academy_id=None, update=False):
        from ..services.google_cloud import Storage

        files = request.data.getlist('file')
        names = request.data.getlist('name')
        result = {
            'data': [],
            'instance': [],
        }

        file = request.data.get('file')
        slugs = []

        if not file:
            raise ValidationException('Missing file in request', code=400)

        if not len(files):
            raise ValidationException('empty files in request')

        if not len(names):
            for file in files:
                names.append(file.name)

        elif len(files) != len(names):
            raise ValidationException('numbers of files and names not match')

        # files validation below
        for index in range(0, len(files)):
            file = files[index]
            if file.content_type not in MIME_ALLOW:
                raise ValidationException(
                    f'You can upload only files on the following formats: {",".join(MIME_ALLOW)}')

        for index in range(0, len(files)):
            file = files[index]
            name = names[index] if len(names) else file.name
            file_bytes = file.read()
            hash = hashlib.sha256(file_bytes).hexdigest()
            slug = slugify(name)

            slug_number = Media.objects.filter(slug__startswith=slug).exclude(hash=hash).count() + 1
            if slug_number > 1:
                while True:
                    roman_number = num_to_roman(slug_number, lower=True)
                    slug = f'{slug}-{roman_number}'
                    if not slug in slugs:
                        break
                    slug_number = slug_number + 1

            slugs.append(slug)
            data = {
                'hash': hash,
                'slug': slug,
                'mime': file.content_type,
                'name': name,
                'categories': [],
                'academy': academy_id,
            }

            # it is receive in url encoded
            if 'categories' in request.data:
                data['categories'] = request.data['categories'].split(',')
            elif 'Categories' in request.headers:
                data['categories'] = request.headers['Categories'].split(',')

            media = Media.objects.filter(
                hash=hash, academy__id=academy_id).first()
            if media:
                data['id'] = media.id

                url = Media.objects.filter(hash=hash).values_list(
                    'url', flat=True).first()
                if url:
                    data['url'] = url

            else:
                url = Media.objects.filter(hash=hash).values_list(
                    'url', flat=True).first()
                if url:
                    data['url'] = url

                else:
                    # upload file section
                    storage = Storage()
                    cloud_file = storage.file(media_gallery_bucket(), hash)
                    cloud_file.upload(file_bytes)
                    data['url'] = cloud_file.url()
                    data['thumbnail'] = data['url'] + '-thumbnail'

            result['data'].append(data)

        from django.db.models import Q
        query = None
        datas_with_id = [x for x in result['data'] if 'id' in x]
        for x in datas_with_id:
            if query:
                query = query | Q(id=x['id'])
            else:
                query = Q(id=x['id'])

        if query:
            result['instance'] = Media.objects.filter(query)

        return result

    @capable_of('crud_media')
    def put(self, request, academy_id=None):
        upload = self.upload(request, academy_id, update=True)
        serializer = MediaPUTSerializer(
            upload['instance'], data=upload['data'], context=upload['data'], many=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaskingUrlView(APIView):
    parser_classes = [FileUploadParser]
    permission_classes = [AllowAny]

    def get(self, request, media_id=None, media_slug=None):
        lookups = {}
        if media_id:
            lookups['id'] = media_id
        elif media_slug:
            lookups['slug'] = media_slug

        width = request.GET.get('width')
        height = request.GET.get('height')

        media = Media.objects.filter(**lookups).first()
        if not media:
            raise ValidationException('Resource not found', code=404)

        url = media.url

        if width and height:
            raise ValidationException(
                'You need to pass either width or height, not both, in order to avoid losing aspect ratio',
                code=400,
                slug='width-and-height-in-querystring')

        if (width or height) and not media.mime.startswith('image/'):
            raise ValidationException(
                'cannot resize this resource',
                code=400,
                slug='cannot-resize-media')

        # register click
        media.hits = media.hits + 1
        media.save()

        resolution = MediaResolution.objects.filter(
            Q(width=width) | Q(height=height),
            hash=media.hash).first()

        if (width or height) and not resolution:
            func = Function(
                region='us-central1',
                project_id='breathecode-197918',
                name='resize-image')

            res = func.call({
                'width': width,
                'height': height,
                'filename': media.hash,
                'bucket': media_gallery_bucket(),
            })

            if not res['status_code'] == 200 or not res['message'] == 'Ok':
                if 'message' in res:
                    raise ValidationException(
                        res['message'],
                        code=500,
                        slug='cloud-function-bad-input')

                raise ValidationException(
                    'Unhandled request from cloud functions',
                    code=500,
                    slug='unhandled-cloud-function')

            width = res['width']
            height = res['height']
            resolution = MediaResolution(
                width=width,
                height=height,
                hash=media.hash)
            resolution.save()

        if (width or height):
            width = resolution.width
            height = resolution.height

            url = f'{url}-{width}x{height}'
            resolution.hits = resolution.hits + 1
            resolution.save()

        if request.GET.get('mask') != 'true':
            return redirect(url, permanent=True)

        response = requests.get(url, stream=True)
        resource = StreamingHttpResponse(
            response.raw,
            status=response.status_code,
            reason=response.reason,
        )

        header_keys = [x for x in response.headers.keys() if x !=
                       'Transfer-Encoding' and x != 'Content-Encoding' and x !=
                       'Keep-Alive' and x != 'Connection']

        for header in header_keys:
            resource[header] = response.headers[header]

        return resource
