from rest_framework import serializers
from .models import Defect, Product

# ====================== 新增：Product Serializer ======================
class ProductSerializer(serializers.ModelSerializer):
    # 顯示 owner 的使用者名稱（更清楚）
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'product_id',
            'version',
            'owner',
            'description',
            'created_at'
        ]
        read_only_fields = ['owner', 'created_at']


class DefectSerializer(serializers.ModelSerializer):
    assigned_to = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Defect
        fields = [
            'id',
            'product',
            'version',
            'title',
            'description',
            'steps_to_reproduce',
            'tester_id',
            'reporter_email',
            'severity',
            'priority',
            'status',
            'assigned_to',
            'date_reported',
            'date_fixed'
        ]

    def get_fields(self):
        """根據角色和 HTTP 方法動態控制欄位 + status choices"""
        fields = super().get_fields()
        user = self.context['request'].user
        method = self.context['request'].method   # 判斷是 GET 還是 POST

        # ==================== Tester 的處理 ====================
        if user.groups.filter(name='Tester').exists():
            if method == 'POST':
                # Tester 在提交時，只顯示允許填寫的欄位
                fields_to_hide = ['version', 'status', 'severity', 'priority', 'date_fixed', 'assigned_to']
                for field in fields_to_hide:
                    fields.pop(field, None)

        # ==================== Developer 和 Product Owner 的處理 ====================
        else:
            if method == 'PUT' and 'status' in fields:
                # Developer 只看到這四種 status
                if user.groups.filter(name='Developer').exists():
                    fields['status'].choices = [
                        ('open', 'Open'),
                        ('assigned', 'Assigned'),
                        ('cannot reproduce', 'Cannot reproduce'),
                        ('fixed', 'Fixed')
                    ]

                # Product Owner 只看到這些 status
                elif user.groups.filter(name='Product Owner').exists():
                    fields['status'].choices = [
                        ('new', 'New'),
                        ('open', 'Open'),
                        ('rejected', 'Rejected'),
                        ('reopened', 'Reopened'),
                        ('resolved', 'Resolved'),
                        ('duplicate', 'Duplicate')
                    ]

        return fields

    # 全局唯讀欄位
    read_only_fields = [
        'severity',
        'priority',
        'date_reported',
        'date_fixed'
    ]