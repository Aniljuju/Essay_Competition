from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import language_tool_python

# load grammar tool once (performance optimization)
tool = language_tool_python.LanguageTool('en-US')


class UserProfile(models.Model):
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
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def has_started(self):
        return timezone.now() >= self.start_date
    
    def has_ended(self):
        return timezone.now() > self.end_date
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Competition'
        verbose_name_plural = 'Competitions'


class Essay(models.Model):
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

    grammar_errors = models.PositiveIntegerField(default=0)
    spelling_errors = models.PositiveIntegerField(default=0)
    grammar_score = models.PositiveIntegerField(default=100)
    final_score = models.FloatField(default=0)   # ⭐ NEW FIELD

    def __str__(self):
        return f"{self.user.username} - {self.competition.title}"

    def current_paragraph_count(self):
        return self.paragraphs.count()
    
    def can_add_paragraph(self):
        return (
            self.status == 'in_progress' and
            self.current_paragraph_count() < self.competition.max_paragraphs
        )

    def calculate_word_count(self):
        total = 0
        for paragraph in self.paragraphs.all():
            total += len(paragraph.content.split())
        return total

    # ===============================
    # GRAMMAR + SPELL CHECK
    # ===============================
    def analyze_grammar(self):
        try:
            full_text = " ".join(
                p.content for p in self.paragraphs.all().order_by('order')
            )

            matches = tool.check(full_text)

            grammar_errors = 0
            spelling_errors = 0

            for match in matches:
                if match.rule_issue_type == 'misspelling':
                    spelling_errors += 1
                else:
                    grammar_errors += 1

            total_errors = grammar_errors + spelling_errors
            score = max(0, 100 - (total_errors * 2))

            self.grammar_errors = grammar_errors
            self.spelling_errors = spelling_errors
            self.grammar_score = score

        except Exception:
            # if grammar tool fails, don't crash submission
            self.grammar_errors = 0
            self.spelling_errors = 0
            self.grammar_score = 100

    # ===============================
    # FINAL JUDGE SCORE
    # ===============================
    def calculate_final_score(self, fastest_time, max_words):
        if not self.completed_at:
            return

        user_time = (self.completed_at - self.started_at).total_seconds()
        fastest_seconds = fastest_time.total_seconds()

        speed_score = (fastest_seconds / user_time) * 100 if user_time > 0 else 0
        word_score = (self.word_count / max_words) * 100 if max_words > 0 else 0
        spelling_score = max(0, 100 - (self.spelling_errors * 3))

        final = (
            speed_score * 0.30 +
            word_score * 0.20 +
            self.grammar_score * 0.30 +
            spelling_score * 0.20
        )

        self.final_score = round(final, 2)
        self.save()

    # ===============================
    # COMPLETE ESSAY
    # ===============================
    def complete_essay(self):
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.word_count = self.calculate_word_count()
            self.analyze_grammar()
            self.save()

    class Meta:
        ordering = ['-started_at']
        unique_together = ['user', 'competition']
        verbose_name = 'Essay'
        verbose_name_plural = 'Essays'


class Paragraph(models.Model):
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
