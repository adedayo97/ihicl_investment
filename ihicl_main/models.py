from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models import F
from decimal import Decimal

class InvestmentSector(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, blank=True)  # For Font Awesome icons
    
    def __str__(self):
        return self.name

class InvestmentOpportunity(models.Model):
    sector = models.ForeignKey(InvestmentSector, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    featured_image = models.ImageField(upload_to='investment_images/')
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    expected_return = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='team/')
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} - {self.position}"

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}'s testimonial"

class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question
    

class ContactSubmission(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=50)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    

# models.py - Update InvestorProfile model
# models.py - Update InvestorProfile model
class InvestorProfile(models.Model):
    TITLE_CHOICES = [
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Ms', 'Ms'),
        ('Dr', 'Dr'),
        ('Prof', 'Prof'),
        ('Other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_profile')
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True, null=True)
    other_title = models.CharField(max_length=50, blank=True, null=True)
    telephone = models.CharField(max_length=20)
    address = models.TextField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    newsletter_subscription = models.BooleanField(default=False)  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Investor Profile"
    
    def get_full_title(self):
        if self.title == 'Other' and self.other_title:
            return self.other_title
        return self.get_title_display()



# Add these models to your existing models.py

# Make the project field optional instead of removing it
# models.py - Update Investment model with defaults
class Investment(models.Model):
    INVESTMENT_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    )
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    project = models.ForeignKey(InvestmentOpportunity, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date_invested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=INVESTMENT_STATUS, default='active')
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    @property
    def investment_type(self):
        if self.project and self.project.title:
            return self.project.title
        return "General Investment"
    
    @property
    def roi_percentage(self):
        try:
            amount = float(self.amount or 0)
            current_value = float(self.current_value or 0)
            if amount > 0:
                return float(((current_value - amount) / amount * 100))
            return 0.00
        except (TypeError, ValueError):
            return 0.00
    
    @property
    def status_color(self):
        colors = {
            'active': 'success',
            'completed': 'info',
            'pending': 'warning',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def __str__(self):
        return f"{self.investor.username} - {self.investment_type} - ₦{self.amount}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('investment', 'Investment'),
        ('return', 'Return'),
        ('withdrawal', 'Withdrawal'),
        ('dividend', 'Dividend'),
    )
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₦{self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Generate reference if not exists
        if not self.reference:
            import random
            import string
            self.reference = f"TX{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
        
        # Only process withdrawals when status changes to completed
        if self.transaction_type == 'withdrawal' and self.status == 'completed':
            if self.pk:  # Check if this is an update (not a new object)
                try:
                    original = Transaction.objects.get(pk=self.pk)
                    if original.status != 'completed':  # Only deduct if status changed to completed
                        self.process_withdrawal()
                except Transaction.DoesNotExist:
                    # New transaction, process withdrawal
                    self.process_withdrawal()
        
        super().save(*args, **kwargs)
    
    def process_withdrawal(self):
        """Process withdrawal by deducting from investments"""
        investments = Investment.objects.filter(
            investor=self.user,
            status__in=['active', 'completed']
        ).order_by('date_invested')
        
        remaining_amount = self.amount  # Already a Decimal
        for investment in investments:
            if remaining_amount <= 0:
                break
            
            current_value = investment.current_value or Decimal('0.00')  # Keep as Decimal
            if current_value >= remaining_amount:
                investment.current_value = current_value - remaining_amount
                investment.save()
                remaining_amount = Decimal('0.00')
            else:
                remaining_amount -= current_value
                investment.current_value = Decimal('0.00')
                investment.save()




class NextOfKin(models.Model):
    investor = models.OneToOneField(
        InvestorProfile, 
        on_delete=models.CASCADE, 
        related_name='next_of_kin'
    )
    full_name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.relationship}) - {self.investor.user.get_full_name()}"
    

class StatementRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    reference = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Simplified save method - let signals handle reference generation
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Statement Request #{self.reference} - {self.user.email}"
    
    class Meta:
        ordering = ['-request_date']


# Add this at the BOTTOM of your models.py file (after all model definitions)
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=StatementRequest)
def generate_statement_reference(sender, instance, created, **kwargs):
    """
    Signal to generate reference for StatementRequest after it's created
    """
    if created and not instance.reference:
        instance.reference = f"STMT-{instance.id:06d}"
        # Use update() to avoid triggering save signals recursively
        StatementRequest.objects.filter(id=instance.id).update(reference=instance.reference)