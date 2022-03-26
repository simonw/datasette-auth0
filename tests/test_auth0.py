from datasette.app import Datasette
import base64
import pytest
import urllib

CONFIG_KEYS = ("domain", "client_id", "client_secret")


@pytest.fixture
def non_mocked_hosts():
    # https://docs.datasette.io/en/stable/testing_plugins.html#testing-outbound-http-calls-with-pytest-httpx
    return ["localhost"]


@pytest.fixture
def datasette():
    return Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-auth0": {
                    "domain": "test.us.auth0.com",
                    "client_id": "CLIENT_ID",
                    "client_secret": "CLIENT_SECRET",
                }
            }
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("config_key", CONFIG_KEYS)
async def test_config_check(config_key):
    datasette = Datasette(
        [],
        memory=True,
        metadata={
            "plugins": {
                "datasette-auth0": {
                    key: "1" for key in CONFIG_KEYS if key != config_key
                }
            }
        },
    )
    response = await datasette.client.get("/-/auth0-login")
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert_message(
        datasette,
        response,
        "The following auth0 plugin settings are missing: {}".format(config_key),
    )


@pytest.mark.asyncio
async def test_auth0_login(datasette):
    response = await datasette.client.get("/-/auth0-login")
    assert response.status_code == 302
    location = response.headers["location"]
    bits = urllib.parse.urlparse(location)
    assert bits.netloc == "test.us.auth0.com"
    assert bits.path == "/authorize"
    qs = dict(urllib.parse.parse_qsl(bits.query))
    assert (
        qs.items()
        >= {
            "response_type": "code",
            "client_id": "CLIENT_ID",
            "redirect_uri": "http://localhost/-/auth0-callback",
            "scope": "openid profile email",
        }.items()
    )
    # state should be a random string
    assert len(qs["state"]) == 32


@pytest.mark.asyncio
async def test_callback(datasette, httpx_mock):
    httpx_mock.add_response(
        url="https://test.us.auth0.com/oauth/token",
        json={"access_token": "ACCESS_TOKEN"},
    )
    httpx_mock.add_response(
        url="https://test.us.auth0.com/userinfo", json={"id": "user"}
    )
    response = await datasette.client.get(
        "/-/auth0-callback?state=state&code=x", cookies={"auth0-state": "state"}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert datasette.unsign(response.cookies["ds_actor"], "actor")["a"] == {
        "id": "user"
    }
    post_request, get_request = httpx_mock.get_requests()
    # post should have had client ID / secret in Authorization
    assert post_request.headers["authorization"] == "Basic {}".format(
        base64.b64encode(b"CLIENT_ID:CLIENT_SECRET").decode("utf-8")
    )
    # get should have used the access token
    assert get_request.headers["authorization"] == "Bearer ACCESS_TOKEN"


@pytest.mark.asyncio
async def test_callback_state_must_match(datasette):
    state = "state1234"
    response = await datasette.client.get(
        "/-/auth0-callback?state=not-the-same&code=x", cookies={"auth0-state": state}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert_message(
        datasette,
        response,
        "state check failed, your authentication request is no longer valid",
    )


def assert_message(datasette, response, message):
    assert datasette.unsign(response.cookies["ds_messages"], "messages") == [
        [message, 3]
    ]
