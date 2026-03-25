from rest_framework import serializers
from .models import Defect

class DefectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Defect
        fields = '__all__'          # 把所有欄位都開放給 API
        read_only_fields = ['date_reported', 'date_fixed']   # 這兩個欄位不能讓別人改
        