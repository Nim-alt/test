from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
import pytest

@pytest.mark.django_db
class TestAPIEndpoints:
    client = APIClient()

    def setUp(self):
        # Setup code here. For example, creating necessary objects
        self.credentials = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        # Create a user and log in
        self.client.post(reverse('register'), self.credentials, format='json')
        self.client.login(username='testuser', password='testpassword')

    def test_create_defect(self):
        response = self.client.post(reverse('defect-list'), {'title': 'Test Defect'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_retrieve_defect(self):
        defect = self.client.post(reverse('defect-list'), {'title': 'Test Defect'}, format='json').data
        response = self.client.get(reverse('defect-detail', args=[defect['id']]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Defect'

    def test_update_defect(self):
        defect = self.client.post(reverse('defect-list'), {'title': 'Test Defect'}, format='json').data
        response = self.client.patch(reverse('defect-detail', args=[defect['id']]), {'title': 'Updated Defect'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Defect'
    
def test_delete_defect(self):
        defect = self.client.post(reverse('defect-list'), {'title': 'Test Defect'}, format='json').data
        response = self.client.delete(reverse('defect-detail', args=[defect['id']]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_product_list(self):
        response = self.client.get(reverse('product-list'))
        assert response.status_code == status.HTTP_200_OK

    # Add additional tests for custom actions and authentication requirements
