from django.shortcuts import render
from django.db.models import Sum
import urllib2
import json
from django.http.response import HttpResponse
from models import *
from forms import *
from django.db import transaction
# Create your views here.


# def promoter_transaction_log_enrty(ref_no, promoter, payment_type, coins, amount, TDS):
#     PromoterTransactionLog.objects.create(ref_no=ref_no, promoter_id=promoter, payment_type=payment_type, coins=coins, amount=amount, TDS=TDS)


# for admin_custom
# def get_total_expense():
#     return PromoterTransactionLog.objects.all().aggregate(total_amount=Sum('amount'))


def phone_recharge(promoter, subscriber_type, coins, operator, mobile_number):
    promoter_account = promoter.promoteraccount
    # subscriber type is postpaid or prepaid
    payment_type = 'R'
    # from form
    amount = int(coins/100)
    left_coins = coins % 100
    coins -= left_coins

    TDS = 0

    # Mode = 0 -> Test; 1 -> Live
    mode = 0
    # Username
    username = 'myusername'
    # api kiey
    api_key = 'blah'
    # operator from form
    response = ''
    try:
        latest_obj = PromoterTransactionLog.objects.latest('id')
    except:
        latest_obj_id = 0
    else:
        latest_obj_id = latest_obj.id

    ref_no = "TRAC%012d" % (latest_obj_id + 1)

    if subscriber_type == 'PR':
        response = urllib2.urlopen('https://joloapi.com/api/recharge.php?mode='+str(mode)+'&userid='+username+'&key='+api_key+'&operator='+operator+'&service='+mobile_number+'&amount='+str(amount)+'&orderid='+ref_no+'&type=json')
    elif subscriber_type == 'PO':
        response = urllib2.urlopen('https://joloapi.com/api/cbill.php?mode='+str(mode)+'&userid='+username+'&key='+api_key+'&operator='+operator+'&service='+mobile_number+'&amount='+str(amount)+'&orderid='+ref_no+'&type=json')
    data = json.load(response)

    if data['status'] == 'SUCCESS':
        # todo: promoter money account
        promoter_account.decrement_account_coins(coins - left_coins)
        PromoterTransactionLog.objects.create(ref_no=ref_no, promoter_id=promoter, payment_type=payment_type, coins=coins, amount=amount, TDS=TDS, extra=data, paid=True)
        return HttpResponse('Success. Ref No = ' + ref_no)
    else:
        return HttpResponse("Transaction Failed. Error code:" + data['errorcode'])


@transaction.atomic
def prepaid_recharge_view(request):
    promoter = request.user.promoterprofile
    if request.POST:
        form = RechargeForm(request.POST, promoter=promoter, subscriber_type='PR')
    else:
        form = RechargeForm(initial={"mobile_no": request.user.mobile}, promoter=promoter, subscriber_type='PR')
    context = {
        "form": form
    }
    if request.POST and form.is_valid():
        mobile_no = form.cleaned_data['mobile_no']
        coins = form.cleaned_data['coins']
        operator = form.cleaned_data['operator']
        return phone_recharge(promoter, 'PR', coins, operator, mobile_no)
    else:
        return render(request, 'promoter/recharge.html', context)


@transaction.atomic
def postpaid_recharge_view(request):
    promoter = request.user.promoterprofile
    if request.POST:
        form = RechargeForm(request.POST, promoter=promoter, subscriber_type='PO')
    else:
        form = RechargeForm(initial={"mobile_no": request.user.mobile}, promoter=promoter, subscriber_type='PO')
    context = {
        "form": form
    }
    if request.POST and form.is_valid():
        mobile_no = form.cleaned_data['mobile_no']
        coins = form.cleaned_data['coins']
        operator = form.cleaned_data['operator']
        return phone_recharge(promoter, 'PO', coins, operator, mobile_no)
    else:
        return render(request, 'promoter/recharge.html', context)


@transaction.atomic
def paytm_transfer_view(request):
    promoter = request.user.promoterprofile
    if request.POST:
        form = PayTMForm(request.POST, promoter=promoter)
    else:
        form = PayTMForm(promoter=promoter)
    context = {
        "form": form
    }
    if request.POST and form.is_valid():
        mobile_no = form.cleaned_data['mobile_no']
        coins = int(form.cleaned_data['coins'])
        amount = int(coins/100)
        left_coins = coins % 100
        coins -= left_coins
        TDS = 0
        try:
            latest_obj = PromoterTransactionLog.objects.latest('id')
        except:
            latest_obj_id = 0
        else:
            latest_obj_id = latest_obj.id

        ref_no = "TRAC%012d" % (latest_obj_id + 1)
        payment_type = 'P'
        extra_data = {
            "mobile_number": mobile_no,
            "status": "pending"
        }
        PromoterTransactionLog.objects.create(ref_no=ref_no, promoter_id=promoter, payment_type=payment_type, coins=coins, amount=amount, TDS=TDS, extra=extra_data, paid=False)
        return HttpResponse("Your request has been heard. Transfer will be made shotly. This is your transaction reference no: " + ref_no)
    else:
        return render(request, 'promoter/recharge.html', context)


# def get_paytm_transactions():
#     return PromoterTransactionLog.objects.filter(payment_type='P').order_by('paid')


# def get_transaction(transaction_uuid):
#     return PromoterTransactionLog.objects.get(uuid=transaction_uuid)


# def create_transaction_update(transaction, staff, field_updated, old_value, new_value):
#     TransactionUpdateLog.objects.create(transaction_id=transaction, staff_id=staff, field_updated=field_updated, old_value=old_value, new_value=new_value)