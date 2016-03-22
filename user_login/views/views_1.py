from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import login, logout, authenticate
from user_login.forms import UserCreationForm, LoginForm, LoginFormCaptcha, UserCreationFormCaptcha
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from admin_custom.models import ErrorLog, ActivityLog
from admin_custom.tasks import send_mail_async
from video.models import Video
from promoter.models import PromoterProfile
import datetime
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core import signing


def main(request):
    if request.user.is_authenticated():
        return check_user(request)
    else:
        video_list = unsubscribed_profiling_v2()

        sign_up_form = UserCreationForm(request.POST or None, prefix='sign_up_form')
        login_form = LoginForm(request.POST or None, prefix='login_form')

        if request.POST:
            if 'sign_up_form-email' in request.POST:
                if sign_up_form.is_valid():
                    user_obj = sign_up_form.save(commit=False)
                    user_obj.user_type = 'P'
                    user_obj.save()
                    new_user = authenticate(email=user_obj.email,
                                            password=sign_up_form.cleaned_data['password1'])
                    login(request, new_user)
                    send_registration_email(new_user)
                    activity_meta = {
                        "method": "user_login.views.main",
                        "form_validation": "True"
                    }
                    ActivityLog.objects.create_log(request=request, action_type="Sign Up",
                                                   act_meta=activity_meta)
                    return redirect('/pr/')
                else:
                    return sign_up_captcha(request)

            if 'login_form-email' in request.POST:
                if login_form.is_valid():
                    user = login_form.get_user()
                    login(request, user)
                    activity_meta = {
                        "method": "user_login.views.main",
                        "form_validation": "True"
                    }
                    ActivityLog.objects.create_log(request=request, action_type="Sign Up",
                                                   act_meta=activity_meta)
                    return check_user(request)

                else:
                    return user_login_captcha(request)
        else:
            # Pagination
            paginator = Paginator(video_list, 12)  # Show 12 contacts per page

            page = request.GET.get('page')
            try:
                videos = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                videos = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                videos = paginator.page(paginator.num_pages)

            context = {
                "form": sign_up_form,
                "login_form": login_form,
                "queryset": videos,
            }
            activity_meta = {
                "method": "user_login.views.main",
                "page_number": request.GET.get('page')  # TODO: Remove after AJAX implemented
            }
            ActivityLog.objects.create_log(request=request, action_type="Main Page",
                                           act_meta=activity_meta)
            return render(request, 'user_login/main.html', context)


def check_user(request):
    if request.user.is_active:
        user_type = request.user.get_user_type()
        if user_type == 'P':
            return redirect('/pr/')
        elif user_type == 'C':
            return redirect('/cl/')
        elif user_type == 'S':
            return redirect('/staff/')
        elif user_type == 'A':
            return redirect('/admin/')
    else:
        error_meta = {
            "method": "user_login.views.check_user",
        }
        ErrorLog.objects.create_log(error_code=101, error_type='Logged In User Not Active', error_meta=error_meta,
                                    request=request)
        logout(request)
        return redirect('/')


def user_login(request):
    login_form = LoginForm(request.POST or None, prefix='login_form')
    if request.POST:
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            activity_meta = {
                "method": "user_login.views.user_login",
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request=request, action_type="Log In on different page",
                                           act_meta=activity_meta)
            return check_user(request)
        else:
            return user_login_captcha(request)
    else:
        context = {'login_form': login_form}
        return render(request, 'login.html', context)


@require_POST
def user_login_captcha(request):
    login_form = LoginFormCaptcha(request.POST, prefix='login_form')
    context = {'login_form': login_form}
    if login_form.is_valid():
        user = login_form.get_user()
        login(request, user)
        activity_meta = {
            "method": "user_login.views.user_login_captcha",
            "form_validation": "True"
        }
        ActivityLog.objects.create_log(request=request, action_type="Login with captcha",
                                       act_meta=activity_meta)
        return check_user(request)

    else:
        activity_meta = {
            "method": "user_login.views.user_login_captcha",
            "form_validation": "False"
        }
        ActivityLog.objects.create_log(request=request, action_type="Login with captcha",
                                       act_meta=activity_meta)
        return render(request, 'login.html', context)


def sign_up(request):
    sign_up_form = UserCreationForm(request.POST or None, prefix='sign_up_form')
    if request.POST:
        if sign_up_form.is_valid():
            user_obj = sign_up_form.save(commit=False)
            user_obj.user_type = 'P'
            user_obj.save()
            new_user = authenticate(email=user_obj.email,
                                    password=sign_up_form.cleaned_data['password1'])
            login(request, new_user)
            send_registration_email(new_user)
            activity_meta = {
                "method": "user_login.views.sign_up",
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request=request, action_type="Sign Up in different page",
                                           act_meta=activity_meta)
            return redirect('/pr/')
        else:
            return sign_up_captcha(request)
    else:
        context = {'sign_up_form': sign_up_form}
        return render(request, 'sign_up.html', context)


@require_POST
def sign_up_captcha(request):
    sign_up_form = UserCreationFormCaptcha(request.POST, prefix='sign_up_form')
    context = {'sign_up_form': sign_up_form}
    if sign_up_form.is_valid():
        user_obj = sign_up_form.save(commit=False)
        user_obj.user_type = 'P'
        user_obj.save()
        new_user = authenticate(email=user_obj.email,
                                password=sign_up_form.cleaned_data['password1'])
        login(request, new_user)
        send_registration_email(new_user)
        activity_meta = {
            "method": "user_login.views.sign_up_captcha",
            "form_validation": "True"
        }
        ActivityLog.objects.create_log(request=request, action_type="Sign up on separate page",
                                       act_meta=activity_meta)
        return redirect('/pr/')
    else:
        activity_meta = {
            "method": "user_login.views.sign_up_captcha",
            "form_validation": "False"
        }
        ActivityLog.objects.create_log(request=request, action_type="Sign up on separate page",
                                       act_meta=activity_meta)
        return render(request, 'sign_up.html', context)


def send_registration_email(user):
    subject, from_email, recipient = 'Vidzert Account Verification', 'from@example.com', user.email
    signed_data = signing.dumps({"email": str(recipient)}, salt='verify_email')
    text_content = 'verify/%s' % signed_data
    # html_content = '<a href="enter link here">Click here for verification</a>'
    send_mail_async.delay(subject, text_content, [recipient])


def unsubscribed_profiling_v2():
    videos = []
    featured_everyone_videos = Video.objects.get_featured_everyone_videos()
    non_featured_everyone_videos = Video.objects.get_non_featured_everyone_videos()
    featured_videos = Video.objects.get_featured_non_everyone_videos()
    non_featured_videos = Video.objects.get_non_featured_non_everyone_videos()
    videos.extend(featured_everyone_videos)
    videos.extend(featured_videos)
    videos.extend(non_featured_everyone_videos)
    videos.extend(non_featured_videos)
    return videos


def client_registration(request):
    if request.user.is_authenticated():
        return redirect('/')
    else:
        sign_up_form = UserCreationForm(request.POST or None, prefix='sign_up_form')
        if request.POST:
            if sign_up_form.is_valid():
                form = sign_up_form.save(commit=False)
                form.user_type = 'C'
                form.save()
                new_user = authenticate(email=form.email,
                                        password=request.POST['sign_up_form-password1'])
                login(request, new_user)
                send_registration_email(new_user)
                activity_meta = {
                    "method": "user_login.views.client_registration",
                    "form_validation": "True"
                }
                ActivityLog.objects.create_log(request=request, action_type="Client Sign up",
                                               act_meta=activity_meta)
                return redirect('/cl/')
            else:
                return client_registration_captcha(request)
        else:
            context = {
                "form": sign_up_form
            }
            return render(request, 'client_registration.html', context)


@require_POST
def client_registration_captcha(request):
    sign_up_form = UserCreationFormCaptcha(request.POST, prefix='sign_up_form')
    context = {'sign_up_form': sign_up_form}
    if sign_up_form.is_valid():
        form = sign_up_form.save(commit=False)
        form.user_type = 'C'
        form.save()
        new_user = authenticate(email=form.email,
                                password=request.POST['sign_up_form-password1'])
        login(request, new_user)
        send_registration_email(new_user)
        activity_meta = {
            "method": "user_login.views.client_registration_captcha",
            "form_validation": "True"
        }
        ActivityLog.objects.create_log(request=request, action_type="Client Captcha Sign up",
                                       act_meta=activity_meta)
        return redirect('/cl/')
    else:
        activity_meta = {
            "method": "user_login.views.client_registration_captcha",
            "form_validation": "False"
        }
        ActivityLog.objects.create_log(request=request, action_type="Client Captcha Sign up",
                                       act_meta=activity_meta)
        return render(request, 'client_registration.html', context)


def top_earners(request):
    latest_video_earners_list = []
    latest_survey_earners_list = []
    overall_top_earners_list = []

    date_from = datetime.datetime.now() - datetime.timedelta(days=1)
    date_from = timezone.make_aware(date_from, timezone.get_current_timezone())

    overall_top_earners = PromoterProfile.objects.filter(promoteraccount__total_coins__gt=0).order_by(
        '-promoteraccount__total_coins').select_related('promoter_id', 'promoteraccount__total_coins')[:3]
    latest_video_earners = PromoterProfile.objects.filter(videopromoterlog__create_time__gte=date_from).annotate(
        coins=Sum('videopromoterlog__coins')).order_by('-coins').select_related('promoter_id')[:3]
    latest_survey_earners = PromoterProfile.objects.filter(surveypromoterlog__create_time__gte=date_from).annotate(
        coins=Sum('surveypromoterlog__coins')).order_by('-coins').select_related('promoter_id')[:3]

    # Serializer
    for earner in latest_video_earners:
        earner_dict = {
            "name": earner.promoter_id.name,
            "coins": earner.coins
        }
        latest_video_earners_list.append(earner_dict)

    for earner in latest_survey_earners:
        earner_dict = {
            "name": earner.promoter_id.name,
            "coins": earner.coins
        }
        latest_survey_earners_list.append(earner_dict)

    for earner in overall_top_earners:
        earner_dict = {
            "name": earner.promoter_id.name,
            "coins": earner.promoteraccount.total_coins
        }
        overall_top_earners_list.append(earner_dict)

    response = JsonResponse({
        "latest_video_earners_list": latest_video_earners_list,
        "latest_survey_earners_list": latest_survey_earners_list,
        "overall_top_earners_list": overall_top_earners_list
    })
    return response


@login_required
def logout_view(request):
    logout(request)
    return redirect('/')
