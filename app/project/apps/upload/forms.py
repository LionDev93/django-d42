from django.forms import Form, FileField, EmailField, IntegerField

class UploadForm(Form):
    gdrive_file = FileField()
    email = EmailField()
    ticket_number = IntegerField(min_value=1, required=False)

