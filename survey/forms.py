from django import forms
from video.models import VideoCategory
from models import *
from django.utils.translation import ugettext_lazy as _
from cities_light.models import Region
import json
from django.contrib.postgres.forms import IntegerRangeField


class SurveyForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(queryset=VideoCategory.objects.all())

    class Meta:
        model = Survey
        fields = ['title', 'category']


class SurveyInfoForm(forms.ModelForm):
    class Meta:
        model = SurveyInfo
        fields = ['desc', 'banner_landing_page', 'banner_landing_page_image']
        labels = {
            'desc': _('Description'),
            'banner_landing_page': _('Banner Landing Page URL'),
            'banner_landing_page_image': _('Banner Landing Page Image'),
        }


class SurveyProfileForm(forms.ModelForm):
    age = IntegerRangeField()
    state = forms.ModelMultipleChoiceField(queryset=Region.objects.all(), required=False)

    class Meta:
        model = SurveyProfile
        fields = ['age', 'gender', 'city', 'state', ]


class SurveyAccountForm(forms.ModelForm):
    class Meta:
        model = SurveyAccount
        fields = ['survey_cost']
        labels = {
            'survey_cost': _('Survey Cost'),
        }

    def clean_survey_cost(self):
        cost = self.cleaned_data['survey_cost']
        if int(cost) <= 1000:
            raise forms.ValidationError("Minimum amount is Rs.1000/-")
        else:
            return self.cleaned_data['survey_cost']


class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['sort_id', 'heading', 'help_text']
        labels = {
            'sort_id': _('Sort Number'),
            'help_text': _('Help Text for Question Set')
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['number', 'sort_id', 'text', 'question_type', 'extra_text', 'required', 'footer_text', 'choices']
        labels = {
            'sort_id': _('Sort Number'),
            'text': _('Question Text'),
            'question_type': _('Quesion Type'),
            'extra_text': _('Extra Question Text'),
            'footer_text': _('Question Footer'),
            'Choices': _('Choices')
        }


class QuestionSetAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questionset = kwargs.pop('questionset')
        promoter = kwargs.pop('promoter')
        super(QuestionSetAnswerForm, self).__init__(*args, **kwargs)

        questions = questionset.question_set.all().order_by('sort_id')

        for question in questions:

            try:
                answer_obj = Answer.objects.get(question_id=question, promoter_id=promoter)
            except Answer.DoesNotExist:
                answer_obj = None

            initial_answer = None
            initial_comment = None

            if answer_obj:
                answer_obj_parsed = json.loads(answer_obj.answer_text)
                initial_answer = answer_obj_parsed.get('text', None)
                initial_comment = answer_obj_parsed.get('comment', None)

            if question.question_type == 'CH1':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                                                            choices=((choice,
                                                                                                      choice)
                                                                                                     for choice in
                                                                                                     question.choices),
                                                                                            label=question.text,
                                                                                            required=True,
                                                                                            initial=initial_answer)
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                                                            choices=((choice,
                                                                                                      choice)
                                                                                                     for choice in
                                                                                                     question.choices),
                                                                                            label=question.text,
                                                                                            initial=initial_answer
                                                                                            )
            elif question.question_type == 'CH2':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                                                            choices=((choice,
                                                                                                      choice)
                                                                                                     for choice in
                                                                                                     question.choices),
                                                                                            label=question.text,
                                                                                            required=True,
                                                                                            initial=initial_answer)
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                                                            choices=((choice,
                                                                                                      choice)
                                                                                                     for choice in
                                                                                                     question.choices),
                                                                                            label=question.text,
                                                                                            initial=initial_answer
                                                                                            )
                self.fields['ques-' + str(question.id) + '-comment'] = forms.CharField(max_length=128, label="Comment",
                                                                                       initial=initial_comment)

            elif question.question_type == 'CH3':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.CharField(widget=forms.TextInput,
                                                                                          label=question.text,
                                                                                          required=True,
                                                                                          initial=initial_answer)
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.CharField(widget=forms.Textarea,
                                                                                          label=question.text,
                                                                                          initial=initial_answer)
            elif question.question_type == 'CH4':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=((choice, choice) for choice in question.choices),
                        label=question.text,
                        required=True,
                        initial=initial_answer)
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=((choice, choice) for choice in question.choices),
                        label=question.text,
                        initial=initial_answer
                    )
            elif question.question_type == 'CH6':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=((choice, choice) for choice in question.choices),
                        label=question.text,
                        required=True,
                        initial=initial_answer)
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=((choice, choice) for choice in question.choices),
                        label=question.text,
                        initial=initial_answer
                    )
                self.fields['ques-' + str(question.id) + '-comment'] = forms.CharField(max_length=128, label="Comment",
                                                                                       initial=initial_comment)

            elif question.question_type == 'CH7':
                if question.required:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.IntegerField(required=True,
                                                                                             label=question.text,
                                                                                             initial=int(
                                                                                                 initial_answer))
                else:
                    self.fields['ques-' + str(question.id) + '-answer'] = forms.IntegerField(label=question.text,
                                                                                             initial=int(
                                                                                                 initial_answer))


QuestionSetFormSet = forms.inlineformset_factory(Survey, QuestionSet, QuestionSetForm, extra=1)
QuestionFormSet = forms.inlineformset_factory(QuestionSet, Question, QuestionForm, extra=5)
