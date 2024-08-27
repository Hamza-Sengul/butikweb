from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    description = models.TextField()
    features = models.TextField(help_text="Separate each feature with a newline.")

    def get_features(self):
        return self.features.split('\n')

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"{self.product.name} Image"
    
class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    rating = models.PositiveIntegerField(default=1)  # Rating between 1 and 5
    created_at = models.DateTimeField(auto_now_add=True)

    def masked_name(self):
        return f"{self.name[0]}{'*' * (len(self.name) - 1)} {self.surname[0]}{'*' * (len(self.surname) - 1)}"

    def __str__(self):
        return f"{self.name} {self.surname} - {self.product.name}"