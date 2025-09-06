from django.db import models
from pip._vendor import vendored


class Category(models.Model):
    CATEGORY_TYPES = (
        ('expense', 'Expense'),
        ('income', 'Income'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    vendor = models.CharField(max_length=32, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_category'
        ordering = ['category_type', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name}"
