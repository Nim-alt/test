from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

class Defect(models.Model):
    # Basic information
    title = models.CharField(max_length=200, verbose_name="Defect Title")
    description = models.TextField(verbose_name="Defect Description")
    reporter_email = models.EmailField(verbose_name="Reporter Email")

    # Severity
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name="Severity"
    )

    # Priority
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priority"
    )

    # Status (Defect lifecycle for Sprint 1)
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('fixed', 'Fixed'),
        ('resolved', 'Resolved'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Status"
    )

    # Assigned to Developer
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assigned To"
    )

    # Timestamps
    date_reported = models.DateTimeField(auto_now_add=True, verbose_name="Reported Date")
    date_fixed = models.DateTimeField(null=True, blank=True, verbose_name="Fixed Date")

    def __str__(self):
        return f"#{self.id} - {self.title}"

    class Meta:
        verbose_name = "Defect"
        verbose_name_plural = "Defects"


# ==================== Email Notification (Sprint 1) ====================
@receiver(post_save, sender=Defect)
def send_defect_notification(sender, instance, created, **kwargs):
    """Send email notification when a defect is created or status changes"""
    if created:
        action = "created"
    else:
        action = "status updated"

    subject = f"BetaTrax - Defect #{instance.id} {action} - {instance.get_status_display()}"
    message = f"""
Defect Title: {instance.title}
Current Status: {instance.get_status_display()}
Reporter Email: {instance.reporter_email}
Severity: {instance.get_severity_display()}
Priority: {instance.get_priority_display()}
    """

    send_mail(
        subject=subject,
        message=message,
        from_email='betatrax@example.com',
        recipient_list=[instance.reporter_email],
        fail_silently=False,
    )