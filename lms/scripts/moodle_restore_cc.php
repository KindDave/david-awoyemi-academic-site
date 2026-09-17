<?php
/**
 * Restore an IMS Common Cartridge (or any Moodle backup) into a NEW course from the command line.
 *
 *   php moodle_restore_cc.php --file=/tmp/lms/course.imscc --categoryid=2 [--fullname=... --shortname=...]
 *
 * Moodle's own admin/cli/restore_backup.php cannot restore cartridges: it creates a temporary
 * controller and calls destroy() before the cartridge has been converted to Moodle 2 format,
 * which fails because no plan exists yet. This script follows the web restore sequence instead:
 * extract, convert (imscc11 -> moodle2), precheck, execute.
 *
 * Run inside the Moodle container as the web server user, for example:
 *   docker compose exec -u daemon moodle /opt/bitnami/php/bin/php /tmp/lms/moodle_restore_cc.php --file=... --categoryid=2
 */

define('CLI_SCRIPT', true);
foreach (['/bitnami/moodle/config.php', '/opt/bitnami/moodle/config.php', __DIR__ . '/../../config.php'] as $c) {
    if (file_exists($c)) { require($c); break; }
}
if (!isset($CFG)) { fwrite(STDERR, "Moodle config.php not found\n"); exit(1); }
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->dirroot . '/backup/util/includes/restore_includes.php');

list($options, $unrecognized) = cli_get_params(
    ['file' => '', 'categoryid' => 0, 'fullname' => '', 'shortname' => '', 'help' => false], ['h' => 'help']);
if ($options['help'] || !$options['file'] || !$options['categoryid']) {
    echo "Usage: --file=<path> --categoryid=<id> [--fullname=<name>] [--shortname=<code>]\n";
    exit($options['help'] ? 0 : 1);
}
if (!file_exists($options['file'])) { cli_error("file not found: {$options['file']}"); }
$category = $DB->get_record('course_categories', ['id' => $options['categoryid']], '*', MUST_EXIST);

// The Common Cartridge converter loads its templates from the relative path cc/sheets/,
// which resolves only when the working directory is <dirroot>/backup (as it is for web restores).
chdir($CFG->dirroot . '/backup');

$admin = get_admin();
$backupdir = restore_controller::get_tempdir_name(SITEID, $admin->id);
$path = make_backup_temp_directory($backupdir);

echo "== extracting to $path\n";
$fp = get_file_packer('application/vnd.moodle.backup');
if (!$fp->extract_to_pathname($options['file'], $path)) { cli_error("extraction failed"); }

try {
    list($fullname, $shortname) = restore_dbops::calculate_course_names(0,
        $options['fullname'] ?: get_string('restoringcourse', 'backup'),
        $options['shortname'] ?: get_string('restoringcourseshortname', 'backup'));
    $courseid = restore_dbops::create_new_course($fullname, $shortname, $category->id);
    echo "== created course id $courseid in category {$category->name}\n";

    $rc = new restore_controller($backupdir, $courseid, backup::INTERACTIVE_NO,
        backup::MODE_GENERAL, $admin->id, backup::TARGET_NEW_COURSE);

    if ($rc->get_status() == backup::STATUS_REQUIRE_CONV) {
        echo "== converting " . $rc->get_format() . " to moodle2\n";
        $rc->convert();
    }
    if (!$rc->execute_precheck()) {
        $results = $rc->get_precheck_results();
        echo "== precheck problems:\n" . print_r($results, true);
        if (!empty($results['errors'])) { throw new moodle_exception('generalexceptionmessage', 'error', '', 'precheck errors'); }
    }
    echo "== executing restore plan\n";
    $rc->execute_plan();
    $rc->destroy();
    fulldelete($path);

    $course = $DB->get_record('course', ['id' => $courseid]);
    echo "== restored: [{$course->id}] {$course->fullname} ({$course->shortname})\n";
    echo "COURSEID=$courseid\n";
    exit(0);
} catch (Throwable $e) {
    fulldelete($path);
    if (!empty($courseid)) { delete_course($courseid, false); fix_course_sortorder(); }
    fwrite(STDERR, "!! restore failed: " . $e->getMessage() . "\n" . $e->getTraceAsString() . "\n");
    exit(1);
}
