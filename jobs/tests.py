from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .models import Application, Job


class JobViewsTests(TestCase):
    def setUp(self):
        self.employer = CustomUser.objects.create_user(
            username="employer", password="test-password", role="employer"
        )
        self.applicant = CustomUser.objects.create_user(
            username="applicant", password="test-password", role="seeker"
        )
        self.job = Job.objects.create(
            title="Developer",
            company_name="Example Co",
            description="Build useful things.",
            location="Remote",
            salary="80000.00",
            posted_by=self.employer,
        )

    def test_job_create_assigns_current_user_as_poster(self):
        self.client.force_login(self.employer)

        response = self.client.post(
            reverse("job_create"),
            {
                "title": "Designer",
                "company_name": "Another Co",
                "description": "Design useful things.",
                "location": "Remote",
                "salary": "70000.00",
            },
        )

        self.assertRedirects(response, reverse("my_jobs"))
        created_job = Job.objects.get(title="Designer")
        self.assertEqual(created_job.posted_by, self.employer)

    def test_job_update_and_delete_are_limited_to_owner(self):
        other_employer = CustomUser.objects.create_user(
            username="other-employer", password="test-password", role="employer"
        )
        self.client.force_login(other_employer)

        update_response = self.client.get(
            reverse("job_update", kwargs={"pk": self.job.pk})
        )
        delete_response = self.client.get(
            reverse("job_delete", kwargs={"pk": self.job.pk})
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_my_jobs_and_applications_only_show_current_users_records(self):
        Application.objects.create(job=self.job, applicant=self.applicant)
        self.client.force_login(self.applicant)

        applications_response = self.client.get(reverse("my_applications"))
        self.client.force_login(self.employer)
        jobs_response = self.client.get(reverse("my_jobs"))

        self.assertEqual(applications_response.status_code, 200)
        self.assertEqual(
            list(applications_response.context["applications"]),
            [Application.objects.get(applicant=self.applicant)],
        )
        self.assertEqual(list(jobs_response.context["jobs"]), [self.job])

    def test_apply_requires_post_and_does_not_create_duplicates(self):
        self.client.force_login(self.applicant)
        apply_url = reverse("apply_to_job", kwargs={"job_id": self.job.pk})

        get_response = self.client.get(apply_url)
        post_response = self.client.post(apply_url)
        duplicate_response = self.client.post(apply_url)

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(
            post_response, reverse("job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertRedirects(
            duplicate_response, reverse("job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(Application.objects.filter(job=self.job).count(), 1)

    def test_login_is_required_for_private_views_and_applying(self):
        apply_url = reverse("apply_to_job", kwargs={"job_id": self.job.pk})

        for url in (
            reverse("job_create"),
            reverse("my_jobs"),
            reverse("my_applications"),
            apply_url,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_guest_header_links_to_protected_job_posting_and_account_pages(self):
        response = self.client.get(reverse("job_list"))

        self.assertContains(response, f'href="{reverse("job_create")}"')
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, f'href="{reverse("signup")}"')

    def test_only_employers_can_post_and_only_seekers_can_apply(self):
        self.client.force_login(self.applicant)
        self.assertEqual(self.client.get(reverse("job_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("my_jobs")).status_code, 403)

        self.client.force_login(self.employer)
        self.assertEqual(self.client.get(reverse("job_create")).status_code, 200)
        employer_detail = self.client.get(
            reverse("job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertContains(employer_detail, "Switch to Job Seeker")
        self.assertNotContains(employer_detail, "Apply now")
        self.assertEqual(
            self.client.post(
                reverse("apply_to_job", kwargs={"job_id": self.job.pk})
            ).status_code,
            403,
        )
        self.assertFalse(Application.objects.filter(job=self.job).exists())

    def test_employer_can_switch_to_seeker_and_apply(self):
        self.client.force_login(self.employer)
        detail_url = reverse("job_detail", kwargs={"pk": self.job.pk})
        switch_response = self.client.post(
            reverse("switch_role"), {"next": detail_url}
        )

        self.assertRedirects(switch_response, detail_url)
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.role, "seeker")

        detail_response = self.client.get(detail_url)
        self.assertContains(detail_response, "Apply now")
        self.assertContains(detail_response, "Switch to Employer")
        apply_response = self.client.post(
            reverse("apply_to_job", kwargs={"job_id": self.job.pk})
        )

        self.assertRedirects(apply_response, detail_url)
        self.assertTrue(
            Application.objects.filter(job=self.job, applicant=self.employer).exists()
        )

    def test_role_switch_requires_login_and_post(self):
        switch_url = reverse("switch_role")

        anonymous_response = self.client.post(switch_url)
        self.assertRedirects(
            anonymous_response,
            f"{reverse('login')}?next={switch_url}",
            fetch_redirect_response=False,
        )

        self.client.force_login(self.employer)
        self.assertEqual(self.client.get(switch_url).status_code, 405)

    def test_guest_cannot_post_or_apply_before_signing_in(self):
        create_url = reverse("job_create")
        apply_url = reverse("apply_to_job", kwargs={"job_id": self.job.pk})

        create_response = self.client.post(create_url, {})
        apply_response = self.client.post(apply_url)

        self.assertRedirects(
            create_response,
            f"{reverse('login')}?next={create_url}",
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            apply_response,
            f"{reverse('login')}?next={apply_url}",
            fetch_redirect_response=False,
        )
        self.assertFalse(Application.objects.filter(job=self.job).exists())

    def test_signup_preserves_next_url_for_login_after_registration(self):
        create_url = reverse("job_create")
        signup_url = f"{reverse('signup')}?next={create_url}"
        response = self.client.post(
            signup_url,
            {
                "username": "newemployer",
                "first_name": "New",
                "last_name": "Employer",
                "email": "employer@example.com",
                "role": "employer",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
                "next": create_url,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next=%2Fjobs%2Fcreate%2F",
            fetch_redirect_response=False,
        )
        new_user = CustomUser.objects.get(username="newemployer")
        self.assertEqual(new_user.first_name, "New")
        self.assertEqual(new_user.last_name, "Employer")

    def test_signup_requires_first_and_last_name(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "nameless",
                "email": "nameless@example.com",
                "role": "seeker",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First name")
        self.assertContains(response, "Last name")
        self.assertFalse(CustomUser.objects.filter(username="nameless").exists())

    def test_homepage_greets_signed_in_user_by_name_or_username(self):
        self.applicant.first_name = "Ada"
        self.applicant.last_name = "Lovelace"
        self.applicant.save(update_fields=["first_name", "last_name"])
        self.client.force_login(self.applicant)

        named_response = self.client.get(reverse("job_list"))
        self.assertContains(named_response, "Welcome,")
        self.assertContains(named_response, "Ada")
        self.assertContains(named_response, "Lovelace")

        self.client.force_login(self.employer)
        username_response = self.client.get(reverse("job_list"))
        self.assertContains(username_response, "employer")

    def test_public_pages_link_to_login_and_signup(self):
        home_response = self.client.get(reverse("job_list"))
        login_response = self.client.get(reverse("login"))
        signup_response = self.client.get(reverse("signup"))

        self.assertContains(home_response, f'href="{reverse("login")}"')
        self.assertContains(home_response, "Log in / Sign up")
        self.assertNotContains(home_response, f'href="{reverse("signup")}"')
        self.assertContains(login_response, f'href="{reverse("signup")}"')
        self.assertContains(signup_response, f'href="{reverse("login")}"')

    def test_authenticated_header_shows_job_navigation(self):
        self.client.force_login(self.employer)

        response = self.client.get(reverse("job_list"))

        self.assertContains(response, f'href="{reverse("job_create")}"')
        self.assertContains(response, f'href="{reverse("my_jobs")}"')
        self.assertContains(response, 'Switch to Job Seeker')
        self.assertContains(response, f'action="{reverse("switch_role")}"')
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, "Log in / Sign up")
        self.assertNotContains(response, f'href="{reverse("signup")}"')
        self.assertNotContains(response, "Log out")

        self.client.force_login(self.applicant)
        applicant_response = self.client.get(reverse("job_list"))
        self.assertContains(
            applicant_response, f'href="{reverse("my_applications")}"'
        )
        self.assertContains(applicant_response, 'Switch to Employer')

    def test_styled_pages_link_to_shared_stylesheet(self):
        self.client.force_login(self.employer)
        employer_pages = (
            reverse("job_create"),
            reverse("my_jobs"),
        )
        for url in employer_pages:
            with self.subTest(url=url):
                self.assertContains(
                    self.client.get(url), 'href="/static/jobs/site.css"'
                )

        self.client.force_login(self.applicant)
        self.assertContains(
            self.client.get(reverse("my_applications")),
            'href="/static/jobs/site.css"',
        )

        self.client.logout()
        for url in (reverse("login"), reverse("signup")):
            with self.subTest(url=url):
                self.assertContains(
                    self.client.get(url), 'href="/static/jobs/site.css"'
                )

    def test_job_detail_shows_shared_style_and_application_action(self):
        self.client.force_login(self.applicant)

        response = self.client.get(
            reverse("job_detail", kwargs={"pk": self.job.pk})
        )

        self.assertContains(response, 'href="/static/jobs/site.css"')
        self.assertContains(response, "Apply now")
