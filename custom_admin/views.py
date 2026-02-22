"""
custom_admin/views.py
Uses: competition.models (UserProfile related_name='profile',
      Essay related_name='paragraphs', Essay.started_at, Essay.completed_at)
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from competition.models import Competition, Essay, Paragraph, UserProfile
from competition.forms import CompetitionForm

from .decorators import admin_required


# ─────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def dashboard(request):
    now = timezone.now()

    # Stat counts
    total_users    = User.objects.count()
    pending_users  = UserProfile.objects.filter(status='pending').count()
    verified_users = UserProfile.objects.filter(status='verified').count()
    rejected_users = UserProfile.objects.filter(status='rejected').count()

    total_competitions   = Competition.objects.count()
    active_competitions  = Competition.objects.filter(
        start_date__lte=now, end_date__gte=now
    ).count()
    overdue_competitions = Competition.objects.filter(end_date__lt=now)

    total_essays       = Essay.objects.count()
    completed_essays   = Essay.objects.filter(status__in=['completed', 'locked']).count()
    in_progress_essays = Essay.objects.filter(status='in_progress').count()
    locked_essays      = Essay.objects.filter(status='locked').count()
    pure_completed     = Essay.objects.filter(status='completed').count()

    # Chart data — user status bar chart
    user_chart_data = json.dumps({
        'labels': ['Pending', 'Verified', 'Rejected'],
        'values': [pending_users, verified_users, rejected_users],
    })

    # Chart data — essay status doughnut
    essay_chart_data = json.dumps({
        'labels': ['In Progress', 'Completed', 'Locked'],
        'values': [in_progress_essays, pure_completed, locked_essays],
    })

    # Chart data — competitions per month (last 12 months)
    # Uses Competition.created_at which exists on your model
    comp_months = []
    comp_counts = []
    for i in range(11, -1, -1):
        # Build month boundaries without dateutil dependency
        month = (now.month - i - 1) % 12 + 1
        year  = now.year + ((now.month - i - 1) // 12)
        from django.utils.timezone import datetime
        import calendar
        month_start = now.replace(year=year, month=month, day=1,
                                  hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(year, month)[1]
        month_end = month_start.replace(day=last_day, hour=23, minute=59, second=59)
        count = Competition.objects.filter(
            created_at__gte=month_start, created_at__lte=month_end
        ).count()
        comp_months.append(month_start.strftime('%b %Y'))
        comp_counts.append(count)

    comp_chart_data = json.dumps({'labels': comp_months, 'values': comp_counts})

    # Top 5 users by completed essays
    top_users = (
        User.objects.annotate(
            completed_count=Count(
                'essays',
                filter=Q(essays__status__in=['completed', 'locked'])
            )
        )
        .filter(completed_count__gt=0)
        .order_by('-completed_count')[:5]
    )

    # 5 most recent essays
    recent_essays = (
        Essay.objects
        .select_related('user', 'competition')
        .order_by('-started_at')[:5]
    )

    context = {
        'total_users':          total_users,
        'pending_users':        pending_users,
        'verified_users':       verified_users,
        'rejected_users':       rejected_users,
        'total_competitions':   total_competitions,
        'active_competitions':  active_competitions,
        'total_essays':         total_essays,
        'completed_essays':     completed_essays,
        'user_chart_data':      user_chart_data,
        'essay_chart_data':     essay_chart_data,
        'comp_chart_data':      comp_chart_data,
        'overdue_competitions': overdue_competitions,
        'top_users':            top_users,
        'recent_essays':        recent_essays,
    }
    return render(request, 'custom_admin/dashboard.html', context)


# ─────────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def users(request):
    qs = User.objects.select_related('profile').order_by('-date_joined')

    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
    if status in ('pending', 'verified', 'rejected'):
        qs = qs.filter(profile__status=status)

    paginator  = Paginator(qs, 20)
    users_page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'custom_admin/users.html', {
        'users':         users_page,
        'search_query':  q,
        'status_filter': status,
        'total_count':   paginator.count,
    })


@login_required
@admin_required
@require_POST
def update_user_status(request):
    """AJAX — update user profile status."""
    user_id    = request.POST.get('user_id')
    new_status = request.POST.get('status')

    if new_status not in ('pending', 'verified', 'rejected'):
        return JsonResponse({'ok': False, 'error': 'Invalid status.'}, status=400)

    user = get_object_or_404(User, pk=user_id)
    # related_name='profile' on UserProfile
    user.profile.status = new_status
    user.profile.save()

    return JsonResponse({'ok': True, 'status': new_status, 'username': user.username})


@login_required
@admin_required
@require_POST
def delete_user(request):
    """AJAX — permanently delete a user."""
    user = get_object_or_404(User, pk=request.POST.get('user_id'))
    username = user.username
    user.delete()
    return JsonResponse({'ok': True, 'username': username})


# ─────────────────────────────────────────────────────────────────
# ESSAY MANAGEMENT
# ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def essays(request):
    qs = (
        Essay.objects
        .select_related('user', 'competition')
        .prefetch_related('paragraphs')   # related_name='paragraphs'
        .order_by('-started_at')          # Essay.started_at field
    )

    q           = request.GET.get('q', '').strip()
    status      = request.GET.get('status', '').strip()
    comp_filter = request.GET.get('competition', '').strip()

    if q:
        qs = qs.filter(user__username__icontains=q)
    if status in ('in_progress', 'completed', 'locked'):
        qs = qs.filter(status=status)
    if comp_filter.isdigit():
        qs = qs.filter(competition__pk=int(comp_filter))

    paginator   = Paginator(qs, 20)
    essays_page = paginator.get_page(request.GET.get('page', 1))

    competitions = Competition.objects.order_by('title')

    summary = {
        'in_progress': Essay.objects.filter(status='in_progress').count(),
        'completed':   Essay.objects.filter(status='completed').count(),
        'locked':      Essay.objects.filter(status='locked').count(),
    }

    return render(request, 'custom_admin/essays.html', {
        'essays':        essays_page,
        'competitions':  competitions,
        'search_query':  q,
        'status_filter': status,
        'comp_filter':   comp_filter,
        'total_count':   paginator.count,
        'summary':       summary,
    })


@login_required
@admin_required
@require_POST
def essay_action(request):
    """AJAX — lock or unlock an essay."""
    essay_id = request.POST.get('essay_id')
    action   = request.POST.get('action')

    if action not in ('lock', 'unlock'):
        return JsonResponse({'ok': False, 'error': 'Invalid action.'}, status=400)

    essay = get_object_or_404(Essay, pk=essay_id)

    if action == 'lock':
        essay.status = 'locked'
        essay.save()
    else:  # unlock
        if essay.status != 'locked':
            return JsonResponse({'ok': False, 'error': 'Essay is not locked.'}, status=400)
        # Restore to completed if finished, otherwise in_progress
        essay.status = 'completed' if essay.completed_at else 'in_progress'
        essay.save()

    return JsonResponse({'ok': True, 'new_status': essay.status, 'essay_id': essay.pk})


@login_required
@admin_required
def essay_detail(request, essay_id):
    """AJAX GET — return essay data as JSON for the modal."""
    essay = get_object_or_404(
        Essay.objects
        .select_related('user', 'competition')
        .prefetch_related('paragraphs'),
        pk=essay_id,
    )
    # paragraphs uses related_name='paragraphs'
    paragraphs = [
        {'order': p.order, 'content': p.content}
        for p in essay.paragraphs.order_by('order')
    ]
    return JsonResponse({
        'id':              essay.pk,
        'username':        essay.user.username,
        'competition':     essay.competition.title,
        'status':          essay.status,
        'word_count':      essay.word_count,
        'grammar_score':   essay.grammar_score,
        'grammar_errors':  essay.grammar_errors,
        'spelling_errors': essay.spelling_errors,
        'final_score':     essay.final_score,
        'started_at':      essay.started_at.strftime('%b %d, %Y %H:%M') if essay.started_at else None,
        'completed_at':    essay.completed_at.strftime('%b %d, %Y %H:%M') if essay.completed_at else None,
        'paragraphs':      paragraphs,
    })


# ─────────────────────────────────────────────────────────────────
# CREATE COMPETITION
# ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def create_competition(request):
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Competition created successfully.')
            return redirect('custom_admin:dashboard')
    else:
        form = CompetitionForm()
    return render(request, 'custom_admin/create_competition.html', {'form': form})
