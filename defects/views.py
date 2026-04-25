from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Defect, Product, Comment, DefectHistory
from .permissions import IsProductOwnerOrDeveloperForDefect
from .serializers import DefectSerializer, ProductSerializer,CommentSerializer
from rest_framework.decorators import action
from rest_framework.decorators import action
from .state_machine import is_transition_allowed, ROLE_OWNER, ROLE_DEVELOPER, get_allowed_transitions  
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django_filters import rest_framework as filters


# ====================== Defect API ======================
class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends=(filters.DjangoFilterBackend,)
    filterset_fields=['status','priority','tester_id','severity','assigned_to','title']
    search_fields=['title','description']
    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='Product Owner').exists():
            return Defect.objects.filter(product__owner=user).order_by('id')
        
        elif user.groups.filter(name='Developer').exists():
            return Defect.objects.filter(product__developers=user).order_by('id')
        
        else:
            return Defect.objects.filter(
                Q(tester_email=user.email) | Q(tester_id=str(user.id))
            ).order_by('id')


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        new_comment_text = request.data.get('new_comment')
        new_status = request.data.get('status')
        old_status = instance.status

        if new_status == 'duplicate':
            if request.user != instance.product.owner:
                return Response(
                    {'error': 'Only product owner can mark a defect as duplicate.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if old_status != 'new':
                return Response(
                    {'error': 'Only defects with status "new" can be marked as duplicate.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            target_id = request.data.get('target_defect_id')
            if not target_id:
                return Response(
                    {'error': 'target_defect_id is required when status is "duplicate".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                target_defect = Defect.objects.get(id=target_id)
            except Defect.DoesNotExist:
                return Response(
                    {'error': f'Defect with id {target_id} does not exist.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if target_defect.product != instance.product:
                return Response(
                    {'error': 'Target defect must belong to the same product.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if target_defect.pk == instance.pk:
                return Response(
                    {'error': 'A defect cannot be marked as a duplicate of itself.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            current = target_defect
            while current is not None:
                if current.pk == instance.pk:
                    return Response(
                        {'error': 'Cannot mark a defect as a duplicate of one of its descendants.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                current = current.duplicate_of

            instance.duplicate_of = target_defect
            instance.status = 'duplicate'
            instance.save(update_fields=['duplicate_of', 'status'])

            DefectHistory.objects.create(
                defect=instance,
                old_status=old_status,
                new_status='duplicate',
                changed_by=request.user,
                assigned_to=instance.assigned_to 
            )



            if new_comment_text:
                Comment.objects.create(
                    defect=instance,
                    author=request.user,
                    text=new_comment_text
                )

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if new_status is not None and new_status != old_status:
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if not role:
                return Response(
                    {'error': 'You are not authorized to change the status of this defect.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not is_transition_allowed(old_status, new_status, role):
                return Response(
                    {'error': f'Transition from {old_status} to {new_status} is not allowed for {role}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if new_comment_text:
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if not role:
                return Response(
                    {'error': 'Only product owner or developer can add comments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        kwargs['partial'] = partial
        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()



        if new_status is not None and instance.status != old_status:
            DefectHistory.objects.create(
                defect=instance,
                old_status=old_status,
                new_status=instance.status,
                changed_by=request.user,
                assigned_to=instance.assigned_to  
            )


        if new_status == 'fixed':
            instance.date_fixed = timezone.now()
            instance.save(update_fields=['date_fixed'])
            response.data = self.get_serializer(instance).data
        elif new_status == 'reopened':
            instance.date_fixed = None
            instance.assigned_to = None
            instance.save(update_fields=['date_fixed', 'assigned_to'])
            response.data = self.get_serializer(instance).data



        if new_status == 'assigned' and old_status != 'assigned':
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if role == 'developer':  
                instance.assigned_to = user
                instance.save(update_fields=['assigned_to'])
                response.data = self.get_serializer(instance).data

        


        if new_comment_text:
            Comment.objects.create(
                defect=instance,
                author=request.user,
                text=new_comment_text
            )
            serializer = self.get_serializer(instance)
            response.data = serializer.data

        return response
    
        


    @action(detail=True, methods=['get'], url_path='candidate-targets')
    def candidate_targets(self, request, pk=None):
        defect = self.get_object()
        candidates = Defect.objects.filter(product=defect.product).exclude(status='new').values('id', 'title')
        return Response(list(candidates))


    @action(detail=True, methods=['get'], url_path='allowed-statuses')
    def allowed_statuses(self, request, pk=None):
        defect = self.get_object()
        user = request.user
        if user == defect.product.owner:
            role = ROLE_OWNER
        elif user in defect.product.developers.all():
            role = ROLE_DEVELOPER
        else:
            role = None
        if not role:
            return Response({'allowed_statuses': []})  
        allowed = get_allowed_transitions(defect.status, role)
        status_choices = dict(Defect.STATUS_CHOICES)
        allowed_with_labels = [{'value': s, 'label': status_choices.get(s, s)} for s in allowed]
        return Response({'allowed_statuses': allowed_with_labels})
    
    
    @action(detail=False, methods=['get'], url_path='metrics/(?P<user_id>[^/.]+)')
    def developer_metrics(self, request, user_id=None):
        from django.contrib.auth.models import User
        try:
            developer = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Developer not found'}, status=404)

        if not developer.groups.filter(name='Developer').exists():
            return Response({'error': 'User is not a developer'}, status=400)
        fixed = DefectHistory.objects.filter(assigned_to=developer, new_status='fixed').count()
        reopened = DefectHistory.objects.filter(assigned_to=developer, new_status='reopened').count()

        if fixed < 20:
            rating = "Insufficient data"
        else:
            ratio = reopened / fixed
            if ratio < 1/32:
                rating = "Good"
            elif ratio < 1/8:
                rating = "Fair"
            else:
                rating = "Poor"

        return Response({'developer_id': developer.id, 'rating': rating})
    


        
    def perform_create(self, serializer):
        serializer.save(
            tester_id=str(self.request.user.id),
            tester_email=self.request.user.email,
            status='new',
        )

    @staticmethod
    def get_user_role_for_defect(user, defect):
        if user == defect.product.owner:
            return 'owner'
        elif user in defect.product.developers.all():
            return 'developer'
        return None
    

    def create(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Tester').exists():
            return Response(
                {'error': 'Only testers can submit defect reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    

    


# ====================== Product API ======================
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Product Owner').exists():
            return Product.objects.filter(owner=user).order_by('id')
        return Product.objects.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


    def create(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Product Owner').exists():
            return Response(
                {'error': 'Only product owners can register products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)