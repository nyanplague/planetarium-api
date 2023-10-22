from django.test import TestCase

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from planetarium.models import AstronomyShow, PlanetariumDome, ShowSession, ShowTheme
from planetarium.serializers import AstronomyShowListSerializer, AstronomyShowDetailSerializer

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")
SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def detail_url(astronomy_show_id: int):
    return reverse("planetarium:astronomyshow-detail", args=[astronomy_show_id])


def sample_astronomy_show(**params):
    defaults = {
        "title": "Sample title",
        "description": "Sample description",
    }
    defaults.update(params)
    return AstronomyShow.objects.create(**defaults)


def sample_show_session(**params):
    planetarium_dome = PlanetariumDome.objects.create(
        name="TestDome", rows=20, seats_in_row=20
    )
    defaults = {
        "show_time": "2023-10-22 14:00:00",
        "astronomy_show": None,
        "planetarium_dome": planetarium_dome
    }

    defaults.update(params)

    return ShowSession.objects.create(**defaults)


class Unauthenticatedastronomy_showApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class Authenticatedastronomy_showApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testuser@test.com",
            "testpassword",
        )
        self.client.force_authenticate(self.user)

    def test_list_astronomy_shows(self):
        sample_astronomy_show()
        sample_astronomy_show()

        res = self.client.get(ASTRONOMY_SHOW_URL)

        astronomy_shows = AstronomyShow.objects.order_by("id")
        serializer = AstronomyShowListSerializer(astronomy_shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_astronomy_show_by_show_theme(self):
        show_theme1 = ShowTheme.objects.create(name="Test theme 1")
        show_theme2 = ShowTheme.objects.create(name="Test theme 1")

        astronomy_show1 = sample_astronomy_show(title="Test show 1")
        astronomy_show2 = sample_astronomy_show(title="Test show 2")

        astronomy_show1.show_themes.add(show_theme1)
        astronomy_show2.show_themes.add(show_theme2)

        astronomy_show3 = sample_astronomy_show(title="Show without title")

        res = self.client.get(
            ASTRONOMY_SHOW_URL, {"themes": f"{show_theme1.id},{show_theme2.id}"}
        )

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_astronomy_shows_by_title(self):
        astronomy_show1 = sample_astronomy_show(title="Show")
        astronomy_show2 = sample_astronomy_show(title="Another Show")
        astronomy_show3 = sample_astronomy_show(title="No match")

        res = self.client.get(ASTRONOMY_SHOW_URL, {"title": "Show"})

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_retrieve_astronomy_show_detail(self):
        astronomy_show = sample_astronomy_show()
        astronomy_show.show_themes.add(ShowTheme.objects.create(name="Test show theme"))

        url = detail_url(astronomy_show.id)
        res = self.client.get(url)

        serializer = AstronomyShowDetailSerializer(astronomy_show)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_astronomy_show_forbidden(self):
        payload = {
            "title": "New Show",
            "description": "Description",
        }
        res = self.client.post(ASTRONOMY_SHOW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlanetariumApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@admin.com", "testpassword", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        payload = {
            "title": "astronomy_show",
            "description": "Description",
        }
        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        print(res.status_code)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(astronomy_show, key))

    def test_create_astronomy_show_with_show_themes(self):
        showtheme1 = ShowTheme.objects.create(name="Cosmo")
        showtheme2 = ShowTheme.objects.create(name="Odyssey")

        payload = {
            "title": "New Astronomy Show",
            "show_themes": [showtheme1.id, showtheme2.id],
            "description": "New show",
            "duration": 148,
        }
        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])
        show_themes = astronomy_show.show_themes.all()
        self.assertEqual(show_themes.count(), 2)
        self.assertIn(showtheme1, show_themes)
        self.assertIn(showtheme2, show_themes)
