from breathecode.utils.validation_exception import ValidationException
import logging, json
from slugify import slugify
from breathecode.utils import APIException
from breathecode.authenticate.models import CredentialsGithub
from .models import Asset, AssetTranslation, AssetTechnology, AssetAlias
from github import Github

logger = logging.getLogger(__name__)


def create_asset(data, asset_type):
    slug = data['slug']

    aa = AssetAlias.objects.filter(slug=slug).first()
    if aa is not None:
        raise APIException('Asset with this alias ' + slug + ' alrady exists')

    a = Asset.objects.filter(slug=slug).first()
    if a is None:
        a = Asset(slug=slug, asset_type=asset_type)
        logger.debug(f'Adding asset project {a.slug}')
    else:
        logger.debug(f'Updating asset project {slug}')

    a.title = data['title']
    a.url = data['repository']
    a.readme_url = data['readme']

    if 'intro' in data:
        a.intro_video_url = data['intro']
    if 'language' in data:
        a.lang = data['language']
    if 'description' in data:
        a.description = data['description']
    if 'duration' in data:
        a.duration = data['duration']
    if 'solution_url' in data:
        a.duration = data['solution']
    if 'difficulty' in data:
        a.difficulty = data['difficulty']
    if 'graded' in data:
        a.graded = data['graded']
    if 'video-id' in data:
        a.solution_video_url = 'https://www.youtube.com/watch?v=' + str(
            data['video-id'])
    if 'preview' in data:
        a.preview = data['preview']
    if 'video-solutions' in data:
        a.with_solutions = data['video-solutions']

    a.save()

    if 'translations' in data:
        for lan in data['translations']:
            if lan == 'en':
                lan = 'us'  # english is really USA
            l = AssetTranslation.objects.filter(slug=lan).first()
            if l is not None:
                if a.translations.filter(slug=lan).first() is None:
                    a.translations.add(l)
            else:
                logger.debug(
                    f'Ignoring language {lan} because its not added as a possible AssetTranslation'
                )

    aa = AssetAlias(slug=slug, asset=a)
    aa.save()


def sync_with_github(asset_slug, author_id=None):

    try:

        asset = Asset.objects.filter(slug=asset_slug).first()
        if asset is None:
            raise Exception(
                f'Asset with slug {asset_slug} not found when attempting to sync with github'
            )

        if asset.author is not None:
            author_id = asset.author.id

        if author_id is None:
            raise Exception(
                f'System does not know what github credentials to use to retrive asset info for: {asset_slug}'
            )

        org_name, repo_name = get_url_info(asset.url)

        credentials = CredentialsGithub.objects.filter(
            user__id=author_id).first()
        if credentials is None:
            raise Exception(
                f'Github credentials for this user {author_id} not found when sync asset {asset_slug}'
            )

        g = Github(credentials.token)
        repo = g.get_repo(f'{org_name}/{repo_name}')
        readme_file = repo.get_contents('README.md')

        learn_file = None
        try:
            learn_file = repo.get_contents('learn.json')
        except:
            try:
                learn_file = repo.get_contents('.learn/learn.json')
            except:
                try:
                    learn_file = repo.get_contents('bc.json')
                except:
                    try:
                        learn_file = repo.get_contents('.learn/bc.json')
                    except:
                        raise Exception(
                            'No configuration learn.json or bc.json file was found'
                        )

        asset.readme = str(readme_file.content)

        if learn_file is not None:
            config = json.loads(learn_file.decoded_content.decode('utf-8'))
            asset.config = config
            if 'title' in config:
                asset.title = config['title']
            if 'description' in config:
                asset.description = config['description']

            if 'preview' in config:
                asset.preview = config['preview']
            else:
                raise Exception(f'Missing preview URL')

            if 'video-id' in config:
                asset.solution_video_url = 'https://www.youtube.com/watch?v=' + str(
                    config['video-id'])
                asset.with_video = True

            if 'duration' in config:
                asset.duration = config['duration']
            if 'difficulty' in config:
                asset.difficulty = config['difficulty']
            if 'solution' in config:
                asset.solution = config['solution']
                asset.with_solutions = True

            if 'language' in config:
                asset.lang = config['language']
            elif 'syntax' in config:
                asset.lang = config['syntax']

            if 'translations' in config:
                for lang in config['translations']:
                    language = AssetTranslation.objects.filter(
                        slug__iexact=lang).first()
                    if language is None:
                        raise Exception(f"Language '{lang}' not found")
                    asset.translations.add(language)

            if 'technologies' in config:
                for tech_slug in config['technologies']:
                    _slug = slugify(tech_slug)
                    technology = AssetTechnology.objects.filter(
                        slug__iexact=_slug).first()
                    if technology is None:
                        technology = AssetTechnology(slug=_slug,
                                                     title=tech_slug)
                        technology.save()
                    asset.technologies.add(technology)

        asset.status_text = 'Successfully Synched'
        asset.status = 'OK'
        asset.save()
    except Exception as e:
        asset.status_text = str(e)
        asset.status = 'ERROR'
        asset.save()
        logger.error(f'Error updating {asset.slug} from github: ' + str(e))

    logger.debug(f'Successfully re-synched asset {asset_slug} with github')
    return asset.status


def get_url_info(url: str):
    last_slash_index = url.rfind('/')
    last_suffix_index = url.rfind('.git')
    if last_suffix_index < 0:
        last_suffix_index = len(url)

    if last_slash_index < 0 or last_suffix_index <= last_slash_index:
        raise Exception('Badly formatted url {}'.format(url))

    repo_name_position = last_slash_index + 1
    repo_name = url[repo_name_position:last_suffix_index]

    last_slash_index = url[0:repo_name_position - 2].rfind('/')
    org_name = url[last_slash_index + 1:repo_name_position - 1]

    return org_name, repo_name


def generate_learn_json(asset_slug, author_id=None):

    try:

        asset = Asset.objects.filter(slug=asset_slug).first()
        if asset is None:
            raise Exception(
                f'Asset with slug {asset_slug} not found when attempting to sync with github'
            )

        if asset.author is not None:
            author_id = asset.author.id

        if author_id is None:
            raise Exception(
                f'System does not know what github credentials to use to retrive asset info for: {asset_slug}'
            )

        org_name, repo_name = get_url_info(asset.url)

        credentials = CredentialsGithub.objects.filter(
            user__id=author_id).first()
        if credentials is None:
            raise Exception(
                f'Github credentials for this user {author_id} not found when sync asset {asset_slug}'
            )

        g = Github(credentials.token)
        repo = g.get_repo(f'{org_name}/{repo_name}')
        readme_file = repo.get_contents('README.md')

        es_readme_file, it_readme_file, preview, graded, solution, learn_file = None

        try:
            es_readme_file = repo.get_contents('README.es.md')
        except:
            logger.debug('No README.es.md found')

        try:
            it_readme_file = repo.get_contents('README.it.md')
        except:
            logger.debug('No README.it.md found')

        try:
            preview = repo.get_contents('preview.png')
        except:
            logger.debug('No preview.png found')

        try:
            graded = repo.get_contents('test.py')
        except:
            try:
                graded = repo.get_contents('test.js')
            except:
                try:
                    graded = repo.get_contents('test.jsx')
                except:
                    logger.debug('No test.py, test.js, or test.jsx found')

        try:
            solution = repo.get_branch(branch='solution')
        except:
            logger.debug('No solution branch found')

        try:
            learn_file = repo.get_contents('learn.json')
        except:
            try:
                learn_file = repo.get_contents('.learn/learn.json')
            except:
                try:
                    learn_file = repo.get_contents('bc.json')
                except:
                    try:
                        learn_file = repo.get_contents('.learn/bc.json')
                    except:
                        raise Exception(
                            'No configuration learn.json or bc.json file was found'
                        )

        if learn_file is not None:
            config = json.loads(learn_file.decoded_content.decode('utf-8'))
            updated_config = {}
            if 'title' in config:
                updated_config['title'] = config['title']
            if 'slug' in config:
                updated_config['slug'] = config['slug']
            if 'status' in config:
                updated_config['status'] = config['status']
            if solution is not None:
                updated_config['solution'] = solution['path']
            if preview is not None:
                updated_config['preview'] = preview['path']
            if 'difficulty' in config:
                updated_config['difficulty'] = config['difficulty']
            if 'technologies' in config:
                updated_config['technologies'] = config['technologies']
            if 'language' in config:
                updated_config['language'] = config['language']
            if 'duration' in config:
                updated_config['duration'] = config['duration']
            if graded is not None:
                updated_config['graded'] = True
            if readme_file is not None:
                updated_config['translations'] = ['us']
            if es_readme_file is not None:
                updated_config['translations'].append('es')
            if it_readme_file is not None:
                updated_config['translations'].append('it')
            if 'description' in config:
                updated_config['description'] = config['description']
            if 'talents' in config:
                updated_config['talents'] = config['talents']

        updated_learn_file = json.dumps(updated_config)

        try:
            source_branch = repo.get_branch('master')
        except:
            try:
                source_branch = repo.get_branch('main')
            except:
                raise ValidationException(
                    'Source branch invalid, please create master branch')

        if source_branch is not None:
            repo.create_git_ref(ref='refs/heads/learn_json',
                                sha=source_branch.commit.sha)

        repo.update_file(learn_file.path,
                         'more tests',
                         updated_learn_file,
                         learn_file.sha,
                         branch='learn_json')

        return repo.create_pull(
            title='Updated learn.json based on content in repo',
            body='',
            head='learn_json',
            base='master')

    except Exception as e:
        logger.error(f'Error generating learn_json from github: ' + str(e))
        raise ValidationException('')
