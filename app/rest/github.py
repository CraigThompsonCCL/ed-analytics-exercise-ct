from fastapi import APIRouter
from fastapi_cache.decorator import cache
from ..models.github import GitHubPR
from . import async_client
import httpx

router = APIRouter(prefix="/github", tags=["github"])

lodash_prs_list: list[GitHubPR] = []


@router.get("/quick_lodash_pr_count")
@cache(expire=60)
async def get_lodash_prs_quick() -> int:
    """
    A fast implementation to get the count of all lodash PRs.
    Makes an unassured (but very likey) assumption about how GitHub will page this API.
    """
    response = await async_client.get(
        "https://api.github.com/repos/lodash/lodash/pulls?per_page=1&state=all"
    )
    link_text = get_header_link(response, "last")
    return int(link_text.split("=")[-1])


@router.get("/lodash_pr_count")
@cache(expire=60)
async def get_lodash_prs() -> int:
    """Get the count of all lodash PRs."""
    global lodash_prs_list
    prs_list_copy = lodash_prs_list[:]
    newest_pr = prs_list_copy[0] if len(prs_list_copy) else None

    # Quick version - under conservative assumptions, will be called >99% of the time
    if newest_pr:
        pr_found = False
        new_prs_list, pr_found, _ = await find_newer_prs_in_page(
            "https://api.github.com/repos/lodash/lodash/pulls?per_page=5&state=all",
            newest_pr,
        )
        if pr_found:
            # store data
            lodash_prs_list = new_prs_list + prs_list_copy
            return len(prs_list_copy) + len(new_prs_list)

    # Will be called the first time, then likely <1% of the time
    pr_found = False
    new_prs_list = []
    next_page_url = (
        "https://api.github.com/repos/lodash/lodash/pulls?per_page=100&state=all"
    )
    while next_page_url and not pr_found:
        new_prs_list_addition, pr_found, response = await find_newer_prs_in_page(
            next_page_url, newest_pr
        )
        new_prs_list += new_prs_list_addition
        if not pr_found:
            next_page_url = get_header_link(response, "next")
            print("next page url:", next_page_url)
    # store data
    lodash_prs_list = new_prs_list + prs_list_copy
    return len(prs_list_copy) + len(new_prs_list)


async def find_newer_prs_in_page(
    page_url: str, since_pr: GitHubPR | None
) -> tuple[list[GitHubPR], bool, httpx.Response]:
    """Given the URL of a page of PRs and a PR, returns a list of all PRs since that PR.
    Assumes the page includes only PRs after or around the PR in question.
    Also returns whether the PR was found and the HTTPX Response from the page"""
    since_pr_found = False
    new_prs_list = []
    response = await async_client.get(page_url)
    for raw_pr in response.json():
        pr = GitHubPR.model_validate(raw_pr)
        if pr == since_pr:
            since_pr_found = True
            break
        else:
            new_prs_list.append(pr)
    return new_prs_list, since_pr_found, response


def get_header_link(response: httpx.Response, link_type: str) -> str | None:
    """Gets a link of link_type from the link header"""
    link_header = response.headers.get("link", {})
    links = link_header.split(",")
    target_link = None
    for link in links:
        rel = link[-5:-1]
        if rel == link_type:
            target_link = link.split(">")[0].strip()[1:]
            break
    return target_link
