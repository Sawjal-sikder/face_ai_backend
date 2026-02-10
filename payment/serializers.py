from rest_framework import serializers #type: ignore
from .models import Plan, PaypalEvent, AnalysisCreditTransaction

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'amount',
            'interval',
            'credits',
            'active'
        ]




class PaypalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaypalEvent
        fields = ['id', 'user', 'plan','amount', 'credits', 'event_response', 'created_at']
        read_only_fields = ('id', 'user', 'amount', 'credits', 'created_at')
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["user"] = instance.user.full_name if instance.user else None
        representation["plan"] = instance.plan.name if instance.plan else None
        return representation
    
    def create(self, validated_data):
        request = self.context.get("request")
        plan = validated_data.get("plan")
        
        if not plan:
            raise serializers.ValidationError({"plan": "Plan is required."})
        
        validated_data["amount"] = plan.amount
        validated_data["credits"] = plan.credits
        paypal_event = super().create(validated_data)
        
        # create credit transaction
        AnalysisCreditTransaction.objects.create(
            user=request.user,
            credits=plan.credits,
            type="purchase",
            reason=f"Purchase for plan {plan.name} and amount {plan.amount}",
        )
        return paypal_event
    
    
class AnalysisCreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisCreditTransaction
        fields = "__all__"
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["user"] = instance.user.full_name if instance.user else None
        return representation