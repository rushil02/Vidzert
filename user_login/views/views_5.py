from django.core import signing
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from user_login.forms import MobileVerify
from admin_custom.tasks import send_sms_async
from django.contrib.auth.decorators import login_required
import string
import random
from django.shortcuts import render


def verify_email(request, token):
    try:
        unsign_data = signing.loads(token, salt='verify_email')
    except signing.BadSignature:
        return HttpResponse("Bad sign")
    else:
        email = unsign_data['email']
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return HttpResponse(" NO Verified")
        else:
            user.email_verified = True
            user.save()
            return HttpResponse("Verified")


@login_required
def verify_mobile(request):
    user = request.user
    if not user.mobile_verified:
        mobile = request.user.mobile
        if request.POST:
            gen_code = request.session.pop("OTP")
            form = MobileVerify(request.POST, gen_code=gen_code)
            if form.is_valid():
                user.mobile_verified = True
                user.save()
                return HttpResponse("Mobile Verified")
            else:
                return render(request, 'verify_mob.html', {"form": form})
        else:
            code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
            request.session['OTP'] = code
            send_sms_async.delay(code, mobile)
            form = MobileVerify(gen_code=code)
            return render(request, 'verify_mob.html', {"form": form})
    else:
        return HttpResponse("Already verified")
