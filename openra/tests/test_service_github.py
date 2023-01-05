import datetime

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from django.conf import settings
from openra.services.github import Github

class TestServiceGithub(TestCase):

    def test_will_obtain_release_data_from_github(self):
        published_date = datetime.datetime

        repo_mock = Mock()
        repo_mock.get_releases = MagicMock(
            return_value = [
                Mock(tag_name="sample1", published_at=published_date),
                Mock(tag_name="sample2", published_at=published_date)
            ]
        )

        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github()

        github._get_client = MagicMock(
            return_value = client_mock
        )

        self.assertEquals([{
                "tag":"sample1",
                "published":published_date,
            },{
                "tag":"sample2",
                "published":published_date,
            }],
            github.list_releases()
        )

        repo_mock.get_releases.assert_called_once_with()

        client_mock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )

    def test_will_return_assets_for_a_release(self):
        release_mock = Mock()

        mock_asset1 = Mock(browser_download_url="url1")
        mock_asset1.configure_mock(name="asset1")
        mock_asset2 = Mock(browser_download_url="url2")
        mock_asset2.configure_mock(name="asset2")

        release_mock.get_assets = MagicMock(
            return_value = [
                mock_asset1,
                mock_asset2,
            ]
        )

        repo_mock = Mock()
        repo_mock.get_release = MagicMock(
            return_value = release_mock
        )

        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github()

        github._get_client = MagicMock(
            return_value = client_mock
        )

        self.assertEquals([{
                "name":"asset1",
                "url":"url1",
            },{
                "name":"asset2",
                "url":"url2",
            }],
            github.get_release_assets('release_tag')
        )

        release_mock.get_assets.assert_called_once_with()

        repo_mock.get_release.assert_called_once_with(
            'release_tag'
        )

        client_mock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )

    def test_will_only_get_the_repo_once_over_multiple_calls(self):
        release_mock = Mock()
        release_mock.get_assets = MagicMock(
            return_value = []
        )
        repo_mock = Mock()
        repo_mock.get_releases = MagicMock(
            return_value = []
        )
        repo_mock.get_release = MagicMock(
            return_value = release_mock
        )
        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github()

        github._get_client = MagicMock(
            return_value = client_mock
        )

        github.list_releases()
        github.get_release_assets('sample')

        client_mock.get_repo.assert_called_once()
        repo_mock.get_releases.assert_called_once()
        repo_mock.get_release.assert_called_once()
        release_mock.get_assets.assert_called_once()
