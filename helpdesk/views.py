from django.shortcuts import render, redirect
from forms import TicketAuthenticatedUserForm, MessageForm, TicketAnonymousUserForm, TicketStatusForm, TicketAdminForm
from django.http import HttpResponse
from models import Ticket
from django.contrib.auth.decorators import permission_required

# Create your views here.


def submit_ticket(request):
    if request.user.is_authenticated():
        ticket_form = TicketAuthenticatedUserForm(request.POST or None)
    else:
        ticket_form = TicketAnonymousUserForm(request.POST or None)
    message_form = MessageForm(request.POST or None)
    ticket_status_form = TicketStatusForm(request.POST or None)
    context = {
        "ticket_form": ticket_form,
        "message_form": message_form,
        "ticket_status_form": ticket_status_form
    }

    if request.POST:
        if ticket_form.is_valid() and message_form.is_valid():
            ticket = ticket_form.save(commit=False)
            if request.user.is_authenticated():
                ticket.submitter_email = request.user.email
                ticket.submitter = request.user

            ticket.save()

            message = message_form.save(commit=False)
            message.ticket = ticket
            message.sender_type = 'U'
            if request.user.is_authenticated():
                message.sender = request.user
            message.save()
            return HttpResponse("Ticket Reference Number is: " + ticket.ref_no)
        else:
            return render(request, 'helpdesk/submit_ticket.html', context)
    else:
        return render(request, 'helpdesk/submit_ticket.html', context)


def show_ticket(request, ticket_uuid):
    try:
        ticket = Ticket.objects.get(uuid=ticket_uuid)
    except:
        return HttpResponse("Invalid Ticket")

    message_form = MessageForm(request.POST or None)
    if request.POST and message_form.is_valid():
        message = message_form.save(commit=False)
        message.ticket = ticket
        if request.user.is_authenticated():
            message.sender = request.user
        message.sender_type = 'U'
        message.save()

    if (request.user.is_authenticated() and ticket.submitter == request.user) or (not request.user.is_authenticated() and ticket.submitter is None):
        messages = ticket.message_set.order_by('create_time')
        context = {
            "ticket": ticket,
            "message_form": message_form,
            "messages": messages
        }
        return render(request, 'helpdesk/view_ticket.html', context)
    else:
        return HttpResponse("Invalid Ticket")


def check_ticket(request):
    ticket_status_form = TicketStatusForm(request.POST or None)
    if request.POST and ticket_status_form.is_valid():
        ref_no = request.POST.get('ticket_ref_no')
        try:
            ticket = Ticket.objects.get(ref_no=ref_no)
        except:
            return submit_ticket(request)
        return redirect('/helpdesk/view/' + str(ticket.uuid) + '/')
    else:
        return submit_ticket(request)


@permission_required('helpdesk.access_staff')
def staff_home(request):
    tickets = Ticket.objects.all().order_by('-status', '-create_time')
    context = {
        "tickets": tickets
    }
    return render(request, "helpdesk/staff_home.html", context)


@permission_required('helpdesk.access_staff')
def staff_ticket_view(request, ticket_uuid):
    try:
        ticket = Ticket.objects.get(uuid=ticket_uuid)
    except:
        return HttpResponse("Invalid Ticket")

    message_form = MessageForm(request.POST or None)
    if request.POST and message_form.is_valid():
        message = message_form.save(commit=False)
        message.ticket = ticket
        message.sender = request.user
        message.sender_type = 'A'
        message.save()

    ticket_status_form = TicketAdminForm(request.POST or None, instance=ticket)
    if request.POST and ticket_status_form.is_valid():
        ticket_status_form.save()
        return redirect('/helpdesk/admin/')

    messages = ticket.message_set.order_by('create_time')
    context = {
        "ticket": ticket,
        "message_form": message_form,
        "messages": messages,
        "ticket_status_form": ticket_status_form
    }
    return render(request, 'helpdesk/staff_ticket_view.html', context)