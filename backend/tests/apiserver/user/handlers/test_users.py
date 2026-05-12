import pytest

from msm.apiserver.db import models
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import (
    BadRequestErrorResponseModel,
    ForbiddenErrorResponseModel,
    NotFoundErrorResponseModel,
    ValidationErrorResponseModel,
)
from msm.apiserver.user.handlers.users import User
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestUsersGetHandler:
    async def test_get(
        self,
        api_admin: models.User,
        api_user: models.User,
        admin_client: Client,
        factory: Factory,
    ) -> None:
        user_list = await admin_client.get("/users")
        assert user_list.status_code == 200
        users = [
            User.from_model(api_admin).model_dump(),
            User.from_model(api_user).model_dump(),
        ]
        user_details = user_list.json()
        assert user_details["total"] == len(users)
        assert user_details["items"] == users

    @pytest.mark.parametrize(
        "query_params, expected_result",
        [
            (
                {"sort_by": "username-asc"},
                ["admin", "alphacen", "hatp13", "proxima", "trappist"],
            ),
            (
                {"sort_by": "username,full_name,email,is_admin"},
                ["admin", "alphacen", "hatp13", "proxima", "trappist"],
            ),
            (
                {"sort_by": "username-desc"},
                ["trappist", "proxima", "hatp13", "alphacen", "admin"],
            ),
            (
                {"sort_by": "full_name,email-desc"},
                ["admin", "hatp13", "proxima", "alphacen", "trappist"],
            ),
            (
                {"sort_by": "is_admin,full_name-desc"},
                ["alphacen", "proxima", "hatp13", "trappist", "admin"],
            ),
            (
                {"page": 2, "size": 2, "sort_by": "username,email-asc"},
                ["hatp13", "proxima"],
            ),
            (
                {"search_text": "@example"},
                ["admin", "hatp13", "alphacen"],
            ),
            ({"search_text": "Bob+Smith", "page": 1}, []),
            (
                {"search_text": "aur", "sort_by": "username-desc"},
                ["proxima", "alphacen"],
            ),
            (
                {"sort_by": "full_name-asc", "search_text": " b"},
                ["hatp13", "proxima"],
            ),
        ],
    )
    async def test_with_params(
        self,
        admin_client: Client,
        factory: Factory,
        query_params: str,
        expected_result: list[str],
    ) -> None:
        await factory.make_User(
            username="proxima",
            email="proxima@maas-site-manager.example.com",
            full_name="Proxima Centauri b",
        )
        await factory.make_User(
            username="trappist",
            email="trappist@maas-site-manager.example.com",
            full_name="Trappist 1 e",
            is_admin=True,
        )
        await factory.make_User(
            username="hatp13",
            email="hatp13@example.com",
            full_name="HAT-P-13 b",
        )
        await factory.make_User(
            username="alphacen",
            email="alphacen@example.com",
            full_name="Rigel Kentaurus",
        )

        response = await admin_client.get("/users", params=query_params)
        usernames = [user["username"] for user in response.json()["items"]]
        assert usernames == expected_result

    @pytest.mark.parametrize(
        "sort_by,error_msg",
        [
            ("id-asc", "Invalid sort field"),
            ("username,username", "Duplicate sort parameters detected"),
            ("doesntexist", "Invalid sort field"),
        ],
    )
    async def test_with_invalid_params(
        self,
        admin_client: Client,
        sort_by: str,
        error_msg: str,
    ) -> None:
        response = await admin_client.get(
            "/users", params={"sort_by": sort_by}
        )
        assert response.status_code == 422
        err = ValidationErrorResponseModel(**response.json())
        assert err.error.code == ExceptionCode.INVALID_PARAMS
        assert err.error.details is not None
        assert err.error.details[0].messages == [error_msg]

    async def test_pagination(
        self, admin_client: Client, factory: Factory
    ) -> None:
        user = await factory.make_User()

        paginated = await admin_client.get("/users?page=2&size=1")
        assert paginated.status_code == 200
        assert paginated.json() == {
            "page": 2,
            "size": 1,
            "total": 2,
            "items": [
                User.from_model(user).model_dump(),
            ],
        }

    async def test_get_by_id(
        self, admin_client: Client, factory: Factory
    ) -> None:
        user = await factory.make_User()

        response = await admin_client.get(f"/users/{user.id + 100}")
        assert response.status_code == 404
        err = NotFoundErrorResponseModel(**response.json())
        assert err.error.code == ExceptionCode.MISSING_RESOURCE
        assert err.error.details is not None
        assert err.error.details[0].messages[0] == "User does not exist."
        assert err.error.message == "Resource not found."

        response = await admin_client.get(f"/users/{user.id}")
        assert response.status_code == 200
        assert response.json() == User.from_model(user).model_dump()


@pytest.mark.asyncio
class TestUsersPostHandler:
    async def test_post(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A MAAS User",
            "username": "newuser",
            "email": "newuser@example.com",
            "is_admin": False,
        }
        response = await admin_client.post(
            "/users",
            json=user_details
            | {"password": "password", "confirm_password": "password"},
        )
        assert response.status_code == 200
        result = response.json()
        result.pop("id")
        assert result == user_details

    async def test_missing_fields(self, admin_client: Client) -> None:
        response = await admin_client.post(
            "/users",
            json={},
        )
        assert response.status_code == 422
        err = ValidationErrorResponseModel(**response.json())
        assert err.error.code == ExceptionCode.INVALID_PARAMS
        assert err.error.details is not None

        missing_fields = set()

        for entry in err.error.details:
            missing_fields.add(entry.field)
            assert entry.reason == "Missing"

        assert missing_fields == {
            "full_name",
            "username",
            "email",
            "password",
            "confirm_password",
        }

    async def test_password_unconfirmed(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A MAAS User",
            "username": "newuser",
            "email": "user@example.com",
            "password": "password",
            "confirm_password": "",
        }
        response = await admin_client.post(
            "/users",
            json=user_details,
        )
        assert response.status_code == 422
        assert response.json()

    async def test_email_taken(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A New Admin",
            "username": "newAdmin",
            "email": "admin@example.com",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.post(
            "/users",
            json=user_details,
        )
        assert response.status_code == 400
        assert (
            response.json()["error"]["message"]
            == "Email or Username already in use."
        )
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == "email"

    async def test_username_taken(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A New Admin",
            "username": "admin",
            "email": "newadmin@example.com",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.post(
            "/users",
            json=user_details,
        )
        assert response.status_code == 400
        assert (
            response.json()["error"]["message"]
            == "Email or Username already in use."
        )
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == "username"

    async def test_email_and_username_taken(
        self, admin_client: Client
    ) -> None:
        user_details = {
            "full_name": "A New Admin",
            "username": "admin",
            "email": "admin@example.com",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.post(
            "/users",
            json=user_details,
        )
        assert response.status_code == 400
        assert (
            response.json()["error"]["message"]
            == "Email or Username already in use."
        )
        assert len(response.json()["error"]["details"]) == 2
        assert response.json()["error"]["details"][0]["field"] == "email"
        assert response.json()["error"]["details"][1]["field"] == "username"

    async def test_invalid_email(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A New User",
            "username": "user123",
            "email": "not-an.email",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.post(
            "/users",
            json=user_details,
        )
        assert response.status_code == 422
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == "email"


@pytest.mark.asyncio
class TestUsersMePasswordPostHandler:
    async def test_password_change(self, user_client: Client) -> None:
        new_password = "new_admin_password"
        response = await user_client.patch(
            "/users/me/password",
            json={
                "current_password": "user",
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )
        assert response.status_code == 200

    async def test_password_change_incorrect_pass(
        self,
        user_client: Client,
    ) -> None:
        new_password = "new_admin_password"
        response = await user_client.patch(
            "/users/me/password",
            json={
                "current_password": "wrong_password",
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )
        assert response.status_code == 400
        err = BadRequestErrorResponseModel(**response.json())
        assert err.error.message == "Invalid user credentials."
        assert err.error.details is not None
        assert (
            err.error.details[0].messages[0] == "Incorrect current password."
        )

    async def test_password_change_missing_parameters(
        self,
        user_client: Client,
    ) -> None:
        response = await user_client.patch(
            "/users/me/password",
            json={},
        )
        assert response.status_code == 422
        missing_fields = set()
        for entry in response.json()["error"]["details"]:
            missing_fields.add(entry["field"])
            assert entry["reason"] == "Missing"

        assert missing_fields == {
            "current_password",
            "new_password",
            "confirm_password",
        }


@pytest.mark.asyncio
class TestUsersPatchHandler:
    async def test_patch(
        self, api_user: models.User, admin_client: Client
    ) -> None:
        old_details = User.from_model(api_user).model_dump()
        new_details = {"email": "newemail@example.com"}
        response = await admin_client.patch(
            f"/users/{api_user.id}", json=new_details
        )

        user_details = old_details | new_details
        # assert response.status_code == 200
        assert response.json() == user_details

        response = await admin_client.patch("/users/42", json=new_details)
        assert response.status_code == 404

    async def test_demote_admin(
        self, admin_client: Client, factory: Factory
    ) -> None:
        user = await factory.make_User(is_admin=True)
        new_details = {"is_admin": False}
        response = await admin_client.patch(
            f"/users/{user.id}", json=new_details
        )
        assert response.status_code == 200
        assert (
            response.json() == User.from_model(user).model_dump() | new_details
        )

    async def test_demote_self_admin(
        self, api_admin: models.User, admin_client: Client
    ) -> None:
        response = await admin_client.patch(
            f"/users/{api_admin.id}", json={"is_admin": False}
        )
        assert response.status_code == 403
        err = ForbiddenErrorResponseModel(**response.json())
        assert err.error.message == "A request parameter is invalid."
        assert err.error.details is not None
        assert (
            err.error.details[0].messages[0]
            == "Admin users cannot demote themselves."
        )

    async def test_missing_fields(
        self, api_admin: models.User, admin_client: Client
    ) -> None:
        response = await admin_client.patch(f"/users/{api_admin.id}", json={})
        assert response.status_code == 422
        assert (
            response.json()["error"]["message"]
            == "One or more request parameters are invalid"
        )
        assert response.json()["error"]["details"][0]["messages"] == [
            "Value error, At least one field must be set."
        ]

    async def test_nonexistent_user(self, admin_client: Client) -> None:
        response = await admin_client.patch(
            "/users/10000000", json={"full_name": "ghost_in_the_test"}
        )
        assert response.status_code == 404
        err = NotFoundErrorResponseModel(**response.json())
        assert err.error.message == "Resource not found."
        assert err.error.details is not None
        assert err.error.details[0].messages[0] == "User does not exist."

    @pytest.mark.parametrize(
        "new_details,which_taken",
        [
            ({"email": "admin@example.com"}, "email"),
            ({"username": "admin"}, "username"),
        ],
    )
    async def test_duplicate_user(
        self,
        admin_client: Client,
        factory: Factory,
        new_details: dict[str, str],
        which_taken: str,
    ) -> None:
        user = await factory.make_User()

        response = await admin_client.patch(
            f"/users/{user.id}", json=new_details
        )
        assert response.status_code == 400
        assert (
            response.json()["error"]["message"]
            == "Email or Username already in use."
        )
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == which_taken

    async def test_password_validation(
        self, api_admin: models.User, admin_client: Client
    ) -> None:
        response = await admin_client.patch(
            f"/users/{api_admin.id}",
            json={"password": "goodpasswd", "confirm_password": "badpasswd"},
        )
        assert response.status_code == 422
        assert (
            response.json()["error"]["details"][0]["reason"]
            == "PasswordMismatch"
        )

    async def test_field_validation(
        self, api_admin: models.User, admin_client: Client
    ) -> None:
        response = await admin_client.patch(
            f"/users/{api_admin.id}",
            json={"password": "short", "confirm_password": "no"},
        )
        assert response.status_code == 422
        resp = response.json()["error"]["details"]
        assert len(resp) == 2
        assert resp[0]["reason"] == "StringTooShort"
        assert resp[1]["reason"] == "StringTooShort"

    async def test_query_validation(self, admin_client: Client) -> None:
        response = await admin_client.patch(
            f"/users/adsf",
            json={"password": "short", "confirm_password": "no"},
        )
        assert response.status_code == 422
        resp = response.json()["error"]["details"]
        assert len(resp) == 3
        assert resp[0]["reason"] == "IntParsing"
        assert resp[1]["reason"] == "StringTooShort"
        assert resp[2]["reason"] == "StringTooShort"

    async def test_invalid_email(
        self, admin_client: Client, factory: Factory
    ) -> None:
        user = await factory.make_User()
        user_details = {
            "full_name": "A New User",
            "username": "user123",
            "email": "not-an.email",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.patch(
            f"/users/{user.id}",
            json=user_details,
        )
        assert response.status_code == 422
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == "email"


@pytest.mark.asyncio
class TestUsersDeleteHandler:
    async def test_delete(
        self, api_admin: models.User, admin_client: Client, factory: Factory
    ) -> None:
        user = await factory.make_User()
        response = await admin_client.delete(f"/users/{user.id}")
        assert response.status_code == 204
        response = await admin_client.get(f"/users/{user.id}")
        assert response.status_code == 404

    async def test_delete_self_fails(
        self, api_admin: models.User, admin_client: Client, factory: Factory
    ) -> None:
        response = await admin_client.delete(f"/users/{api_admin.id}")
        assert response.status_code == 400

        err = BadRequestErrorResponseModel(**response.json())
        assert err.error.message == "A request parameter is invalid."
        assert err.error.details is not None
        assert (
            err.error.details[0].messages[0]
            == "Cannot delete the current user."
        )


@pytest.mark.asyncio
class TestUsersMePatchHandler:
    async def test_patch(
        self, api_user: models.User, user_client: Client
    ) -> None:
        old_details = User.from_model(api_user).model_dump()
        new_details = {"email": "new-email@example.com"}
        response = await user_client.patch("/users/me", json=new_details)

        assert response.status_code == 200
        assert response.json() == old_details | new_details

    async def test_missing_fields(self, user_client: Client) -> None:
        response = await user_client.patch("/users/me", json={})

        assert response.status_code == 422
        assert (
            response.json()["error"]["message"]
            == "One or more request parameters are invalid"
        )
        assert response.json()["error"]["details"][0]["messages"] == [
            "Value error, At least one field must be set."
        ]

    @pytest.mark.parametrize(
        "new_details,which_taken",
        [
            ({"email": "admin2@example.com"}, "email"),
            ({"username": "admin2"}, "username"),
        ],
    )
    async def test_duplicate_user(
        self,
        admin_client: Client,
        factory: Factory,
        new_details: dict[str, str],
        which_taken: str,
    ) -> None:
        await factory.make_User(username="admin2", email="admin2@example.com")
        response = await admin_client.patch("/users/me", json=new_details)
        assert response.status_code == 400
        assert (
            response.json()["error"]["message"]
            == "Email or Username already in use."
        )
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == which_taken

    async def test_invalid_email(self, admin_client: Client) -> None:
        user_details = {
            "full_name": "A New User",
            "username": "user123",
            "email": "not-an.email",
            "password": "password",
            "confirm_password": "password",
        }
        response = await admin_client.patch(
            "/users/me",
            json=user_details,
        )
        assert response.status_code == 422
        assert len(response.json()["error"]["details"]) == 1
        assert response.json()["error"]["details"][0]["field"] == "email"
