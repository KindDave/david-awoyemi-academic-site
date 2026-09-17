# Moodle Setup Guide

How to install the LMS, brand it, import the courses, and finish the parts that a course package cannot carry. Written for one person running the system.

## 1. Prerequisites

- A Linux server (Ubuntu 24.04 recommended) with 2 vCPU, 4 GB RAM, 40 GB disk, and a public IP. Any major VPS provider works. For a local trial, Docker Desktop on Windows or Mac is enough.
- Docker Engine and the Docker Compose plugin installed.
- A domain or subdomain (for example `learn.example.com`) with an A record pointing at the server. Not needed for a local trial.

## 1a. Windows: state of this machine (as of 2026-09-17)

Docker Desktop was installed through winget on this PC, and its installer enabled the two Windows features it needs (Windows Subsystem for Linux and Virtual Machine Platform). Those features finish installing only after a restart, and the Docker Desktop application itself was not yet placed on disk. To finish:

Update, later on 2026-09-17: Docker Desktop 4.91 and the WSL package (Microsoft.WSL 2.7.13, from winget with elevation) are both installed. Docker showed "Virtualization support not detected" because Windows had not actually restarted since the features were enabled; a Shut down followed by power on does not count (Fast Startup hibernates instead). Use **Start > Power > Restart**. After that, Docker Desktop should start its engine on its own. If it still reports no virtualization after a true restart, run this in an administrator PowerShell and restart once more:

```powershell
bcdedit /set hypervisorlaunchtype auto
```

Original steps, kept for reference:

1. Restart Windows (Restart, not Shut down).
2. Open PowerShell and run `wsl --install --no-distribution`, then restart again if it asks.
3. Run `winget install -e --id Docker.DockerDesktop` and approve the administrator prompt. Start Docker Desktop from the Start menu, accept its service agreement (free for personal and education use), and wait for "Docker Desktop is running".
4. Continue with section 2 below, using the local-trial settings.

ffmpeg was also installed for the current user (used by the video generator, not by Moodle).

## 2. Install (about 15 minutes)

```bash
# On the server (or locally), copy the docker folder from this repository
cd lms/docker
cp .env.example .env
nano .env            # set every password, the admin email, MOODLE_HOST, and the proxy flags
docker compose up -d
docker compose logs -f moodle
```

Wait until the log shows `Moodle setup finished`. First boot takes 3 to 6 minutes.

- **Local trial:** `MOODLE_HOST=localhost`, both proxy flags `no`, then open http://localhost:8080. You can remove the `caddy` service from the compose file for local use.
- **Production:** `MOODLE_HOST=learn.example.com`, both proxy flags `yes`. Caddy obtains an HTTPS certificate automatically; open https://learn.example.com.

Sign in with the admin user and password from `.env`.

**If the Bitnami image cannot be pulled** (Bitnami has been moving images between `bitnami/` and `bitnamilegacy/`), change the image line to `docker.io/bitnamilegacy/moodle:4.5` with the same configuration. If neither is available, the official `moodlehq/moodle-php-apache:8.3` image plus a checkout of Moodle from https://github.com/moodle/moodle works with the same database settings; see the Moodle docs page "Installing Moodle" for the manual steps.

## 3. First-run configuration (about 30 minutes)

Do these in Site administration:

1. **General > Site home**: site name, short name, front page description. Show "list of courses" on the front page.
2. **Users > Permissions > User policies**: keep guest access off site-wide; you will allow guests per course only where needed.
3. **Users > Privacy and policies**: add a site policy that states what data is collected and that research courses have separate consent.
4. **Plugins > Enrolments**: enable Self enrolment so you can give cohorts an enrollment key.
5. **Server > Email**: configure outgoing mail (an SMTP relay such as your institution's, or a transactional email service). Without it, no notifications or password resets go out.
6. **Server > Scheduled tasks**: confirm cron is running (the Bitnami image runs it; the "cron last ran" warning on the notifications page should be gone within a few minutes).
7. **Security > HTTP security**: with Caddy in front, confirm the site URL is https and "Cookie secure" is on.
8. **Development > Debugging**: leave at "None" in production.

## 4. Branding (about 20 minutes)

1. Appearance > Themes > Theme selector: Boost.
2. Appearance > Themes > Boost > General settings:
   - Brand colour: `#0f2d6b`
   - Upload the logo from the website repository (`assets/images/brand-logo.png`) as the site logo and compact logo.
3. Boost > Advanced settings > Raw SCSS: paste the block from `01-lms-design.md` section 5.
4. Appearance > Logos: favicon from the same logo.
5. Course > Course default settings: format "Topics" (called "Custom sections" in 4.5), course layout "Show one section per page".

## 5a. Scripted deployment (what was done on 2026-09-17)

Sections 4 to 6 can be done in one command once the stack is running:

```powershell
powershell -File lms/scripts/deploy_moodle.ps1
```

It brands the site, creates the four categories, restores both `-with-media` packages, converts every assignment page into an Assignment activity with the right points, sets quiz attempts and review options, sets forum attachment limits, enables self-enrolment with a key, and enrols a "teststudent" account (its password is printed at the end). Two facts learned while building it:

- Moodle's own `admin/cli/restore_backup.php` cannot restore Common Cartridge files (it crashes before the conversion step), so the deploy uses `lms/scripts/moodle_restore_cc.php`, which follows the web restore sequence. The cartridge converter also needs the working directory to be Moodle's `backup/` folder; the script handles that.
- Moodle 4.5 imports cartridge HTML as **Page** activities, with the embedded videos, captions, and transcripts stored as the page's files. Nothing further is needed for video.

Local trial URL is **http://localhost:8080** (Moodle's own port, bypassing the Caddy proxy). Moodle's site URL in the container's `config.php` was changed to that address on 2026-09-17 because Edge had cached a permanent redirect from http://localhost to https://localhost from the proxy's first configuration, and nothing serves HTTPS locally. Port 80 (Caddy) is only needed in production with a real domain; for a production move, set `MOODLE_HOST` and `SITE_ADDRESS` in `.env` to the domain and change `$CFG->wwwroot` in `config.php` to match.

Enrolment keys set by the deploy: `genai-pilot-2026` for GENAI 101 and `id553-2026` for ID 553. Change them in each course's Participants > Enrolment methods before real use.

## 5. Import a course manually (about 10 minutes per course)

The build script produces IMS Common Cartridge 1.1 files in `lms/dist/`. Moodle imports them through Restore.

1. Site administration > Courses > Manage courses and categories: create the categories from `01-lms-design.md` section 6.
2. Site administration > Courses > Restore course (or Course > Restore from any course page).
3. Upload `lms/dist/<slug>.imscc`. Moodle detects "IMS Common Cartridge 1.1" and converts it.
4. Choose "Restore as a new course" into the right category. Accept defaults; click through to Perform restore.
5. Open the new course. Each module has become a section; pages, forums, quizzes, and links are in place.

If the upload limit blocks the file, raise **Site administration > Security > Site security settings > Maximum uploaded file size**; the compose file already sets PHP limits to 256 MB.

**Canvas** (if you ever host there): Course Settings > Import Course Content > "Common Cartridge 1.x Package". **Blackboard Learn**: Course Management > Packages and Utilities > Import Package. Both accept the same `.imscc` file.

## 6. Post-import checklist

Common Cartridge 1.1 carries pages, forums, quizzes, and links faithfully. A few things need finishing by hand.

**Assignments.** The cartridge delivers each assignment as a page with instructions and the rubric (there is no assignment type in CC 1.1). For each one:

1. Add an activity > Assignment with the same name. Paste the page content into the description (copy from the page). Set the points from the assignment title in the preview, the due date, and the submission type (file upload or online text; allow PDF and Google Doc links).
2. Turn on the Rubric grading method (Assignment settings > Grade > Grading method > Rubric) and enter the rubric rows from the page. Rubric levels and points are already written in the content.
3. Hide or delete the original page once the Assignment activity exists.

**Forums.** For gallery forums, set Forum type to "Standard forum for general use" and allow attachments (max 50 MB, so audio and video can be uploaded). For the "Questions" thread mentioned in the welcome pages, create and pin that discussion in the introduction forum.

**Quizzes.** Open each quiz > Settings: Grade > Attempts allowed = Unlimited, Grading method = Highest grade (knowledge checks); for pre- and post-course self-assessments set Attempts = 1 and Grade to pass = none. Review options: show specific feedback and right answers after each attempt.

**Videos.** Two package variants exist for each course:

- `lms/dist/<slug>.imscc` (about 100 KB): pages show a callout naming the video. Use this if you host videos on YouTube or your institution's video platform; paste the embed code into each page in place of the callout.
- `lms/dist/<slug>-with-media.imscc` (18 to 35 MB): every page already contains its narrated video with captions and a transcript link. Import this one and nothing further is needed for video.

The 24 videos were generated by `lms/scripts/make_videos.py` from the scripts in `lms/videos/`: branded slides with synthetic narration (Windows text-to-speech), WebVTT captions, and a Markdown transcript per video. They are complete drafts, not recordings of the instructor. To replace any of them with your own recording, read its transcript in `lms/media/<slug>/<id>-transcript.md`, record, and either drop your MP4 over the generated one (same file name) and rebuild with `--with-media`, or embed a YouTube link in the page in Moodle. Because the videos are not committed to git, run `python lms/scripts/make_videos.py` once on a fresh clone before building with media.

**Gradebook.** Grade > Gradebook setup: create categories matching the weights on the course welcome page (for example GENAI 101: galleries 40%, knowledge checks 10%, reflections 20%, final project 30%). Move each activity into its category.

**Completion and certificates.** Course > Course completion: require the activities listed on each course's completion page. Optionally install the "Custom certificate" plugin (mod_customcert) and add a certificate activity restricted to course completion.

**Guest and enrollment.** Course > Participants > Enrolment methods: add Self enrolment with an enrollment key for each cohort; disable guest access unless you want the description public.

## 7. Add a test student and run Module 0

Create a user "Test Student", enroll them, and log in as them (Site administration > Users > Browse list > Log in as). Complete Module 0 end to end. Fix anything that needs the instructor to explain it.

## 8. Backups

Add to the server's crontab (adjust paths):

```bash
# nightly at 02:30: database dump and moodledata archive
30 2 * * * cd /opt/lms/docker && docker compose exec -T mariadb mysqldump -u root -p"$DB_ROOT_PASSWORD" bitnami_moodle | gzip > /opt/backups/db-$(date +\%F).sql.gz && docker run --rm -v docker_moodle_data:/data -v /opt/backups:/backup alpine tar czf /backup/moodledata-$(date +\%F).tgz -C /data . && find /opt/backups -mtime +14 -delete
```

Copy `/opt/backups` off the server (rclone to cloud storage, or your institution's backup service). Test a restore on a local Docker instance every few months.

Also enable Site administration > Courses > Backups > Automated backup setup (weekly, keep 4) so each course can be restored individually.

## 9. Updates

```bash
cd lms/docker
docker compose pull
docker compose up -d
```

Moodle point releases apply on container restart. Before a major version change (for example 4.5 to 5.x), take a full backup, test the upgrade locally, and read the release notes for plugin compatibility.

## 10. If self-hosting becomes a burden

MoodleCloud (moodlecloud.com) runs the same software as a subscription. Export each course as a Moodle backup (Course > Backup, .mbz) or reuse the `.imscc` files from this repository and import them there. Nothing in the authoring pipeline changes.
