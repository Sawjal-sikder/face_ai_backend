from .models import analysesBalance


def update_user_analysis_balance(user, plan):
    balance_obj, created = analysesBalance.objects.get_or_create(user=user)

    if plan.analyses_per_interval == -1:
        # Unlimited plan
        balance_obj.balance = 999999
    else:
        # Reset balance to plan credits
        balance_obj.balance = plan.analyses_per_interval

    balance_obj.save()
    return balance_obj


def deduct_analysis(user):
    balance_obj = analysesBalance.objects.get(user=user)

    # Unlimited
    if balance_obj.balance >= 999999:
        return True

    if balance_obj.balance <= 0:
        return False

    balance_obj.balance -= 1
    balance_obj.save()
    return True
