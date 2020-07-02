from django import forms
from django.forms import ValidationError
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext as _

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout

from .models import KPI, KPIEntry, KPICategory, Department, Beamline

import calendar


class BodyHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.use_custom_control = True
        self.form_show_errors = False


class FooterHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.disable_csrf = True
        self.form_show_errors = False


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ['name', 'acronym', 'division']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.name)
            self.body.form_action = reverse_lazy('department-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New Department"
            self.body.form_action = reverse_lazy('new-department')
        self.body.layout = Layout(
            Div(
                Div('name', css_class="col-12"),
                Div('acronym', css_class="col-6"),
                Div('division', css_class="col-6"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class BeamlineForm(forms.ModelForm):

    class Meta:
        model = Beamline
        fields = ['name', 'acronym', 'department']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.name)
            self.body.form_action = reverse_lazy('beamline-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New Beamline"
            self.body.form_action = reverse_lazy('new-beamline')
        self.body.layout = Layout(
            Div(
                Div('name', css_class="col-12"),
                Div('acronym', css_class="col-6"),
                Div('department', css_class="col-6"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPIForm(forms.ModelForm):

    class Meta:
        model = KPI
        fields = ['name', 'description', 'category', 'kind', 'priority', 'department']
        widgets = {
            'description': forms.Textarea(attrs={"cols": 54, "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"Edit KPI"
            self.body.form_action = reverse_lazy('kpi-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New KPI"
            self.body.form_action = reverse_lazy('new-kpi')
        self.body.layout = Layout(
            Div(
                Div('category', css_class="col-10"),
                Div('priority', css_class="col-2"),
                Div('name', css_class="col-12"),
                Div('description', css_class="col-12"),
                css_class="row"
            ),
            Div(
                Div('kind', css_class="col-6"),
                Div('department', css_class="col-6"),
                css_class="row"
            )
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class BeamlineMonthForm(forms.ModelForm):
    month = forms.ChoiceField(choices=[(i, calendar.month_name[i]) for i in range(1,13)], initial=timezone.now().month)
    year = forms.IntegerField(initial=timezone.now().year)

    class Meta:
        model = KPIEntry
        fields = ['beamline',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = u"New Beamline Report"
        self.body.form_action = reverse_lazy('new-month', kwargs={'pk': self.initial.get('beamline').pk})
        self.body.layout = Layout(
            Div(
                Div(Field('beamline', readonly=True), css_class="col-12"),
                Div(Field('year'), css_class="col-6"),
                Div(Field('month'), css_class="col-6"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )

    def clean_month(self):
        try:
            month =int(self.cleaned_data['month'])
        except:
            raise ValidationError(_('Invalid value: %(month)s'), code='invalid', params={'month': self.cleaned_data['month']})
        return month


class KPIEntryForm(forms.ModelForm):

    class Meta:
        model = KPIEntry
        fields = ['value', 'comments', 'beamline', 'kpi', 'month']
        widgets = {
            'comments': forms.Textarea(attrs={"rows": 4}),
            'beamline': forms.HiddenInput(),
            'kpi': forms.HiddenInput(),
            'month': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.form_action = reverse_lazy('kpientry-edit', kwargs={'pk': self.instance.pk})
            kpi = self.instance.kpi
        else:
            self.body.form_action = reverse_lazy('kpientry-new')
            kpi = self.initial['kpi']
        if kpi.kind == KPI.TYPE.TEXT:
            self.fields['value'].widget = forms.HiddenInput()
        self.body.title = u"{}".format(kpi.name)
        self.body.layout = Layout(
            Div(
                'beamline', 'kpi', 'month',
                HTML("<div class='jumbotron p-3 mb-2 col-12'>{}</div>".format(linebreaksbr(kpi.description))),
                Div('value', css_class="col-3"),
                Div('comments', css_class="col-12 w-100"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPICategoryForm(forms.ModelForm):

    class Meta:
        model = KPICategory
        fields = ['name', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={"cols": 54, "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.name)
            self.body.form_action = reverse_lazy('category-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New KPI Category"
            self.body.form_action = reverse_lazy('new-category')
        self.body.layout = Layout(
            Div(
                Div('priority', css_class="col-2"),
                Div('name', css_class="col-10"),
                Div('description', css_class="col-12 w-100"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )
