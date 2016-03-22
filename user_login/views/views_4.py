from admin_custom.models import ActivityLog
from django.shortcuts import render
from admin_custom.tasks import send_mail_async
import datetime
from django.core import signing
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import get_user_model
from user_login.forms import PasswordRecoveryForm, PasswordResetForm


class SaltMixin(object):
    salt = 'password_recovery'
    url_salt = 'password_recovery_url'


def loads_with_timestamp(value, salt):
    """Returns the unsigned value along with its timestamp, the time when it
    got dumped."""
    try:
        signing.loads(value, salt=salt, max_age=-1)
    except signing.SignatureExpired as e:
        age = float(str(e).split('Signature age ')[1].split(' >')[0])
        timestamp = timezone.now() - datetime.timedelta(seconds=age)
        return timestamp, signing.loads(value, salt=salt)


class RecoverDone(SaltMixin, generic.TemplateView):
    template_name = 'password_reset/reset_sent.html'

    def get_context_data(self, **kwargs):
        ctx = super(RecoverDone, self).get_context_data(**kwargs)
        try:
            ctx['timestamp'], ctx['email'] = loads_with_timestamp(
                self.kwargs['signature'], salt=self.url_salt,
            )
        except signing.BadSignature:
            raise Http404
        return ctx


class Recover(SaltMixin, generic.FormView):
    case_sensitive = True
    form_class = PasswordRecoveryForm
    template_name = 'password_reset/recovery_form.html'
    success_url_name = 'user:password_reset_sent'
    email_template_name = 'password_reset/recovery_email.txt'
    email_subject_template_name = 'password_reset/recovery_email_subject.txt'
    # search_fields = ['username', 'email']

    def get_success_url(self):
        return reverse(self.success_url_name, args=[self.mail_signature])

    def get_context_data(self, **kwargs):
        kwargs['url'] = self.request.get_full_path()
        return super(Recover, self).get_context_data(**kwargs)

    def send_notification(self):
        context = {
            'user': self.user.name,
            'username': self.user.email,
            'token': signing.dumps(self.user.pk, salt=self.salt),
            'secure': self.request.is_secure(),
        }
        body = loader.render_to_string(self.email_template_name,
                                       context).strip()
        subject = loader.render_to_string(self.email_subject_template_name,
                                          context).strip()
        send_recover_email(subject, body, self.user.email)

    def form_valid(self, form):
        self.user = form.cleaned_data['email']
        if self.user:
            self.send_notification()
            email = self.user.email
            self.mail_signature = signing.dumps(email, salt=self.url_salt)
            return super(Recover, self).form_valid(form)
        else:
            return HttpResponse("Mail sent")


class Reset(SaltMixin, generic.FormView):
    form_class = PasswordResetForm
    token_expires = 15 * 60  # 15 minutes
    template_name = 'password_reset/reset.html'
    success_url = reverse_lazy('user:password_reset_done')

    @method_decorator(sensitive_post_parameters('password1', 'password2'))
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.user = None

        try:
            pk = signing.loads(kwargs['token'], max_age=self.token_expires,
                               salt=self.salt)
        except signing.BadSignature:
            return self.invalid()

        self.user = get_object_or_404(get_user_model(), pk=pk)
        return super(Reset, self).dispatch(request, *args, **kwargs)

    def invalid(self):
        return self.render_to_response(self.get_context_data(invalid=True))

    def get_form_kwargs(self):
        kwargs = super(Reset, self).get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(Reset, self).get_context_data(**kwargs)
        if 'invalid' not in ctx:
            ctx.update({
                'username': self.user.email,
                'token': self.kwargs['token'],
            })
        return ctx

    def form_valid(self, form):
        form.save()
        return redirect(self.get_success_url())


class ResetDone(generic.TemplateView):
    template_name = 'password_reset/recovery_done.html'


def send_recover_email(subject, body, email):
    send_mail_async.delay(subject, body, [email])

