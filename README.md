## Quickstart

- Make sure you have [Docker](https://docs.docker.com/get-started/get-docker/) installed.
- From within the root directory, run

```shell
docker compose up
```

After the application builds, you will be able to view the application at `http://127.0.0.1:8000`. Available endpoints include

- `/github/lodash_pr_count` - the primary goal of the assignment
- `/github/quick_lodash_pr_count` - a super-fast implementation that only returns a count

## Development

Make sure you have [Python 3.12](https://www.python.org/downloads/release/python-3125/) or greater installed.

Clone the repo and navigate to the root directory.

Create and activate a virtual environment with

```shell
pip install setuptools
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies with

```shell
pip install .
```

Start the dev server with

```shell
fastapi dev app/main.py
```

## [Optional] Authorization

Authorization with GitHub will increase the rate limits for the API. In production, these would not be hit, but if you continuously restart the server and rerun from the same IP address, you could hit them while developing.

To avoid this, [set up a GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). You can use a classic token (ignore checkboxes) or a fine-grained token with "List pull requests" access.

Create a `.env` file in the root directory with the line

`GITHUB_ACCESS_TOKEN=<your token>`
