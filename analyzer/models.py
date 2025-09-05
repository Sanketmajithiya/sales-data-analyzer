from django.db import models

class UploadLog(models.Model):
    upload_time = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='Pending')  # Success / Failed
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.file_name} ({self.status})"


class ProductSales(models.Model):
    upload = models.ForeignKey(UploadLog, on_delete=models.CASCADE, related_name='sales')
    product_name = models.CharField(max_length=100)
    sales = models.FloatField()
    date = models.DateField()

    def __str__(self):
        return f"{self.product_name} - {self.sales} on {self.date}"
