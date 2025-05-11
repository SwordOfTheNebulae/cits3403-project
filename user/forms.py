from django import forms

from .models import *


class Login(forms.Form):
    username = forms.CharField(
        label="nickname",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control required", 'placeholder': 'nickname'}),

    )
    password = forms.CharField(
        label="password",
        widget=forms.PasswordInput(attrs={"class": "form-control required", 'placeholder': 'password'}),
    )


class Edit(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "password"]
        labels = {
            "password": "password",
            "name": "nickname",
            "email": "email",
        }
        widgets = {
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

        def clean_name(self):
            name = self.cleaned_data.get("name")
            result = User.objects.filter(name=name)
            if result:
                raise forms.ValidationError("Name already exists")
            return name


class RegisterForm(forms.Form):
    username = forms.CharField(
        label="nickname(cannot be repeated)",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", 'placeholder': 'nickname(cannot be repeated)'}),
    )
    email = forms.EmailField(
        label="email", widget=forms.EmailInput(attrs={"class": "form-control", 'placeholder': 'email'})
    )
    password1 = forms.CharField(
        label="password",
        max_length=128,
        widget=forms.PasswordInput(attrs={"class": "form-control", 'placeholder': 'password'}),
    )
    password2 = forms.CharField(
        label="confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control", 'placeholder': 'confirm password'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if len(username) < 6:
            raise forms.ValidationError(
                "Your username must be at least 6 characters long."
            )
        elif len(username) > 50:
            raise forms.ValidationError("Your username is too long.")
        else:
            filter_result = User.objects.filter(username=username)
            if len(filter_result) > 0:
                raise forms.ValidationError("Your username already exists.")
        return username

    def clean_name(self):
        name = self.cleaned_data.get("name")
        filter_result = User.objects.filter(name=name)
        if len(filter_result) > 0:
            raise forms.ValidationError("Your name already exists.")
        return name

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 6:
            raise forms.ValidationError("Your password is too short.")
        elif len(password1) > 20:
            raise forms.ValidationError("Your password is too long.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password mismatch. Please enter again.")
        return password2


class MovieUploadForm(forms.ModelForm):
    class Meta:
        model = MovieUpload
        fields = ['csv_file']
        widgets = {
            'csv_file': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': '.csv',
                'data-browse': 'Browse',
                'lang': 'en'
            }),
        }
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise forms.ValidationError("Only CSV files are allowed")
            # 可以添加其他文件验证，例如大小限制
            if csv_file.size > 5 * 1024 * 1024:  # 5MB限制
                raise forms.ValidationError("File size cannot exceed 5MB")
        return csv_file


class MovieManualForm(forms.ModelForm):
    # 使用CharField并手动处理日期，使其更加用户友好
    years_str = forms.CharField(
        label="Release Date", 
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "YYYY-MM-DD"}),
        help_text="Format: YYYY-MM-DD"
    )
    
    # 使用多选框处理标签
    tag_choices = forms.ModelMultipleChoiceField(
        queryset=Tags.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Movie Tags"
    )
    
    class Meta:
        model = Movie
        fields = [
            'name', 'director', 'country', 'leader', 
            'd_rate_nums', 'd_rate', 'intro', 'image_link'
        ]
        labels = {
            'name': 'Movie Name',
            'director': 'Director',
            'country': 'Country',
            'leader': 'Lead Actors',
            'd_rate_nums': 'Douban Rating Count',
            'd_rate': 'Douban Rating',
            'intro': 'Description',
            'image_link': 'Cover Image',
        }
        widgets = {
            'name': forms.TextInput(attrs={"class": "form-control"}),
            'director': forms.TextInput(attrs={"class": "form-control"}),
            'country': forms.TextInput(attrs={"class": "form-control"}),
            'leader': forms.TextInput(attrs={"class": "form-control"}),
            'd_rate_nums': forms.NumberInput(attrs={"class": "form-control"}),
            'd_rate': forms.TextInput(attrs={"class": "form-control"}),
            'intro': forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            'image_link': forms.FileInput(attrs={
                "class": "form-control", 
                "data-browse": "Browse",
                "lang": "en"
            }),
        }
        
    def clean_years_str(self):
        years_str = self.cleaned_data.get('years_str')
        try:
            import datetime
            # 转换字符串为日期对象
            years_date = datetime.datetime.strptime(years_str, '%Y-%m-%d').date()
            return years_date
        except ValueError:
            raise forms.ValidationError("Incorrect date format. Please use YYYY-MM-DD format")
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 将处理后的日期赋值给模型的years字段
        instance.years = self.cleaned_data.get('years_str')
        
        if commit:
            instance.save()
            # 处理多对多关系
            self.save_m2m()
            # 手动处理标签
            tags = self.cleaned_data.get('tag_choices')
            if tags:
                instance.tags.set(tags)
                
        return instance


class SharedRecommendationForm(forms.ModelForm):
    shared_with_users = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter usernames separated by commas'
        }),
        help_text='Enter usernames to share with, separated by commas'
    )
    
    class Meta:
        model = SharedRecommendation
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_shared_with_users(self):
        users_text = self.cleaned_data.get('shared_with_users', '')
        if not users_text:
            return []
        
        usernames = [username.strip() for username in users_text.split(',')]
        users = []
        invalid_usernames = []
        
        for username in usernames:
            if not username:
                continue
            try:
                user = User.objects.get(username=username)
                users.append(user)
            except User.DoesNotExist:
                invalid_usernames.append(username)
        
        if invalid_usernames:
            raise forms.ValidationError(
                f"The following usernames were not found: {', '.join(invalid_usernames)}"
            )
        
        return users
