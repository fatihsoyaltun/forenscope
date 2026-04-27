from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Şifre')
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Rol',
        empty_label='— Rol Seçin —'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            user.groups.set([self.cleaned_data['group']])
        return user


class UserEditForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Rol',
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                self.fields['group'].initial = self.instance.groups.first()
            except Exception:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            group = self.cleaned_data.get('group')
            if group:
                user.groups.set([group])
        return user
