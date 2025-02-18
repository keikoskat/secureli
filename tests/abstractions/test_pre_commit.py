from subprocess import CompletedProcess
from unittest.mock import MagicMock

import pytest
import yaml
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    PreCommitAbstraction,
    InstallFailedError,
)
from secureli.repositories.settings import (
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
)


@pytest.fixture()
def settings_dict() -> dict:
    return PreCommitSettings(
        repos=[
            PreCommitRepo(
                url="http://example-repo.com/",
                hooks=[
                    PreCommitHook(
                        id="hook-id",
                        arguments=None,
                        additional_args=None,
                    )
                ],
            )
        ]
    ).dict()


@pytest.fixture()
def mock_hashlib(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.return_value = "mock-hash-code"
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_hashlib_no_match(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.side_effect = ["first-hash-code", "second-hash-code"]
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "a: 1"
    return mock_data_loader


@pytest.fixture()
def mock_subprocess(mocker: MockerFixture) -> MagicMock:
    mock_subprocess = MagicMock()
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    mocker.patch("secureli.abstractions.pre_commit.subprocess", mock_subprocess)
    return mock_subprocess


@pytest.fixture()
def pre_commit(
    mock_hashlib: MagicMock,
    mock_open: MagicMock,
    mock_subprocess: MagicMock,
) -> PreCommitAbstraction:
    return PreCommitAbstraction(
        command_timeout_seconds=300,
    )


def test_that_pre_commit_templates_are_loaded_for_supported_languages(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    pre_commit.install("Python")

    mock_subprocess.run.assert_called_with(["pre-commit", "install"])


def test_that_pre_commit_treats_failing_process_as_install_failed_error(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    with pytest.raises(InstallFailedError):
        pre_commit.install("Python")


def test_that_pre_commit_executes_hooks_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.execute_hooks()

    assert execute_result.successful
    assert "--all-files" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_successfully_including_all_files(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.execute_hooks(all_files=True)

    assert execute_result.successful
    assert "--all-files" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_and_reports_failures(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.execute_hooks()

    assert not execute_result.successful


def test_that_pre_commit_executes_a_single_hook_if_specified(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    pre_commit.execute_hooks(hook_id="detect-secrets")

    assert mock_subprocess.run.call_args_list[0].args[0][-1] == "detect-secrets"


##### autoupdate_hooks #####
def test_that_pre_commit_autoupdate_hooks_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks()

    assert execute_result.successful


def test_that_pre_commit_autoupdate_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.autoupdate_hooks()

    assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_bleeding_edge(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(bleeding_edge=True)

    assert execute_result.successful
    assert "--bleeding-edge" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_freeze(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(freeze=True)

    assert execute_result.successful
    assert "--freeze" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_multiple_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url", "some-other-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]
    assert "--repo some-other-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_fails_with_repos_containing_non_strings(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = [{"something": "something-else"}]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_ignores_repos_when_repos_is_a_dict(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = {}
    test_repos_string = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo {}" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_converts_repos_when_repos_is_a_string(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo string" in mock_subprocess.run.call_args_list[0].args[0]


##### update #####
def test_that_pre_commit_update_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.update()

    assert execute_result.successful


def test_that_pre_commit_update_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.update()

    assert not execute_result.successful


##### remove_unused_hooks #####
def test_that_pre_commit_remove_unused_hookss_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.remove_unused_hooks()

    assert execute_result.successful


def test_that_pre_commit_remove_unused_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.remove_unused_hooks()

    assert not execute_result.successful
