# QA Showcase: UI and API tests in Python

[![tests](https://github.com/PavelDobrii/qa-showcase/actions/workflows/tests.yml/badge.svg)](https://github.com/PavelDobrii/qa-showcase/actions/workflows/tests.yml)

This is an example of my test automation work. The tests check **Toolshop**
([practicesoftwaretesting.com](https://practicesoftwaretesting.com)), a demo web shop
with a REST API. The site is made for test practice and is open to everyone.
On your computer the tests use the public site. In CI they use a copy of the app
that the workflow starts in Docker.

## What the project shows

- UI tests with Playwright and the Page Object pattern.
- API tests with httpx and JSON schema checks.
- UI checked against the API: the browser must show the same data that the backend returns.
- Data-driven tests with `pytest.mark.parametrize`.
- Fixtures with clean-up: a test gets its own new cart, and the fixture deletes it after the test.
- Stable waits without `sleep()`, and retry only for temporary network errors.
  See [How the tests stay stable](#how-the-tests-stay-stable).
- Unit tests for the framework code (the retry logic).
- GitHub Actions: lint and tests on every push and pull request, HTML report as an artifact.
- The app under test runs in Docker inside the CI job, so CI does not depend on a shared public site.

## Stack

Python 3.12 · pytest · Playwright for Python · httpx · jsonschema · pytest-html · ruff · Docker Compose · GitHub Actions

## Tests

| Group | Marker | Tests | What they check |
|---|---|---|---|
| Unit | `unit` | 4 | Retry logic. A fake server is used, no network. |
| API | `api` | 9 | Product list and pages, JSON schema, search, sorting, 404, cart: add, change, remove, validation error 422. |
| UI | `ui` | 7 | Search, sorting, category filter, product page, add to cart, product that is out of stock. |

20 tests in total. The `smoke` marker selects 4 of them: the most important checks.
A full run takes about 15 seconds on a laptop.

## How to run locally

You need Python 3.12 or newer.

```bash
git clone https://github.com/PavelDobrii/qa-showcase.git
cd qa-showcase
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Run the tests:

```bash
pytest                             # all tests
pytest -m api                      # only API tests
pytest -m "ui and smoke"           # only UI smoke tests
pytest -m ui --headed              # watch the browser
pytest --html=reports/report.html --self-contained-html   # with an HTML report
```

Run the linter:

```bash
ruff check .
ruff format --check .
```

### Run against a local copy of the app

You need Docker. This is the same setup as in CI:

```bash
bash ci/start-toolshop.sh          # UI on localhost:4200, API on localhost:8091
UI_URL=http://localhost:4200 API_URL=http://localhost:8091 AVOID_DEMO_RESET=0 pytest
docker compose -f ci/toolshop-compose.yml down --volumes   # stop and remove the copy
```

### Settings

The defaults work with the public demo. You can change them with environment variables,
for example to test a local copy of the app.

| Variable | Default | Meaning |
|---|---|---|
| `UI_URL` | `https://practicesoftwaretesting.com` | Web shop address |
| `API_URL` | `https://api.practicesoftwaretesting.com` | REST API address |
| `HTTP_TIMEOUT` | `15` | API request timeout, seconds |
| `UI_TIMEOUT_MS` | `10000` | Timeout for UI actions and checks, milliseconds |
| `AVOID_DEMO_RESET` | `1` | Wait for the hourly reset of the demo data. Use `0` for your own copy. |

## How CI works

The workflow is [`.github/workflows/tests.yml`](.github/workflows/tests.yml).
It runs on every push to `main`, on every pull request, and by hand (the "Run workflow" button).

1. **lint** job: `ruff check` and `ruff format --check`. If it fails, the tests do not start.
2. **test** job:
   - starts a copy of the Toolshop app with Docker Compose
     ([`ci/toolshop-compose.yml`](ci/toolshop-compose.yml)) and fills its database with demo data
     ([`ci/start-toolshop.sh`](ci/start-toolshop.sh));
   - installs the dependencies and Chromium;
   - runs all tests with Python 3.12 against this copy.
3. The test job uploads the `test-report` artifact: an HTML report, a JUnit XML file,
   and for each failed UI test a screenshot and a Playwright trace.
   If a test fails, the artifact also has the app logs.
   To open a trace: `playwright show-trace trace.zip`.

Why a copy of the app and not the public site? The public site is behind Cloudflare bot
protection. It shows a "security verification" page to a browser on a CI server, so UI tests
cannot open the shop there. The API is not blocked. A copy in Docker also gives CI clean data:
no products from other people and no hourly reset.

## How the tests stay stable

The demo site is public. Many people use it at the same time, it is sometimes slow,
and its data changes. These rules keep the tests stable:

1. **Wait for an event, not for time.** There is no `sleep()` in the tests.
   When a test sorts the product list, the page object waits for the API response
   and then for the marker that the app sets when the new list is on the screen
   (`CatalogPage._reload_products`). Without the second step a test can read the old list.
   All UI checks use Playwright `expect()`, which tries again until the check passes or the time is over.
2. **Retry only temporary errors.** The API client tries again after a connection error,
   a timeout, 429, 502, 503 or 504, and waits longer each time.
   It never retries other answers: a 404 or 422 is a real result, and the test must see it.
   It does not repeat a POST after a 5xx error, because the server may have created the object already.
   See [`framework/api/retry.py`](framework/api/retry.py) and its unit tests.
3. **Do not depend on data you do not own.** Other people add products to the demo.
   So the tests do not check exact totals, and they take product ids from the API
   instead of writing them in the code.
4. **Know your test environment.** The public demo database is rebuilt every hour at :00 UTC,
   and all ids change. The tests do not start in the last 2 minutes before the reset,
   and after the reset they wait until the data is back
   ([`framework/demo_reset.py`](framework/demo_reset.py)).
   CI uses its own copy of the app, so this check is off there (`AVOID_DEMO_RESET=0`).
5. **Each test has its own data.** A cart test creates a new cart and deletes it at the end.
   Each UI test gets a new browser context, so it does not see cookies or storage of other tests.

The project does not rerun failed tests automatically. A rerun can hide a real problem.
A flaky test is a bug that must be found and fixed.

## Project structure

```text
.
├── .github/workflows/tests.yml   CI: lint, tests, report
├── ci/
│   ├── toolshop-compose.yml      copy of the app under test for CI (Docker Compose)
│   ├── nginx.conf                web server settings for the app API
│   └── start-toolshop.sh         start the copy, fill the database, wait until it is ready
├── framework/                    code that the tests use
│   ├── api/
│   │   ├── client.py             API client (httpx)
│   │   ├── retry.py              retry for temporary errors
│   │   └── schemas.py            JSON schemas of the responses
│   ├── pages/                    page objects
│   │   ├── base_page.py          parts of every page: header, cart badge
│   │   ├── catalog_page.py       product list, search, sorting, filters
│   │   ├── product_page.py
│   │   └── cart_page.py
│   ├── config.py                 settings from environment variables
│   ├── demo_reset.py             protection against the hourly reset
│   └── waits.py                  wait_until(): polling instead of sleep
├── tests/
│   ├── conftest.py               shared fixtures: settings, API client, cart, test data
│   ├── unit/                     tests of the retry logic
│   ├── api/                      API tests
│   └── ui/                       browser tests and their fixtures
├── pyproject.toml                pytest and ruff settings, markers
└── requirements.txt              pinned versions
```

## About the app under test

Toolshop is an open-source demo app for test practice:
[testsmith-io/practice-software-testing](https://github.com/testsmith-io/practice-software-testing).
This project is not connected with its authors.

## Author

Pavel Daushko, QA Automation Engineer · [LinkedIn](https://www.linkedin.com/in/pavel-daushko-200408188/)
