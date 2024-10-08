import shlex
from typing import Tuple
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
import config
from ..logging import LOGGER

def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(install_requirements())

def update_git_repository():
    REPO_LINK = config.UPSTREAM_REPO
    UPSTREAM_REPO = REPO_LINK
    GITHUB_TOKEN = config.GITHUB_TOKEN  # Çevresel değişkeni burada alıyoruz

    if GITHUB_TOKEN:
        GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
        TEMP_REPO = REPO_LINK.split("https://")[1]
        UPSTREAM_REPO = f"https://{GIT_USERNAME}:{GITHUB_TOKEN}@{TEMP_REPO}"

    try:
        repo = Repo()
        LOGGER("Git").info("Git repository already initialized.")
    except GitCommandError:
        LOGGER("Git").info("Invalid Git Command")
    except InvalidGitRepositoryError:
        repo = Repo.init()
        origin = repo.create_remote("origin", UPSTREAM_REPO)
        origin.fetch()
        repo.create_head(config.UPSTREAM_BRANCH, origin.refs[config.UPSTREAM_BRANCH])
        repo.heads[config.UPSTREAM_BRANCH].set_tracking_branch(origin.refs[config.UPSTREAM_BRANCH])
        repo.heads[config.UPSTREAM_BRANCH].checkout(True)
        try:
            repo.create_remote("origin", config.UPSTREAM_REPO)
        except BaseException:
            pass

        nrs = repo.remote("origin")
        nrs.fetch(config.UPSTREAM_BRANCH)
        try:
            nrs.pull(config.UPSTREAM_BRANCH)
        except GitCommandError as e:
            LOGGER("Git").error(f"Error during pull: {e}")
            repo.git.reset("--hard", "FETCH_HEAD")
        install_req("pip3 install --no-cache-dir -r requirements.txt")
        LOGGER("Git").info("Fetching updates from upstream repository...")
