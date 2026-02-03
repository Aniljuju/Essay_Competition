from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extended user profile with verification status
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Competition(models.Model):
    """
    Essay writing competition
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_paragraphs = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def is_active(self):
        """Check if competition is currently active"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def has_started(self):
        """Check if competition has started"""
        return timezone.now() >= self.start_date
    
    def has_ended(self):
        """Check if competition has ended"""
        return timezone.now() > self.end_date
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Competition'
        verbose_name_plural = 'Competitions'


class Essay(models.Model):
    """
    Essay submitted by user for a competition
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='essays')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='essays')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    word_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.competition.title}"
    
    def current_paragraph_count(self):
        """Get current number of paragraphs"""
        return self.paragraphs.count()
    
    def can_add_paragraph(self):
        """Check if user can add more paragraphs"""
        return (
            self.status == 'in_progress' and
            self.current_paragraph_count() < self.competition.max_paragraphs
        )
    
    def calculate_word_count(self):
        """Calculate total word count from all paragraphs"""
        total = 0
        for paragraph in self.paragraphs.all():
            total += len(paragraph.content.split())
        return total
    
    def complete_essay(self):
        """Mark essay as completed"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.word_count = self.calculate_word_count()
            self.save()
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['user', 'competition']
        verbose_name = 'Essay'
        verbose_name_plural = 'Essays'


class Paragraph(models.Model):
    """
    Individual paragraph in an essay
    """
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='paragraphs')
    order = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Paragraph {self.order} of {self.essay}"
    
    class Meta:
        ordering = ['order']
        unique_together = ['essay', 'order']
        verbose_name = 'Paragraph'
        verbose_name_plural = 'Paragraphs'