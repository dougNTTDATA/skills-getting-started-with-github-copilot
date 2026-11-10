from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = deepcopy(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "new-student@example.com"
    activity = activities[activity_name]

    # Act
    response = client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activity["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = activities["Chess Club"]
    email = "duplicate-student@example.com"
    activity["participants"].append(email)

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activity["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity(client):
    # Arrange
    activity = activities["Basketball Team"]
    activity["participants"] = [
        f"student-{number}@example.com"
        for number in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": "new-student@example.com"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "leaving-student@example.com"
    activity = activities[activity_name]
    activity["participants"].append(email)

    # Act
    response = client.delete(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activity["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity = activities["Basketball Team"]
    email = "not-registered@example.com"

    # Act
    response = client.delete(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in activity["participants"]