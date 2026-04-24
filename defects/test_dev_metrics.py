from django.test import TestCase
from django.contrib.auth.models import User, Group
from unittest.mock import patch, Mock

from .views import DefectViewSet


class dev_metrics_test(TestCase):
    
    def setUp(self):
      
        self.developer_group, _ = Group.objects.get_or_create(name='Developer')
        
        self.developer = User.objects.create_user(
            username='test_developer',
            password='testpass123',
            email='dev@test.com'
        )
      
        self.developer.groups.add(self.developer_group)
        
        self.view = DefectViewSet()
    
    def get_rating(self, fixed_count, reopened_count):
      
        with patch('your_app.views.DefectHistory.objects.filter') as mock_filter:
            mock_filter.side_effect = [
                Mock(count = Mock(return_value = fixed_count)),
                Mock(count = Mock(return_value = reopened_count))
            ]
            response = self.view.developer_metrics(None, user_id=self.developer.id)
            return response.data['rating']

  
    def test_insufficient_data(self):
      
        test_cases = [
            (0, 0),      # Lower boundary: no defects
            (10, 5),     # Middle value
            (19, 100),   # Upper boundary: exactly 19 fixed
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Insufficient data")

  
    def test_good(self):
      
        test_cases = [
            (20, 0),      # Lower boundary: minimum fixed, zero reopened
            (32, 0),      # Fixed exactly 32 with zero reopened
            (33, 1),      # Ratio slightly below 1/32 (0.0303)
            (100, 2),     # Typical case (0.02)
            (1000, 31),   # Upper boundary of ratio (0.031)
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Good")
    

    def test_fair(self):

        test_cases = [
            (32, 1),      # Lower boundary: exactly 1/32
            (64, 3),      # Middle value (0.046875)
            (20, 2),      # Ratio = 0.1
            (64, 7),      # Upper boundary: just below 1/8 (0.109375)
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Fair")
    
    
    def test_poor_rating_class(self):

        test_cases = [
            (32, 4),      # Lower boundary: exactly 1/8
            (40, 6),      # Middle value (0.15)
            (20, 5),      # Ratio = 0.25
            (20, 20),     # Ratio = 1.0
            (30, 40),     # Ratio > 1.0
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Poor")
    
