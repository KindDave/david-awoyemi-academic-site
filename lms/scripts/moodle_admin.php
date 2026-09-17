<?php
/**
 * Moodle administration helper, run inside the Moodle container with the Moodle PHP:
 *
 *   php moodle_admin.php setup   --logo=/tmp/brand-logo.png
 *       Brands the site (Boost colours, fonts, logo), creates course categories, and prints
 *       a JSON map of category name -> id.
 *
 *   php moodle_admin.php postimport --course="<course full name>" --spec=/tmp/<slug>.spec.json
 *       For a course restored from a Common Cartridge: converts assignment pages into Assignment
 *       activities (with the page content as the description and the points as the grade),
 *       sets quiz attempts/grading/review options, sets forum attachment limits, moves the
 *       course into its category, makes it visible, adds self-enrolment, enrols the test student.
 *
 *   php moodle_admin.php teststudent
 *       Creates (or resets) the "Test Student" account and prints its password.
 *
 * The spec JSON is produced by deploy_moodle.ps1 from course.json.
 */

define('CLI_SCRIPT', true);
$configcandidates = ['/bitnami/moodle/config.php', '/opt/bitnami/moodle/config.php', __DIR__ . '/../../config.php'];
foreach ($configcandidates as $c) { if (file_exists($c)) { require($c); break; } }
if (!isset($CFG)) { fwrite(STDERR, "Moodle config.php not found\n"); exit(1); }
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/user/lib.php');
require_once($CFG->dirroot . '/lib/enrollib.php');

list($options, $unrecognized) = cli_get_params(
    ['course' => '', 'spec' => '', 'logo' => '', 'help' => false],
    ['h' => 'help']
);
$command = $unrecognized[0] ?? 'help';

$BRAND = '#0f2d6b';
$SCSS = <<<SCSS
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Crimson+Pro:wght@500;600;700&display=swap');
body { font-family: 'Atkinson Hyperlegible', 'Segoe UI', Arial, sans-serif; }
h1, h2, h3, h4, .h1, .h2, .h3, .h4, .navbar-brand { font-family: 'Crimson Pro', Georgia, serif; }
.navbar { border-bottom: 3px solid #c3902f; }
.btn-primary { background-color: #0f2d6b; border-color: #0f2d6b; }
.btn-primary:hover { background-color: #1f4ba3; border-color: #1f4ba3; }
a { color: #1f4ba3; }
/* Course page content imported from the lms/ cartridges */
.callout { border-left: 4px solid #c3902f; background: rgba(15,45,107,.06); padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 1.2em 0; }
.callout strong:first-child { color: #0f2d6b; }
.kicker { display: inline-block; font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: #c3902f; font-weight: 700; }
.badge { background: #0f2d6b; color: #fff; }
.meta { color: #65759a; font-size: .9rem; margin-bottom: 1.2em; }
figure.video { margin: 1.2em 0; }
figure.video video { width: 100%; max-width: 900px; border-radius: 10px; background: #000; }
figure.video figcaption { color: #65759a; font-size: .9rem; margin-top: .4em; }
.yt-wrap { position: relative; max-width: 900px; aspect-ratio: 16 / 9; border-radius: 10px; overflow: hidden; background: #000; }
.yt-wrap iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
.page-content table, .assign-intro table, .no-overflow table { border-collapse: collapse; width: 100%; margin: 1em 0; }
.page-content th, .page-content td, .assign-intro th, .assign-intro td, .no-overflow th, .no-overflow td { border: 1px solid rgba(15,45,107,.14); padding: 8px 10px; vertical-align: top; }
.page-content th, .assign-intro th, .no-overflow th { background: rgba(15,45,107,.06); color: #0f2d6b; }
.page-content blockquote, .assign-intro blockquote { margin: 1em 0; padding: .4em 1em; border-left: 3px solid #1f4ba3; background: #f7f9fe; }
SCSS;

$CATEGORIES = [
    'AI Literacy and Emerging Technology',
    'Instructional Design',
    'STEM and Physical Computing',
    'Research Studies',
];

function out($msg) { echo $msg . "\n"; }

function ensure_test_student(): array {
    global $DB, $CFG;
    $username = 'teststudent';
    $password = 'Test-' . substr(bin2hex(random_bytes(6)), 0, 10) . '!9';
    $user = $DB->get_record('user', ['username' => $username, 'deleted' => 0]);
    if (!$user) {
        $u = new stdClass();
        $u->username = $username;
        $u->auth = 'manual';
        $u->confirmed = 1;
        $u->mnethostid = $CFG->mnet_localhost_id;
        $u->firstname = 'Test';
        $u->lastname = 'Student';
        $u->email = 'teststudent@example.invalid';
        $u->password = $password;
        $id = user_create_user($u, true, false);
        $user = $DB->get_record('user', ['id' => $id]);
        out("created user teststudent");
    } else {
        update_internal_user_password($user, $password);
        out("reset password for teststudent");
    }
    return [$user, $password];
}

switch ($command) {

case 'setup':
    set_config('theme', 'boost');
    set_config('brandcolor', $BRAND, 'theme_boost');
    set_config('scss', $SCSS, 'theme_boost');
    set_config('enrol_plugins_enabled', 'manual,guest,self,cohort');
    set_config('maxbytes', 268435456);              // 256 MB site upload limit
    set_config('sitepolicyhandler', '');
    if ($options['logo'] && file_exists($options['logo'])) {
        $fs = get_file_storage();
        $ctx = context_system::instance();
        foreach (['logo' => 'logo', 'logocompact' => 'logocompact', 'favicon' => 'favicon'] as $area => $setting) {
            $fs->delete_area_files($ctx->id, 'core_admin', $area, 0);
            $fs->create_file_from_pathname([
                'contextid' => $ctx->id, 'component' => 'core_admin', 'filearea' => $area,
                'itemid' => 0, 'filepath' => '/', 'filename' => 'brand-logo.png',
            ], $options['logo']);
            set_config($setting, '/brand-logo.png', 'core_admin');
        }
        out("logo, compact logo, and favicon set");
    }
    theme_reset_all_caches();
    $ids = [];
    foreach ($CATEGORIES as $name) {
        $cat = $DB->get_record('course_categories', ['name' => $name]);
        if (!$cat) {
            $cat = core_course_category::create(['name' => $name, 'parent' => 0, 'visible' => $name === 'Research Studies' ? 0 : 1]);
            out("created category: $name");
        }
        $ids[$name] = (int)$cat->id;
    }
    // Front page: show the list of available courses.
    set_config('frontpage', '6');
    set_config('frontpageloggedin', '6');
    purge_all_caches();
    out("CATEGORIES_JSON=" . json_encode($ids));
    break;

case 'teststudent':
    list($user, $password) = ensure_test_student();
    out("TESTSTUDENT_PASSWORD=$password");
    break;

case 'postimport':
    $fullname = $options['course'];
    $spec = json_decode(file_get_contents($options['spec']), true);
    if (!$fullname || !$spec) { cli_error("--course and --spec are required"); }
    $course = $DB->get_record('course', ['fullname' => $fullname]);
    if (!$course) {
        // Restored course names may carry a suffix; fall back to a prefix match.
        $course = $DB->get_record_select('course', $DB->sql_like('fullname', ':n'), ['n' => $fullname . '%'], '*', IGNORE_MULTIPLE);
    }
    if (!$course) { cli_error("course not found: $fullname"); }
    out("course id {$course->id}: {$course->fullname}");

    // Category and visibility.
    if (!empty($spec['category'])) {
        $cat = $DB->get_record('course_categories', ['name' => $spec['category']]);
        if ($cat && $course->category != $cat->id) { move_courses([$course->id], $cat->id); out("moved to category {$spec['category']}"); }
    }
    $DB->set_field('course', 'visible', 1, ['id' => $course->id]);
    if (!empty($spec['shortname'])) {
        if (!$DB->record_exists_select('course', 'shortname = :s AND id <> :id', ['s' => $spec['shortname'], 'id' => $course->id])) {
            $DB->set_field('course', 'shortname', $spec['shortname'], ['id' => $course->id]);
        }
    }
    $course = $DB->get_record('course', ['id' => $course->id]);

    $modinfo = get_fast_modinfo($course);
    $assignmodule = $DB->get_field('modules', 'id', ['name' => 'assign']);
    $fs = get_file_storage();
    $converted = 0;

    // Content of an imported cartridge page, minus the kicker/title/meta lines that
    // duplicate what Moodle already shows as the activity heading.
    $tidy = function (string $html): string {
        if (preg_match('~<body[^>]*>(.*)</body>~s', $html, $m)) { $html = $m[1]; }
        $html = preg_replace('~<div class="kicker">.*?</div>~s', '', $html, 1);
        $html = preg_replace('~<h1>.*?</h1>~s', '', $html, 1);
        $html = preg_replace('~<div class="meta">.*?</div>~s', '', $html, 1);
        // Moodle's media filter treats width="100%" as 100 px; give videos explicit 16:9 dimensions.
        $html = str_replace('<video controls preload="metadata" width="100%"', '<video controls preload="metadata" width="900" height="506"', $html);
        return trim($html);
    };

    // 0. Tidy every imported page (Moodle 4.5 imports cartridge HTML as Page activities).
    $tidied = 0;
    foreach ($modinfo->get_cms() as $cm) {
        if ($cm->modname !== 'page') { continue; }
        $page = $DB->get_record('page', ['id' => $cm->instance], 'id, content');
        $new = $tidy($page->content);
        if ($new !== $page->content) {
            $DB->update_record('page', (object)['id' => $page->id, 'content' => $new, 'timemodified' => time()]);
            $tidied++;
        }
    }
    out("tidied $tidied pages");

    // 1. Assignment pages -> Assignment activities.
    foreach ($spec['assignments'] as $a) {
        foreach ($modinfo->get_cms() as $cm) {
            if (!in_array($cm->modname, ['page', 'resource'], true) || $cm->name !== $a['title']) { continue; }
            $html = '';
            if ($cm->modname === 'page') {
                $html = $DB->get_field('page', 'content', ['id' => $cm->instance]);
            } else {
                $ctx = context_module::instance($cm->id);
                foreach ($fs->get_area_files($ctx->id, 'mod_resource', 'content', 0, 'sortorder DESC, id ASC', false) as $f) {
                    if (substr($f->get_filename(), -5) === '.html') { $html = $f->get_content(); break; }
                }
            }
            $html = $tidy($html);

            $mod = new stdClass();
            $mod->modulename = 'assign';
            $mod->module = $assignmodule;
            $mod->course = $course->id;
            $mod->section = $cm->sectionnum;
            $mod->visible = 1;
            $mod->visibleoncoursepage = 1;
            $mod->name = $a['title'];
            $mod->intro = $html;
            $mod->introformat = FORMAT_HTML;
            $mod->alwaysshowdescription = 1;
            $mod->submissiondrafts = 0;
            $mod->requiresubmissionstatement = 0;
            $mod->sendnotifications = 0;
            $mod->sendlatenotifications = 0;
            $mod->sendstudentnotifications = 1;
            $mod->duedate = 0; $mod->allowsubmissionsfromdate = 0; $mod->cutoffdate = 0; $mod->gradingduedate = 0;
            $mod->grade = (int)($a['points'] ?? 100);
            $mod->teamsubmission = 0; $mod->requireallteammemberssubmit = 0; $mod->teamsubmissiongroupingid = 0;
            $mod->blindmarking = 0; $mod->hidegrader = 0; $mod->markingworkflow = 0; $mod->markingallocation = 0;
            $mod->attemptreopenmethod = 'untilpass'; $mod->maxattempts = -1; $mod->preventsubmissionnotingroup = 0;
            $mod->assignsubmission_onlinetext_enabled = 1;
            $mod->assignsubmission_file_enabled = 1;
            $mod->assignsubmission_file_maxfiles = 5;
            $mod->assignsubmission_file_maxsizebytes = 52428800;
            $mod->assignsubmission_file_filetypes = '';
            $mod->assignfeedback_comments_enabled = 1;
            $mod->assignfeedback_comments_commentinline = 0;
            $mod->cmidnumber = ''; $mod->groupmode = 0; $mod->groupingid = 0;
            $mod->completion = 0;
            $info = add_moduleinfo($mod, $course);

            // Place the new activity where the page was, then remove the page.
            $newcm = get_coursemodule_from_id('assign', $info->coursemodule, $course->id, false, MUST_EXIST);
            $section = $DB->get_record('course_sections', ['course' => $course->id, 'section' => $cm->sectionnum], '*', MUST_EXIST);
            $seq = explode(',', $section->sequence);
            $pos = array_search((string)$cm->id, $seq, true);
            $before = ($pos !== false && isset($seq[$pos + 1])) ? (int)$seq[$pos + 1] : null;
            if ($before && $before != $newcm->id) { moveto_module($newcm, $section, $before); }
            course_delete_module($cm->id);
            $converted++;
            out("assignment: {$a['title']} ({$mod->grade} points)");
            break;
        }
    }
    rebuild_course_cache($course->id, true);
    $modinfo = get_fast_modinfo($course);

    // 2. Quiz settings.
    $reviewall = 0x11110; // during, immediately after, later while open, after close
    foreach ($modinfo->get_cms() as $cm) {
        if ($cm->modname !== 'quiz') { continue; }
        $issurvey = false;
        foreach ($spec['surveys'] as $s) { if ($cm->name === $s) { $issurvey = true; } }
        $upd = (object)[
            'id' => $cm->instance,
            'attempts' => $issurvey ? 1 : 0,
            'grademethod' => 1, // highest grade
            'reviewattempt' => $reviewall, 'reviewcorrectness' => $reviewall, 'reviewmarks' => $reviewall,
            'reviewspecificfeedback' => $reviewall, 'reviewgeneralfeedback' => $reviewall,
            'reviewrightanswer' => $reviewall, 'reviewoverallfeedback' => $reviewall,
            'preferredbehaviour' => 'deferredfeedback',
            'timemodified' => time(),
        ];
        $DB->update_record('quiz', $upd);
        out("quiz: {$cm->name}" . ($issurvey ? " (1 attempt, survey)" : " (unlimited, highest)"));
    }

    // 3. Forum settings: general forum, attachments allowed for artifacts.
    foreach ($modinfo->get_cms() as $cm) {
        if ($cm->modname !== 'forum') { continue; }
        $DB->update_record('forum', (object)['id' => $cm->instance, 'type' => 'general',
            'maxbytes' => 52428800, 'maxattachments' => 3, 'forcesubscribe' => 0, 'timemodified' => time()]);
    }
    out("forums configured");

    // 4. Self enrolment (with key if given) and test student.
    $self = enrol_get_plugin('self');
    $instances = enrol_get_instances($course->id, false);
    $hasself = false;
    foreach ($instances as $i) { if ($i->enrol === 'self') { $hasself = true; $selfinst = $i; } }
    if (!$hasself && $self) {
        $id = $self->add_default_instance($course);
        $selfinst = $DB->get_record('enrol', ['id' => $id]);
    }
    if (isset($selfinst)) {
        $DB->update_record('enrol', (object)['id' => $selfinst->id, 'status' => ENROL_INSTANCE_ENABLED,
            'password' => $spec['enrolkey'] ?? '', 'customint6' => 1]);
        out("self-enrolment enabled" . (!empty($spec['enrolkey']) ? " with key" : ""));
    }
    list($student, $pw) = ensure_test_student();
    $studentrole = $DB->get_field('role', 'id', ['shortname' => 'student']);
    $manual = enrol_get_plugin('manual');
    foreach ($instances as $i) {
        if ($i->enrol === 'manual') { $manual->enrol_user($i, $student->id, $studentrole); out("enrolled teststudent"); }
    }
    out("TESTSTUDENT_PASSWORD=$pw");

    rebuild_course_cache($course->id, true);
    purge_all_caches();
    out("DONE converted=$converted");
    break;

default:
    out("commands: setup [--logo=path] | postimport --course=<fullname> --spec=<json> | teststudent");
}
