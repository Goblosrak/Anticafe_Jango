from django.test import TestCase
from django.urls import reverse
from .models import Zone

class ZoneModelTest(TestCase):
    def setUp(self):
        Zone.objects.create(
            title="Тестовая зона",
            description="Описание тестовой зоны",
            price_per_hour=500,
            capacity=4
        )

    def test_zone_creation(self):
        zone = Zone.objects.get(title="Тестовая зона")
        self.assertEqual(zone.price_per_hour, 500)
        self.assertEqual(zone.capacity, 4)

class ViewTests(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Антикафе "Чилл"')

    def test_zones_view(self):
        response = self.client.get(reverse('zones'))
        self.assertEqual(response.status_code, 200)