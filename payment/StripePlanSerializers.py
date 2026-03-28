from rest_framework import serializers #type: ignore
from .models import StripePlan, Subscription

import os
import stripe #type: ignore

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripePlan
        fields = ['id', 'name', 'amount', 'interval', 'stripe_price_id', 'credits']
        read_only_fields = ['id', 'stripe_price_id']
        
    def create(self, validated_data):
        name = validated_data.get('name')
        amount = validated_data.get('amount')
        interval = validated_data.get('interval')
        credits = validated_data.get('credits')
                        
        # create product/subscription plan in Stripe
        try:
            stripe_product = stripe.Product.create(name=name)
        except Exception as e:
            print(f"Error creating Stripe product: {e}")
            raise serializers.ValidationError("Failed to create product in Stripe")
            
        # create price in Stripe
        try:
            stripe_price = stripe.Price.create(
                unit_amount=int(amount * 100),  # Stripe expects amount in cents
                currency='eur',
                recurring={'interval': interval},
                product=stripe_product.id,
            )
        except Exception as e:
            print(f"Error creating Stripe price: {e}")
            raise serializers.ValidationError("Failed to create price in Stripe")
            
        # save the plan in our database
        if stripe_price and stripe_price.id:
            validated_data['stripe_price_id'] = stripe_price.id   
        else:
            raise serializers.ValidationError("Stripe price creation did not return a valid price ID")         
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.amount = validated_data.get('amount', instance.amount)
        instance.interval = validated_data.get('interval', instance.interval)
        instance.credits = validated_data.get('credits', instance.credits)
        
        # update name in Stripe
        try:
            stripe.Product.modify(
                stripe.Price.retrieve(instance.stripe_price_id).product,
                name=instance.name
            )
        except Exception as e:
            print(f"Error updating Stripe product name: {e}")
        
        # create new price in Stripe if amount or interval changed
        if 'amount' in validated_data or 'interval' in validated_data:
            try:
                stripe_price = stripe.Price.create(
                    unit_amount=int(instance.amount * 100),
                    currency='eur',
                    recurring={'interval': instance.interval},
                    product=stripe.Price.retrieve(instance.stripe_price_id).product,
                )
                instance.stripe_price_id = stripe_price.id
            except Exception as e:
                print(f"Error creating new Stripe price: {e}")
        instance.save()
        return instance