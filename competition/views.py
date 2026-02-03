from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, F
from django.contrib.auth.models import User
from .models import Competition, Essay, Paragraph, UserProfile
from .forms import ParagraphForm, CompetitionForm, UserStatusForm
from .decorators import verified_user_required, admin_required


def home(request):
    """
    Public landing page
    """
    return render(request, 'home.html')


def login_view(request):
    """
    User login view
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def logout_view(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    """
    User dashboard showing status and competitions
    """
    user_profile = getattr(request.user, 'profile', None)
    
    # Get user's essays
    user_essays = Essay.objects.filter(user=request.user).select_related('competition')
    
    # Get active competitions if verified
    active_competitions = []
    if user_profile and user_profile.status == 'verified':
        active_competitions = Competition.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
    
    context = {
        'user_profile': user_profile,
        'user_essays': user_essays,
        'active_competitions': active_competitions,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
@verified_user_required
def competition_list(request):
    """
    List all competitions for verified users
    """
    competitions = Competition.objects.all()
    
    # Get user's essays for each competition
    user_essays = {essay.competition_id: essay for essay in Essay.objects.filter(user=request.user)}
    
    context = {
        'competitions': competitions,
        'user_essays': user_essays,
    }
    
    return render(request, 'competition_list.html', context)


@login_required
@verified_user_required
def essay_write(request, competition_id):
    """
    Write essay paragraph by paragraph
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Check if competition is active
    if not competition.is_active():
        messages.error(request, 'This competition is not currently active.')
        return redirect('competition_list')
    
    # Get or create essay
    essay, created = Essay.objects.get_or_create(
        user=request.user,
        competition=competition
    )
    
    # Check if essay is locked or completed
    if essay.status in ['completed', 'locked']:
        messages.info(request, 'This essay is already completed and locked.')
        return redirect('essay_view', essay_id=essay.id)
    
    # Check if max paragraphs reached
    current_count = essay.current_paragraph_count()
    if current_count >= competition.max_paragraphs:
        # Auto-complete essay
        essay.complete_essay()
        messages.success(request, 'Your essay has been completed and submitted!')
        return redirect('essay_view', essay_id=essay.id)
    
    if request.method == 'POST':
        form = ParagraphForm(request.POST)
        if form.is_valid():
            # Double-check paragraph limit
            if not essay.can_add_paragraph():
                messages.error(request, 'You have reached the maximum number of paragraphs.')
                return redirect('essay_view', essay_id=essay.id)
            
            # Create paragraph
            paragraph = form.save(commit=False)
            paragraph.essay = essay
            paragraph.order = current_count + 1
            paragraph.save()
            
            # Check if this was the last paragraph
            if paragraph.order >= competition.max_paragraphs:
                essay.complete_essay()
                messages.success(request, 'Congratulations! Your essay has been completed and submitted!')
                return redirect('essay_view', essay_id=essay.id)
            else:
                messages.success(request, f'Paragraph {paragraph.order} saved successfully!')
                return redirect('essay_write', competition_id=competition.id)
    else:
        form = ParagraphForm()
    
    # Get existing paragraphs
    paragraphs = essay.paragraphs.all().order_by('order')
    
    context = {
        'competition': competition,
        'essay': essay,
        'paragraphs': paragraphs,
        'form': form,
        'current_count': current_count,
        'remaining': competition.max_paragraphs - current_count,
    }
    
    return render(request, 'essay_write.html', context)


@login_required
def essay_view(request, essay_id):
    """
    View completed essay (read-only)
    """
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Check permission: user must own the essay or be admin
    if essay.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this essay.')
        return redirect('dashboard')
    
    paragraphs = essay.paragraphs.all().order_by('order')
    
    context = {
        'essay': essay,
        'paragraphs': paragraphs,
    }
    
    return render(request, 'essay_view.html', context)


@login_required
def leaderboard(request, competition_id):
    """
    Show leaderboard for a competition (only after competition ends)
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Check if competition has ended
    if not competition.has_ended():
        messages.error(request, 'Leaderboard will be available after the competition ends.')
        return redirect('competition_list')
    
    # Get completed essays, sorted by completion time (asc) then word count (desc)
    essays = Essay.objects.filter(
        competition=competition,
        status__in=['completed', 'locked']
    ).select_related('user').order_by('completed_at', '-word_count')
    
    context = {
        'competition': competition,
        'essays': essays,
    }
    
    return render(request, 'leaderboard.html', context)


@login_required
@admin_required
def admin_dashboard(request):
    """
    Admin dashboard with statistics
    """
    total_users = User.objects.count()
    pending_users = UserProfile.objects.filter(status='pending').count()
    verified_users = UserProfile.objects.filter(status='verified').count()
    rejected_users = UserProfile.objects.filter(status='rejected').count()
    
    total_competitions = Competition.objects.count()
    active_competitions = Competition.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()
    
    total_essays = Essay.objects.count()
    completed_essays = Essay.objects.filter(status__in=['completed', 'locked']).count()
    
    context = {
        'total_users': total_users,
        'pending_users': pending_users,
        'verified_users': verified_users,
        'rejected_users': rejected_users,
        'total_competitions': total_competitions,
        'active_competitions': active_competitions,
        'total_essays': total_essays,
        'completed_essays': completed_essays,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required
@admin_required
def admin_users(request):
    """
    Admin user management page
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('status')
        
        if user_id and new_status:
            try:
                user = User.objects.get(id=user_id)
                profile = user.profile
                profile.status = new_status
                profile.save()
                messages.success(request, f'User {user.username} status updated to {new_status}.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
        
        return redirect('admin_users')
    
    # Get all users with profiles
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin_users.html', context)


@login_required
@admin_required
def admin_essays(request):
    """
    Admin essay management page
    """
    if request.method == 'POST':
        essay_id = request.POST.get('essay_id')
        action = request.POST.get('action')
        
        if essay_id and action:
            try:
                essay = Essay.objects.get(id=essay_id)
                
                if action == 'lock':
                    essay.status = 'locked'
                    essay.save()
                    messages.success(request, f'Essay #{essay.id} has been locked.')
                elif action == 'unlock':
                    if essay.status == 'locked':
                        essay.status = 'completed'
                        essay.save()
                        messages.success(request, f'Essay #{essay.id} has been unlocked.')
                    else:
                        messages.error(request, 'Only locked essays can be unlocked.')
                
            except Essay.DoesNotExist:
                messages.error(request, 'Essay not found.')
            except Exception as e:
                messages.error(request, f'Error updating essay: {str(e)}')
        
        return redirect('admin_essays')
    
    # Get all essays with related data
    essays = Essay.objects.select_related('user', 'competition').all().order_by('-started_at')
    
    context = {
        'essays': essays,
    }
    
    return render(request, 'admin_essays.html', context)