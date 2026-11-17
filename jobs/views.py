from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import JobForm
from .models import Application, Job


class EmployerRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.role == "employer"


class JobSeekerRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.request.user.role == "seeker"


class JobListView(ListView):
    model = Job
    template_name = "job_list.html"
    context_object_name = "all_jobs"


class JobDetailView(DetailView):
    model = Job
    template_name = "job_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["already_applied"] = (
            self.request.user.is_authenticated
            and Application.objects.filter(
                job=self.object, applicant=self.request.user
            ).exists()
        )
        return context


class JobCreateView(LoginRequiredMixin, EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "job_form.html"
    success_url = reverse_lazy("my_jobs")

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)


class MyJobsListView(LoginRequiredMixin, EmployerRequiredMixin, ListView):
    model = Job
    template_name = "my_jobs_list.html"
    context_object_name = "jobs"

    def get_queryset(self) -> QuerySet[Job]:
        return Job.objects.filter(posted_by=self.request.user)


class JobUpdateView(LoginRequiredMixin, EmployerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = "job_form.html"
    success_url = reverse_lazy("my_jobs")

    def get_queryset(self) -> QuerySet[Job]:
        return Job.objects.filter(posted_by=self.request.user)


class JobDeleteView(LoginRequiredMixin, EmployerRequiredMixin, DeleteView):
    model = Job
    template_name = "job_confirm_delete.html"
    success_url = reverse_lazy("my_jobs")

    def get_queryset(self) -> QuerySet[Job]:
        return Job.objects.filter(posted_by=self.request.user)


@login_required
@require_POST
def apply_to_job(request: HttpRequest, job_id: int) -> HttpResponse:
    job = get_object_or_404(Job, pk=job_id)
    if request.user.role != "seeker":
        return HttpResponseForbidden("Only job seekers can apply for jobs.")
    Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect("job_detail", pk=job.pk)


@login_required
@require_POST
def switch_role(request: HttpRequest) -> HttpResponse:
    role_switches = {"employer": "seeker", "seeker": "employer"}
    new_role = role_switches.get(request.user.role)
    if new_role is None:
        return HttpResponseForbidden("This account cannot switch roles.")

    request.user.role = new_role
    request.user.save(update_fields=["role"])
    messages.success(
        request, f"Your account is now set to {request.user.get_role_display()}."
    )

    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("job_list")
    return redirect(next_url)


class MyApplicationsListView(LoginRequiredMixin, JobSeekerRequiredMixin, ListView):
    model = Application
    template_name = "my_applications_list.html"
    context_object_name = "applications"

    def get_queryset(self) -> QuerySet[Application]:
        return Application.objects.filter(applicant=self.request.user).select_related(
            "job"
        )
