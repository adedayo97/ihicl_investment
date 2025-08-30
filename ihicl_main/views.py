from django.shortcuts import render
from .models import InvestmentSector, InvestmentOpportunity, TeamMember, Testimonial, FAQ,Investment, Transaction,StatementRequest
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import ContactForm
from .models import ContactSubmission,InvestorProfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .forms import ProfileUpdateForm
from django.db.models import Sum, Count, F,Value
from .models import NextOfKin
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from dateutil.relativedelta import relativedelta 
from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.db.models import ExpressionWrapper, F, DecimalField
from django.contrib.auth.forms import AuthenticationForm
from .forms import LoginForm
from .forms import InvestmentForm,WithdrawForm,StatementRequestForm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import uuid
from .forms import InvestmentRegistrationForm  # Import your new form
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import InvestorProfile






def home(request):
    sectors = InvestmentSector.objects.all()
    featured_investments = InvestmentOpportunity.objects.filter(is_featured=True)
    team_members = TeamMember.objects.all()[:4]
    testimonials = Testimonial.objects.filter(is_active=True)
    
    context = {
        'sectors': sectors,
        'featured_investments': featured_investments,
        'team_members': team_members,
        'testimonials': testimonials,
    }
    return render(request, 'ihicl_main/index.html', context)

def about(request):
    team_members = TeamMember.objects.all()
    context = {'team_members': team_members}
    return render(request, 'ihicl_main/about.html', context)

def investments(request):
    sectors = InvestmentSector.objects.all()
    context = {'sectors': sectors}
    return render(request, 'ihicl_main/services.html', context)

def projects(request):
    investments = InvestmentOpportunity.objects.all()
    context = {'investments': investments}
    return render(request, 'ihicl_main/projects.html', context)

def faqs(request):
    faqs = FAQ.objects.all()
    context = {'faqs': faqs}
    return render(request, 'ihicl_main/faqs.html', context)

def roadmap_view(request):
    return render(request, 'ihicl_main/roadmap.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Save to database first
            contact_submission = ContactSubmission.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            
            # Generate a unique reference number
            reference_number = f"CONTACT-{contact_submission.id:06d}"
            
            # Prepare context for email templates
            email_context = {
                'name': name,
                'email': email,
                'phone': phone,
                'subject': subject,
                'message': message,
                'timestamp': timezone.now(),
                'reference': reference_number,
            }
            
            # Send email notifications
            try:
                # Send email to admin
                admin_subject = f"Contact Form: {subject} - {name}"
                admin_message = render_to_string('emails/contact_admin_notification.html', email_context)
                admin_email = EmailMessage(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL, settings.ADMIN_EMAIL],  # Send to both contact and admin emails
                )
                admin_email.content_subtype = "html"
                admin_email.send()
                
                # Send confirmation email to user
                user_subject = "Thank You for Contacting IHICL Investment"
                user_message = render_to_string('emails/contact_user_confirmation.html', email_context)
                user_email = EmailMessage(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                user_email.content_subtype = "html"
                user_email.send()
                
                messages.success(request, 'Your message has been sent successfully! A confirmation email has been sent to your inbox.')
                
            except Exception as e:
                # Log the error but still show success to user
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send contact emails: {str(e)}")
                messages.success(request, 'Your message has been received! We will get back to you soon.')
            
            return redirect('contact')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'ihicl_main/contact.html', {'form': form})



def search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = InvestmentOpportunity.objects.filter(
            title__icontains=query
        ) | InvestmentOpportunity.objects.filter(
            description__icontains=query
        )
    return render(request, 'ihicl_main/search_results.html', {
        'results': results,
        'query': query
    })



def investment_login(request):
    """
    Handle investor login with custom template
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Login successful!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    
    return render(request, 'ihicl_main/investment_login.html', {'form': form})



def investment_register(request):
    """
    Handle new investor registration with all form fields including investment amount
    """
    # Fetch countries data from REST Countries API
    try:
        response = requests.get('https://restcountries.com/v3.1/all?fields=name,cca2,idd')
        countries_data = response.json()
        
        countries = []
        for country in countries_data:
            name = country.get('name', {}).get('common', '')
            code = country.get('cca2', '')
            idd = country.get('idd', {})
            root = idd.get('root', '')
            suffixes = idd.get('suffixes', [''])
            phone_code = root + (suffixes[0] if suffixes else '')
            
            # Only include countries with valid phone codes
            if phone_code:
                countries.append({
                    'name': name,
                    'code': code,
                    'phone_code': phone_code
                })
        
        # Sort countries alphabetically
        countries.sort(key=lambda x: x['name'])
    except Exception as e:
        # Fallback to some common countries if API fails
        print(f"Error fetching countries: {e}")
        countries = [
            {'name': 'Nigeria', 'code': 'NG', 'phone_code': '+234'},
            {'name': 'United States', 'code': 'US', 'phone_code': '+1'},
            {'name': 'United Kingdom', 'code': 'GB', 'phone_code': '+44'},
            {'name': 'Ghana', 'code': 'GH', 'phone_code': '+233'},
            {'name': 'South Africa', 'code': 'ZA', 'phone_code': '+27'},
            {'name': 'Kenya', 'code': 'KE', 'phone_code': '+254'},
            {'name': 'Canada', 'code': 'CA', 'phone_code': '+1'},
            {'name': 'Australia', 'code': 'AU', 'phone_code': '+61'},
            {'name': 'Germany', 'code': 'DE', 'phone_code': '+49'},
            {'name': 'France', 'code': 'FR', 'phone_code': '+33'},
        ]
    
    if request.method == 'POST':
        # Use the form with reCAPTCHA
        form = InvestmentRegistrationForm(request.POST)
        
        if form.is_valid():
            # Extract cleaned data from the form
            title = form.cleaned_data['title']
            other_title = form.cleaned_data['other_title']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            telephone = form.cleaned_data['telephone']
            address = form.cleaned_data['address']
            country = form.cleaned_data['country']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            postal_code = form.cleaned_data['postal_code']
            investment_amount = form.cleaned_data['investment_amount']
            password = form.cleaned_data['password1']
            terms = form.cleaned_data['terms']
            newsletter = form.cleaned_data['newsletter']
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'ihicl_main/investment_register.html', {
                    'countries': countries,
                    'form': form
                })
            
            # Create new user
            try:
                user = User.objects.create_user(
                    username=email, 
                    email=email, 
                    password=password, 
                    first_name=first_name, 
                    last_name=last_name
                )
                user.save()
                
                # Create investor profile with additional information
                investor_profile = InvestorProfile(
                    user=user,
                    title=title,
                    other_title=other_title if title == 'Other' else '',
                    telephone=telephone,
                    address=address,
                    country=country,
                    city=city,
                    state=state,
                    postal_code=postal_code
                )
                # Set newsletter subscription after creating the object
                investor_profile.newsletter_subscription = True if newsletter else False
                investor_profile.save()
                
                # Create investment record
                investment = Investment.objects.create(
                    investor=user,
                    amount=investment_amount,
                    date_invested=timezone.now(),
                    status='pending',  # Set to pending until admin approves
                    current_value=investment_amount  # Initial value same as amount
                )
                
                # Send email notifications
                try:
                    # Prepare context for email templates
                    email_context = {
                        'user': user,
                        'investor_profile': investor_profile,
                        'amount': investment_amount,
                    }
                    
                    # Send email to admin
                    admin_subject = f"New Investment Registration - {user.get_full_name()}"
                    admin_message = render_to_string('emails/investment_admin_notification.html', email_context)
                    admin_email = EmailMessage(
                        admin_subject,
                        admin_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_EMAIL],
                    )
                    admin_email.content_subtype = "html"
                    admin_email.send()
                    
                    # Send email to user
                    user_subject = "Investment Registration Received - IHICL"
                    user_message = render_to_string('emails/investment_user_confirmation.html', email_context)
                    user_email = EmailMessage(
                        user_subject,
                        user_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                    )
                    user_email.content_subtype = "html"
                    user_email.send()
                    
                except Exception as e:
                    # Log email error but don't prevent registration
                    print(f"Email sending error: {e}")
                
                # Log the user in
                from django.contrib.auth import login
                backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user, backend=backend)
                
                messages.success(request, f'Account created successfully! Your investment of ₦{investment_amount:,.2f} has been received and is pending approval.')
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return render(request, 'ihicl_main/investment_register.html', {
                    'countries': countries,
                    'form': form
                })
        else:
            # Form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            return render(request, 'ihicl_main/investment_register.html', {
                'countries': countries,
                'form': form
            })
    
    # GET request - show empty form with countries data
    form = InvestmentRegistrationForm()
    return render(request, 'ihicl_main/investment_register.html', {
        'countries': countries,
        'form': form
    })

from django.db.models import Sum, Count
from decimal import Decimal
import json
from datetime import datetime, timedelta


# views.py - Update dashboard view
# views.py - Update dashboard view to filter by status
@login_required
def dashboard(request):
    """
    Render the investor dashboard with real investment data
    Only include investments with status 'active' or 'completed' in calculations
    """
    try:
        investor_profile = request.user.investor_profile
    except InvestorProfile.DoesNotExist:
        investor_profile = None
    
    # Get investor's portfolio data - ONLY ACTIVE/COMPLETED INVESTMENTS
    investor_portfolio = Investment.objects.filter(
        investor=request.user, 
        status__in=['active', 'completed']  # Only include these statuses
    )
    
    # Calculate totals - handle None values (ONLY ACTIVE/COMPLETED)
    total_investment = investor_portfolio.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    investment_count = investor_portfolio.count()
    
    # Calculate current value and ROI - handle None values (ONLY ACTIVE/COMPLETED)
    current_value_sum = investor_portfolio.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
    roi_amount = current_value_sum - total_investment
    roi_percentage = (roi_amount / total_investment * 100) if total_investment > 0 else Decimal('0.00')
    
    # Get pending returns (sum of expected returns from active investments)
    pending_returns = Decimal('0.00')
    active_investments = investor_portfolio.filter(status='active')
    for investment in active_investments:
        if (investment.current_value is not None and 
            investment.amount is not None and
            isinstance(investment.current_value, (Decimal, int, float)) and
            isinstance(investment.amount, (Decimal, int, float))):
            pending_returns += Decimal(str(investment.current_value)) - Decimal(str(investment.amount))
    
    # Get all investments (including pending) for display purposes
    all_investments = Investment.objects.filter(investor=request.user)
    
    # Get recent transactions - FIXED: Use distinct to avoid duplicates
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-date').distinct()[:5]
    
    # Generate performance data for chart (using only active/completed)
    performance_data = generate_performance_data(request.user)
    
    # Get next of kin information
    try:
        next_of_kin = request.user.investor_profile.next_of_kin
    except (InvestorProfile.DoesNotExist, NextOfKin.DoesNotExist):
        next_of_kin = None
    
    context = {
        'user': request.user,
        'investor_profile': investor_profile,
        'total_investment': total_investment,
        'investment_count': investment_count,
        'current_value': current_value_sum,
        'roi_percentage': roi_percentage,
        'pending_returns': pending_returns,
        'next_payout_date': None,  # This will make it show "TBD",
        'investor_portfolio': all_investments,  # Show all investments in portfolio table
        'active_portfolio': investor_portfolio,  # For calculations
        'recent_transactions': recent_transactions,
        'performance_data': performance_data,
        'performance_labels': json.dumps(performance_data['labels']),
        'performance_values': json.dumps([float(v) for v in performance_data['values']]),
        'next_of_kin': next_of_kin,
    }
    
    return render(request, 'ihicl_main/dashboard.html', context)

@login_required
def cleanup_duplicates(request):
    """
    Temporary view to clean up duplicate transactions
    """
    # Get all transactions for the user
    transactions = Transaction.objects.filter(user=request.user)
    
    # Find duplicates by reference
    from collections import Counter
    references = list(transactions.values_list('reference', flat=True))
    duplicate_refs = [ref for ref, count in Counter(references).items() if count > 1]
    
    cleaned_count = 0
    for ref in duplicate_refs:
        duplicates = Transaction.objects.filter(reference=ref).order_by('-date')
        if duplicates.count() > 1:
            # Keep the first (most recent) and delete the rest
            for duplicate in duplicates[1:]:
                duplicate.delete()
                cleaned_count += 1
    
    messages.success(request, f'Cleaned up {cleaned_count} duplicate transactions.')
    return redirect('dashboard')


 # You may need to install: pip install python-dateutil
def generate_performance_data(user):
    """
    Generate performance data based on user's ACTIVE/COMPLETED investment history
    """
    try:
        # Get only active/completed investments ordered by date
        investments = Investment.objects.filter(
            investor=user, 
            status__in=['active', 'completed']
        ).order_by('date_invested')
        
        if not investments.exists():
            # Return empty data if no investments
            return {'labels': [], 'values': []}
        
        # Create monthly performance data
        labels = []
        values = []
        
        # Start from the first investment
        first_investment_date = investments.first().date_invested.date()  # Convert to date
        current_date = first_investment_date
        cumulative_value = Decimal('0.00')
        
        # Get current date
        today = timezone.now().date()
        
        # Ensure we don't create an infinite loop
        max_months = 60  # 5 years maximum
        
        for month in range(max_months):
            if current_date > today:
                break
                
            # Calculate value for this month
            month_investments = investments.filter(
                date_invested__year=current_date.year, 
                date_invested__month=current_date.month
            )
            
            for investment in month_investments:
                cumulative_value += investment.amount
            
            # Add some growth (simplified - in real app, this would come from actual returns)
            if cumulative_value > 0:
                cumulative_value *= Decimal('1.05')  # 5% monthly growth for demo
            
            labels.append(current_date.strftime('%b %Y'))
            values.append(float(cumulative_value))
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            
            # Ensure day is valid (e.g., not 31 in months with 30 days)
            try:
                current_date = current_date.replace(day=1)
            except ValueError:
                # If day is invalid, set to last day of previous month
                if current_date.month == 1:
                    current_date = current_date.replace(year=current_date.year-1, month=12, day=31)
                else:
                    current_date = current_date.replace(month=current_date.month-1, day=1)
        
        return {
            'labels': labels[-12:],  # Last 12 months
            'values': values[-12:],
        }
        
    except Exception as e:
        # Log the error and return empty data
        print(f"Error generating performance data: {e}")
        return {'labels': [], 'values': []}


# In your views.py - Update the EmailBackend class
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
    
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None    

# Add this to your views.py for debugging
def debug_password_reset(request):
    """Debug view to check password reset issues"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        from django.contrib.auth import authenticate
        user = authenticate(request, username=email, password=password)
        
        if user:
            return render(request, 'debug.html', {
                'success': True,
                'message': f'Authentication successful for {email}'
            })
        else:
            # Check if user exists
            from django.contrib.auth.models import User
            try:
                user_obj = User.objects.get(email=email)
                return render(request, 'debug.html', {
                    'success': False,
                    'message': f'User exists but authentication failed. Password correct: {user_obj.check_password(password)}'
                })
            except User.DoesNotExist:
                return render(request, 'debug.html', {
                    'success': False,
                    'message': f'User with email {email} does not exist'
                })
    
    return render(request, 'debug.html')



def map_view(request):
    return render(request, 'ihicl_main/map.html')




@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # We need to pass all the dashboard context here too
    investor_profile = request.user.investor_profile
    investor_portfolio = Investment.objects.filter(investor=request.user)
    total_investment = investor_portfolio.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    investment_count = investor_portfolio.count()
    current_value_sum = investor_portfolio.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
    roi_percentage = ((current_value_sum - total_investment) / total_investment * 100) if total_investment > 0 else Decimal('0.00')
    
    # Fixed pending_returns calculation
    pending_returns = Decimal('0.00')
    for investment in investor_portfolio.filter(status='active', current_value__isnull=False, amount__isnull=False):
        pending_returns += (investment.current_value - investment.amount)
    
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
    performance_data = generate_performance_data(request.user)
    
    context = {
        'user': request.user,
        'investor_profile': investor_profile,
        'total_investment': total_investment,
        'investment_count': investment_count,
        'current_value': current_value_sum,
        'roi_percentage': roi_percentage,
        'pending_returns': pending_returns,
        'next_payout_date': (datetime.now() + timedelta(days=15)).strftime('%d %b %Y'),
        'investor_portfolio': investor_portfolio,
        'recent_transactions': recent_transactions,
        'performance_data': performance_data,
        'performance_labels': json.dumps(performance_data['labels']),
        'performance_values': json.dumps([float(v) for v in performance_data['values']]),
        'form': form,
    }
    
    return render(request, 'ihicl_main/dashboard.html', context)


@login_required
def update_next_of_kin(request):
    if request.method == 'POST':
        # Get or create NextOfKin for the current user
        next_of_kin, created = NextOfKin.objects.get_or_create(investor=request.user.investor_profile)
        
        # Update fields from form data
        next_of_kin.full_name = request.POST.get('kin_full_name')
        next_of_kin.relationship = request.POST.get('kin_relationship')
        next_of_kin.email = request.POST.get('kin_email')
        next_of_kin.phone = request.POST.get('kin_phone')
        next_of_kin.address = request.POST.get('kin_address')
        
        try:
            next_of_kin.save()
            messages.success(request, 'Next of kin information updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating next of kin: {str(e)}')
        
        return redirect('dashboard')
    
    return redirect('dashboard')



@staff_member_required
def admin_dashboard(request):
    # Get statistics for the admin dashboard
    total_investors = InvestorProfile.objects.count()
    total_investments = Investment.objects.count()
    total_investment_amount = Investment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = Transaction.objects.count()
    
    # Recent investments
    recent_investments = Investment.objects.select_related('investor', 'project').order_by('-date_invested')[:10]
    
    # New investors (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_investors = InvestorProfile.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Investment statistics by status
    investment_stats = Investment.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'total_investors': total_investors,
        'total_investments': total_investments,
        'total_investment_amount': total_investment_amount,
        'total_transactions': total_transactions,
        'new_investors': new_investors,
        'recent_investments': recent_investments,
        'investment_stats': investment_stats,
    }
    
    return render(request, 'admin/ihicl_dashboard.html', context)


# views.py
@login_required
def invest_form(request):
    investor_profile = request.user.investor_profile
    
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Save investment to database (optional, add if needed)
            investment = Investment.objects.create(
                investor=request.user,
                amount=amount,
                date_invested=timezone.now(),
                status='pending'  # Adjust based on your model
            )
            
            # Prepare context for email templates
            email_context = {
                'user': request.user,
                'investor_profile': investor_profile,
                'amount': amount,  # Pass raw Decimal amount
            }
            
            # Send email to admin
            try:
                admin_subject = f"New Investment Request - {request.user.get_full_name()}"
                admin_message = render_to_string('emails/investment_admin_notification.html', email_context)
                admin_email = EmailMessage(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    )
                admin_email.content_subtype = "html"
                admin_email.send()
            except Exception as e:
                messages.error(request, f'Error sending admin notification: {str(e)}')
            
            # Send email to user
            try:
                user_subject = "Investment Request Received - IHICL"
                user_message = render_to_string('emails/investment_user_confirmation.html', email_context)
                user_email = EmailMessage(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    )
                user_email.content_subtype = "html"
                user_email.send()
            except Exception as e:
                messages.error(request, f'Error sending user confirmation: {str(e)}')
            
            # Format amount for success message
            formatted_amount = f"{amount:,.2f}"
            messages.success(request, f'Your investment request of ₦{formatted_amount} has been received. We will contact you shortly.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InvestmentForm()
    
    return render(request, 'ihicl_main/invest_form.html', {
        'form': form,
        'investor_profile': investor_profile
    })


# Add this to views.py at the end

# views.py
  # Add this import at the top

from django.utils import timezone
from datetime import timedelta

@login_required
def withdraw_form(request):
    investor_profile = request.user.investor_profile
    
    current_value_sum = Investment.objects.filter(
        investor=request.user,
        status__in=['active', 'completed']
    ).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
    
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Check for recent similar pending withdrawal (within 5 minutes)
            if Transaction.objects.filter(
                user=request.user,
                transaction_type='withdrawal',
                amount=amount,
                status='pending',
                date__gte=timezone.now() - timedelta(minutes=5)
            ).exists():
                messages.error(request, 'A similar withdrawal request is already pending. Please wait before submitting again.')
                return redirect('dashboard')
            
            # Check sufficient balance
            if amount > current_value_sum:
                messages.error(request, 'Insufficient balance for withdrawal.')
                return render(request, 'ihicl_main/withdraw_form.html', {
                    'form': form,
                    'investor_profile': investor_profile,
                    'available_balance': current_value_sum
                })
            
            # Generate unique transaction reference
            unique_reference = f'WD-{timezone.now().strftime("%Y%m%d%H%M%S")}-{uuid.uuid4().hex[:8]}'
            
            # Create transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                amount=amount,
                date=timezone.now(),
                description='Withdrawal Request',
                reference=unique_reference,
                status='pending'
            )
            
            # Email sending and messages (unchanged from your code)
            email_context = {
                'user': request.user,
                'investor_profile': investor_profile,
                'amount': amount,
                'transaction': transaction,
            }
            try:
                admin_subject = f"New Withdrawal Request - {request.user.get_full_name()}"
                admin_message = render_to_string('emails/withdrawal_admin_notification.html', email_context)
                admin_email = EmailMessage(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                )
                admin_email.content_subtype = "html"
                admin_email.send()
            except Exception as e:
                print(f"Error sending admin notification: {str(e)}")
            
            try:
                user_subject = "Withdrawal Request Received - IHICL"
                user_message = render_to_string('emails/withdrawal_user_confirmation.html', email_context)
                user_email = EmailMessage(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                )
                user_email.content_subtype = "html"
                user_email.send()
            except Exception as e:
                print(f"Error sending user confirmation: {str(e)}")
            
            formatted_amount = f"{amount:,.2f}"
            messages.success(request, f'Your withdrawal request of ₦{formatted_amount} has been received and is pending approval.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WithdrawForm()
    
    return render(request, 'ihicl_main/withdraw_form.html', {
        'form': form,
        'investor_profile': investor_profile,
        'available_balance': current_value_sum
    })



@login_required
def statement_request(request):
    """
    Handle statement requests from investors
    """
    if request.method == 'POST':
        form = StatementRequestForm(request.POST)
        if form.is_valid():
            period_start = form.cleaned_data['period_start']
            period_end = form.cleaned_data['period_end']
            notes = form.cleaned_data['notes']
            
            # Create statement request record
            statement_request = StatementRequest.objects.create(
                user=request.user,
                period_start=period_start,
                period_end=period_end,
                notes=notes,
                status='pending'
            )
            
            # Prepare context for email templates
            email_context = {
                'user': request.user,
                'investor_profile': request.user.investor_profile,
                'statement_request': statement_request,
                'period_start': period_start,
                'period_end': period_end,
                'notes': notes,
            }
            
            # Send email notifications
            try:
                # Send email to admin
                admin_subject = f"New Statement Request - {request.user.get_full_name()}"
                admin_message = render_to_string('emails/statement_admin_notification.html', email_context)
                admin_email = EmailMessage(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                )
                admin_email.content_subtype = "html"
                admin_email.send()
                
                # Send confirmation email to user
                user_subject = "Statement Request Received - IHICL"
                user_message = render_to_string('emails/statement_user_confirmation.html', email_context)
                user_email = EmailMessage(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                )
                user_email.content_subtype = "html"
                user_email.send()
                
                messages.success(request, f'Your statement request has been received (Reference: {statement_request.reference}). We will process it within 24 hours.')
                
            except Exception as e:
                # Log email error but still show success to user
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send statement request emails: {str(e)}")
                messages.success(request, f'Your statement request has been received (Reference: {statement_request.reference}).')
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Default to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        form = StatementRequestForm(initial={
            'period_start': first_day,
            'period_end': last_day,
        })
    
    return render(request, 'ihicl_main/statement_request.html', {
        'form': form,
        'investor_profile': request.user.investor_profile
    })