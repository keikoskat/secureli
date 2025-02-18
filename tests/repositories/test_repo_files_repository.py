from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.repositories.repo_files import RepoFilesRepository


@pytest.fixture()
def git_not_exists_folder_path() -> MagicMock:
    git_folder_path = MagicMock()
    git_folder_path.exists.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = git_folder_path
    return mock_folder_path


@pytest.fixture()
def git_a_file_for_some_reason_folder_path() -> MagicMock:
    git_folder_path = MagicMock()
    git_folder_path.exists.return_value = True
    git_folder_path.is_dir.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = git_folder_path
    return mock_folder_path


def always_exists_path(path_str: str) -> MagicMock:
    path = Path(path_str)

    mock_stat = MagicMock()
    mock_stat.st_size = 1024

    mock_path = MagicMock()
    mock_path.parts = path.parts
    mock_path.suffix = path.suffix
    mock_path.stat.return_value = mock_stat
    mock_path.is_file.return_value = True
    mock_path.__str__.return_value = path_str
    return mock_path


def does_not_exist_path(path_str: str) -> MagicMock:
    mock_path = always_exists_path(path_str)
    mock_path.exists.return_value = False
    return mock_path


@pytest.fixture()
def good_folder_path() -> MagicMock:
    git_folder_path = MagicMock()
    git_folder_path.exists.return_value = True
    git_folder_path.is_dir.return_value = True
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = git_folder_path
    mock_folder_path.rglob.return_value = [
        always_exists_path(".invisible_folder/visible_file.txt"),
        always_exists_path(".invisible_folder/.invisible_file.txt"),
        always_exists_path("visible_folder/.invisible_file.txt"),
        always_exists_path(
            "visible_folder/visible_file.txt"
        ),  # The one file we should count!
    ]
    return mock_folder_path


@pytest.fixture()
def mock_open_resource(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("builtins.open", mocker.mock_open(read_data="sample_data"))


@pytest.fixture()
def mock_open_resource_with_io_error(mocker: MockerFixture) -> MagicMock:
    mock_open_with_error = mocker.mock_open(read_data="sample_data")
    mock_open_with_error.side_effect = IOError("Generic I/O error")
    return mocker.patch("builtins.open", mock_open_with_error)


@pytest.fixture()
def mock_open_resource_with_value_error(mocker: MockerFixture) -> MagicMock:
    mock_open_with_error = mocker.mock_open(read_data="sample_data")
    mock_open_with_error.side_effect = ValueError("Generic value error")
    return mocker.patch("builtins.open", mock_open_with_error)


@pytest.fixture()
def good_file_path(mock_open_resource) -> MagicMock:
    return always_exists_path("folder/file.txt")


@pytest.fixture()
def nonexistent_file_path(mock_open_resource) -> MagicMock:
    mock_file_path = always_exists_path("folder/file.txt")
    mock_file_path.exists.return_value = False
    return mock_file_path


@pytest.fixture()
def too_big_file_path(mock_open_resource) -> MagicMock:
    mock_file_path = always_exists_path("folder/file.txt")
    mock_file_path.stat.return_value.st_size = 100000000
    return mock_file_path


@pytest.fixture()
def io_error_occurs_file_path(mock_open_resource_with_io_error) -> MagicMock:
    mock_file_path = always_exists_path("folder/file.txt")
    return mock_file_path


@pytest.fixture()
def value_error_occurs_file_path(mock_open_resource_with_value_error) -> MagicMock:
    mock_file_path = always_exists_path("folder/file.txt")
    return mock_file_path


@pytest.fixture()
def repo_files_repository() -> RepoFilesRepository:
    all_mov_files = "^(?:.+/)?[^/]*\\.mov(?:(?P<ps_d>/).*)?$"
    return RepoFilesRepository(
        max_file_size=10000,
        ignored_file_extensions="",
        ignored_file_patterns=[all_mov_files],
    )


def test_that_list_repo_files_raises_value_error_without_git_repo(
    repo_files_repository: RepoFilesRepository, git_not_exists_folder_path: MagicMock
):
    with pytest.raises(ValueError):
        repo_files_repository.list_repo_files(git_not_exists_folder_path)


def test_that_list_repo_files_raises_value_error_if_dot_git_is_a_file_somehow(
    repo_files_repository: RepoFilesRepository,
    git_a_file_for_some_reason_folder_path: MagicMock,
):
    with pytest.raises(ValueError):
        repo_files_repository.list_repo_files(git_a_file_for_some_reason_folder_path)


def test_that_list_repo_files_filters_out_invisible_files_and_folders(
    repo_files_repository: RepoFilesRepository, good_folder_path: MagicMock
):
    files = repo_files_repository.list_repo_files(good_folder_path)

    assert len(files) == 1
    assert str(files[0]) == "visible_folder/visible_file.txt"


def test_that_load_file_loads_data(
    repo_files_repository: RepoFilesRepository, good_file_path: MagicMock
):
    data = repo_files_repository.load_file(good_file_path)

    assert data == "sample_data"


def test_that_load_file_raises_value_error_for_nonexistent_file(
    repo_files_repository: RepoFilesRepository, nonexistent_file_path: MagicMock
):
    with pytest.raises(ValueError):
        repo_files_repository.load_file(nonexistent_file_path)


def test_that_load_file_raises_value_error_for_file_that_is_too_big(
    repo_files_repository: RepoFilesRepository, too_big_file_path: MagicMock
):
    with pytest.raises(ValueError):
        repo_files_repository.load_file(too_big_file_path)


def test_that_load_file_raises_value_error_for_file_if_io_error_occurs(
    repo_files_repository: RepoFilesRepository, io_error_occurs_file_path: MagicMock
):
    with pytest.raises(ValueError):
        repo_files_repository.load_file(io_error_occurs_file_path)


def test_that_load_file_raises_value_error_for_file_if_value_error_occurs(
    repo_files_repository: RepoFilesRepository, value_error_occurs_file_path: MagicMock
):
    with pytest.raises(ValueError):
        repo_files_repository.load_file(value_error_occurs_file_path)
