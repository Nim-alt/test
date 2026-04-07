from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Defect, Product
from .serializers import DefectSerializer, ProductSerializer


# ====================== Defect API ======================
class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='Product Owner').exists():
            # Product Owner 只看到自己 Product 的 defect
            return Defect.objects.filter(product__owner=user)
        
        elif user.groups.filter(name='Developer').exists():
            # Developer 可以看到全部 defect
            return Defect.objects.all()
        
        else:
            # Tester 只看到自己提交的 defect
            return Defect.objects.filter(
                Q(reporter_email=user.email) | Q(tester_id=user.username)
            )


# ====================== Product API ======================
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Product Owner').exists():
            return Product.objects.filter(owner=user)
        return Product.objects.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)