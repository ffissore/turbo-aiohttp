import base64
import json

from aiohttp import web, ClientSession
from aiohttp_jinja2 import render_template, render_string

from turbo import Turbo

turbo = Turbo()

FIREBASE_API_KEY = "<<COPY FROM FRONTEND CONFIG>>"


async def index(request: web.Request):
    return render_template("login.html", request, {})


async def login_pw(request: web.Request):
    # todo: input validation
    form = await request.post()
    email = form["email"]
    password = form["password"]

    async with ClientSession() as session:
        async with session.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json={"email": email, "password": password, "returnSecureToken": True},
        ) as resp:
            # todo: handle error
            data = await resp.json()
            firebase_token = data["idToken"]

        async with session.post(
            "https://api.nbx.com/auth/verify",
            json={"token": firebase_token},
        ) as resp:
            authservice_response_status = resp.status
            authservice_response_data = await resp.text()

            if resp.status == 403:
                body_json = await resp.json()
                if body_json["error"] == "missing_code_field":
                    return turbo.stream(
                        turbo.replace(
                            render_string(
                                "login_2fa.html", request, {"token": firebase_token}
                            ),
                            target="login",
                        )
                    )
                else:
                    # todo: handle the case when 2fa is not set up
                    return turbo.stream(
                        turbo.replace(
                            json.dumps(
                                {
                                    "status": authservice_response_status,
                                    "data": authservice_response_data,
                                }
                            ),
                            target="login",
                        )
                    )
            else:
                return turbo.stream(
                    turbo.replace(
                        json.dumps(
                            {
                                "status": authservice_response_status,
                                "data": authservice_response_data,
                            }
                        ),
                        target="login",
                    )
                )


async def login_2fa(request: web.Request):
    # todo: input validation
    form = await request.post()
    token = form["token"]
    code = form["code"]

    async with ClientSession() as session:
        async with session.post(
            "https://api.nbx.com/auth/verify",
            json={"token": token, "code": code},
        ) as resp:
            # todo: error handling
            authservice_response_status = resp.status
            authservice_response_data = await resp.json()

            session_token = authservice_response_data["token"]
            account_id = authservice_response_data["account_id"]

        async with session.post(
            f"https://api.nbx.com/auth/accounts/{account_id}/tokens",
            headers={"Authorization": f"Bearer {session_token}"},
        ) as resp:
            # todo: error handling
            authservice_response_status = resp.status
            authservice_response_data = await resp.json()
            fingerprint = resp.cookies[account_id].value
            return turbo.stream(
                [
                    turbo.replace(
                        render_string(
                            "script.html",
                            request,
                            {"token": authservice_response_data["token"], "fingerprint": fingerprint},
                        ),
                        target="script-holder",
                    ),
                    turbo.replace(
                        render_string(
                            "welcome.html", request, {"account_id": account_id}
                        ),
                        target="login",
                    ),
                ]
            )


async def balances(request: web.Request):
    # todo: input validation
    account_token = request.headers["Authorization"].split(" ")[1]
    sub_fingerprint = request.headers["X-Nbx-Sub-Fingerprint"]

    # decode account_token as jwt
    # todo: validate token and use lib to decode
    middle_part = account_token.split(".")[1]
    missing_padding = len(middle_part) % 4
    if missing_padding:
        middle_part += "=" * (4 - missing_padding)
    decoded = base64.b64decode(middle_part)
    decoded_json = json.loads(decoded)
    account_id = decoded_json["sub"]

    async with ClientSession() as session:
        async with session.get(
            f"https://api.nbx.com/accounts/{account_id}/assets",
            headers={"Authorization": f"Bearer {account_token}"},
            cookies={account_id: sub_fingerprint},
        ) as resp:
            return render_template(
                "balances.html",
                request,
                {"assets": await resp.json()},
            )


ROUTES = [
    web.get("/gabor", index),
    web.post("/gabor/login", login_pw),
    web.post("/gabor/login_2fa", login_2fa),
    web.get("/gabor/balances", balances),
]
